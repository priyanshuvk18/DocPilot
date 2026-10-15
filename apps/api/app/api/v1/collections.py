"""
Collections API.
GET    /v1/collections
POST   /v1/collections
GET    /v1/collections/{id}
PATCH  /v1/collections/{id}
DELETE /v1/collections/{id}
"""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser
from app.db.session import get_db, set_rls_context
from app.models import Collection
from app.schemas import CollectionCreate, CollectionOut, CollectionUpdate

router = APIRouter()


@router.get("", response_model=list[CollectionOut], summary="List collections")
async def list_collections(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[CollectionOut]:
    await set_rls_context(db, str(user.user_id))
    ws_id = user.workspace_id or uuid.UUID("00000000-0000-0000-0000-000000000002")

    result = await db.execute(
        select(Collection).where(Collection.workspace_id == ws_id).order_by(Collection.created_at.desc())
    )
    cols = result.scalars().all()
    return [CollectionOut.model_validate(c) for c in cols]


@router.post("", response_model=CollectionOut, status_code=status.HTTP_201_CREATED, summary="Create a collection")
async def create_collection(
    payload: CollectionCreate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CollectionOut:
    user.require_role("owner", "member")
    await set_rls_context(db, str(user.user_id))
    ws_id = user.workspace_id or uuid.UUID("00000000-0000-0000-0000-000000000002")

    col = Collection(
        workspace_id=ws_id,
        name=payload.name,
        description=payload.description,
    )
    db.add(col)
    await db.commit()
    await db.refresh(col)
    return CollectionOut.model_validate(col)


@router.get("/{collection_id}", response_model=CollectionOut, summary="Get collection by ID")
async def get_collection(
    collection_id: uuid.UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CollectionOut:
    await set_rls_context(db, str(user.user_id))
    result = await db.execute(select(Collection).where(Collection.id == collection_id))
    col = result.scalar_one_or_none()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")
    return CollectionOut.model_validate(col)


@router.patch("/{collection_id}", response_model=CollectionOut, summary="Update collection")
async def update_collection(
    collection_id: uuid.UUID,
    payload: CollectionUpdate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CollectionOut:
    user.require_role("owner", "member")
    await set_rls_context(db, str(user.user_id))

    result = await db.execute(select(Collection).where(Collection.id == collection_id))
    col = result.scalar_one_or_none()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")

    if payload.name is not None:
        col.name = payload.name
    if payload.description is not None:
        col.description = payload.description

    await db.commit()
    await db.refresh(col)
    return CollectionOut.model_validate(col)


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete collection")
async def delete_collection(
    collection_id: uuid.UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    user.require_role("owner")
    await set_rls_context(db, str(user.user_id))

    result = await db.execute(select(Collection).where(Collection.id == collection_id))
    col = result.scalar_one_or_none()
    if col:
        await db.delete(col)
        await db.commit()
