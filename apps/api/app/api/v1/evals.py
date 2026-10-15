"""
Evaluations & golden benchmark API.
Architecture.md §4.4 & §7.3.
"""
from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import CurrentUser
from app.db.session import get_db, set_rls_context
from app.models import EvalCase, EvalRun, EvalSet
from app.schemas import (
    EvalCaseCreate,
    EvalCaseOut,
    EvalResultOut,
    EvalRunOut,
    EvalSetCreate,
    EvalSetOut,
)
from app.services.evals.runner import run_evaluation_suite

router = APIRouter()


@router.get("/eval-sets", response_model=list[EvalSetOut], summary="List evaluation sets")
async def list_eval_sets(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[EvalSetOut]:
    await set_rls_context(db, str(user.user_id))
    ws_id = user.workspace_id or uuid.UUID("00000000-0000-0000-0000-000000000002")

    result = await db.execute(
        select(EvalSet)
        .options(selectinload(EvalSet.cases), selectinload(EvalSet.runs))
        .where(EvalSet.workspace_id == ws_id)
        .order_by(EvalSet.created_at.desc())
    )
    sets = result.scalars().all()
    return [EvalSetOut.model_validate(s) for s in sets]


@router.post("/eval-sets", response_model=EvalSetOut, status_code=status.HTTP_201_CREATED, summary="Create an evaluation set")
async def create_eval_set(
    payload: EvalSetCreate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EvalSetOut:
    user.require_role("owner", "member")
    await set_rls_context(db, str(user.user_id))
    ws_id = user.workspace_id or uuid.UUID("00000000-0000-0000-0000-000000000002")

    eval_set = EvalSet(workspace_id=ws_id, name=payload.name)
    db.add(eval_set)
    await db.flush()

    for c in payload.cases:
        case = EvalCase(
            eval_set_id=eval_set.id,
            question=c.question,
            reference_answer=c.reference_answer,
        )
        db.add(case)

    await db.commit()
    await db.refresh(eval_set)

    # Reload with relations
    res = await db.execute(
        select(EvalSet)
        .options(selectinload(EvalSet.cases), selectinload(EvalSet.runs))
        .where(EvalSet.id == eval_set.id)
    )
    return EvalSetOut.model_validate(res.scalar_one())


@router.get("/eval-sets/{eval_set_id}", response_model=EvalSetOut, summary="Get evaluation set")
async def get_eval_set(
    eval_set_id: uuid.UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EvalSetOut:
    await set_rls_context(db, str(user.user_id))
    result = await db.execute(
        select(EvalSet)
        .options(selectinload(EvalSet.cases), selectinload(EvalSet.runs))
        .where(EvalSet.id == eval_set_id)
    )
    es = result.scalar_one_or_none()
    if not es:
        raise HTTPException(status_code=404, detail="Eval set not found")
    return EvalSetOut.model_validate(es)


@router.post("/eval-sets/{eval_set_id}/cases", response_model=EvalCaseOut, status_code=status.HTTP_201_CREATED, summary="Add test case to eval set")
async def add_eval_case(
    eval_set_id: uuid.UUID,
    payload: EvalCaseCreate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EvalCaseOut:
    user.require_role("owner", "member")
    await set_rls_context(db, str(user.user_id))

    case = EvalCase(
        eval_set_id=eval_set_id,
        question=payload.question,
        reference_answer=payload.reference_answer,
    )
    db.add(case)
    await db.commit()
    await db.refresh(case)
    return EvalCaseOut.model_validate(case)


@router.post("/eval-sets/{eval_set_id}/runs", response_model=EvalRunOut, summary="Trigger evaluation run")
async def trigger_eval_run(
    eval_set_id: uuid.UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    config: dict[str, Any] | None = None,
) -> EvalRunOut:
    user.require_role("owner", "member")
    await set_rls_context(db, str(user.user_id))
    ws_id = user.workspace_id or uuid.UUID("00000000-0000-0000-0000-000000000002")

    run = await run_evaluation_suite(
        session=db,
        eval_set_id=eval_set_id,
        workspace_id=ws_id,
        config=config,
    )
    # Reload with results
    res = await db.execute(
        select(EvalRun)
        .options(selectinload(EvalRun.results))
        .where(EvalRun.id == run.id)
    )
    return EvalRunOut.model_validate(res.scalar_one())


@router.get("/eval-runs/{run_id}", response_model=EvalRunOut, summary="Get evaluation run results")
async def get_eval_run(
    run_id: uuid.UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EvalRunOut:
    await set_rls_context(db, str(user.user_id))
    result = await db.execute(
        select(EvalRun)
        .options(selectinload(EvalRun.results))
        .where(EvalRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Eval run not found")
    return EvalRunOut.model_validate(run)
