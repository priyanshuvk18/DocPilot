# DocPilot — UI/UX Motion & Interaction Spec

**Design intent:** A calm, precise, "intelligent instrument." Motion communicates *state* (loading, grounded, confirmed) and never decorates at the cost of speed or clarity. Premium feel on the marketing page; quiet and fast inside the app.

**Stack:** Next.js · Tailwind · Framer Motion (`motion`) · React Three Fiber (landing hero only) · CSS `@property`/transforms.

---

## 0. Foundations

### Motion tokens (`styles/tokens.css`)
```css
:root {
  /* durations */
  --dur-instant: 90ms;
  --dur-fast: 160ms;
  --dur-base: 260ms;
  --dur-slow: 480ms;
  --dur-hero: 900ms;

  /* easings */
  --ease-out: cubic-bezier(0.22, 1, 0.36, 1);        /* default enter */
  --ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);     /* state change */
  --ease-spring-soft: cubic-bezier(0.34, 1.56, 0.64, 1); /* playful pop */

  /* depth */
  --shadow-rest: 0 1px 2px rgb(0 0 0 / .06), 0 4px 12px rgb(0 0 0 / .05);
  --shadow-lift: 0 8px 24px rgb(0 0 0 / .12), 0 2px 6px rgb(0 0 0 / .08);
  --accent: #6D5EF6;       /* indigo-violet */
  --accent-glow: rgb(109 94 246 / .35);
}
```

### Spring presets (Framer Motion)
```ts
export const spring = {
  soft:   { type: "spring", stiffness: 170, damping: 22 },
  snappy: { type: "spring", stiffness: 380, damping: 30 },
  float:  { type: "spring", stiffness: 60,  damping: 14, mass: 1.2 },
};
```

### Rules
1. **Animate only `transform` and `opacity`** (GPU-friendly). Avoid animating `width/height/top/left/box-shadow` directly; fade a pseudo-element for shadows.
2. **Respect `prefers-reduced-motion`:** replace movement with opacity-only fades ≤ 120 ms; disable parallax, 3D tilt, and looping animations. Provide an in-app "Reduce motion" toggle.
3. **Budget:** interactions ≤ 300 ms; entrances ≤ 600 ms (hero up to 900 ms); no animation may block input.
4. **Never animate streaming text layout** (causes reflow); only fade in the cursor/caret.
5. **Accessibility:** focus states are as prominent as hover; no information conveyed by motion alone; keep contrast ≥ 4.5:1.
6. **Hover only on pointer devices:** wrap in `@media (hover: hover) and (pointer: fine)`; provide `:active`/focus equivalents for touch.

```ts
// hooks/useReducedMotion.ts — wrap Framer's hook + user setting
import { useReducedMotion as useRM } from "framer-motion";
export const useMotionOK = () => !useRM() && !userSettings.reduceMotion;
```

---

## 1. Hover Effects

| Element | Effect | Spec |
|---|---|---|
| **Primary button** | Lift + glow | `translateY(-1px)`, accent glow fades in (pseudo-element opacity 0→1), 160 ms `--ease-out`. `:active` → `scale(.98)`, 90 ms. |
| **Secondary/ghost button** | Fill sweep | Background fills left→right via `scaleX` on a pseudo-element, 220 ms. |
| **Document card** | Elevate + reveal actions | Card `translateY(-3px)`, shadow rest→lift (opacity crossfade of shadow layer), action icons (Open, Re-index, Delete) slide up 6 px and fade in, 180 ms staggered 30 ms. |
| **Citation chip `[1]`** | Preview popover | On hover/focus (delay 120 ms): popover with source filename, page, 2-line quote; arrow tracks chip; `scale(.96→1)` + fade, 140 ms. The source passage in the side panel gets a highlight pulse. |
| **Sidebar nav item** | Indicator slide | Shared-layout `layoutId` pill glides between items (spring.snappy); icon nudges 2 px right. |
| **Chat message** | Toolbar reveal | Copy / 👍 / 👎 / Regenerate fade in at message corner on hover/focus-within, 120 ms. |
| **Table rows (monitoring)** | Row highlight | Background tint 8% accent; left 2 px accent bar scales in vertically. |
| **Links** | Underline draw | `background-size: 0→100%` underline, 200 ms. |
| **Eval score badge** | Tooltip + count | Hover shows delta vs. baseline with ▲/▼ color-coded and an icon (not color alone). |

```tsx
// Example: document card
<motion.article
  whileHover={{ y: -3 }}
  transition={spring.snappy}
  className="group relative rounded-2xl border bg-card p-4"
>
  <span className="pointer-events-none absolute inset-0 rounded-2xl opacity-0
        shadow-[var(--shadow-lift)] transition-opacity duration-200 group-hover:opacity-100" />
  <div className="opacity-0 translate-y-1.5 transition group-hover:opacity-100
        group-hover:translate-y-0 group-focus-within:opacity-100">
    <CardActions />
  </div>
</motion.article>
```

---

## 2. Smooth Loader

**Principle:** Loading should feel like *progress*, not waiting. Use skeletons for layout-known content, determinate progress for ingestion, and a purposeful "thinking" state for AI.

### 2.1 App boot / route transitions
- **Top progress bar** (2 px, accent gradient) with trickle easing; completes with a quick fade. Appears only if navigation > 200 ms (avoids flicker).
- **Skeleton screens** for lists/cards: shimmer gradient moving diagonally, 1.4 s loop, `background-position` on a masked layer. Skeleton shapes match final layout to prevent CLS.
- Minimum display time 300 ms once shown, to prevent flash.

### 2.2 Document ingestion status (determinate)
Status pill morphs through states with a shared-layout transition:

`Queued` (pulsing dot) → `Parsing` (ring progress) → `Embedding` (ring + "Chunk 42/130") → `Ready` (ring completes → checkmark draws with SVG `pathLength` 0→1, 320 ms, subtle scale pop) → `Failed` (shake 2 px ×2 + retry button).

```tsx
<motion.path d="M5 13l4 4L19 7" stroke="currentColor" fill="none"
  initial={{ pathLength: 0 }} animate={{ pathLength: 1 }}
  transition={{ duration: .32, ease: [0.22, 1, 0.36, 1] }} />
```

### 2.3 AI "thinking" loader (chat)
- **Phase-labelled status** streamed from API: *Searching documents… → Reading 6 passages… → Writing answer…* Label crossfades (160 ms, 4 px vertical slide).
- Visual: **three-dot orb** with staggered scale/opacity (1.2 s loop, `ease-in-out`), or a soft gradient "breathing" ring around the assistant avatar.
- Retrieved sources appear as **small chips popping in sequentially** (stagger 60 ms) *before* the answer starts, which makes waiting feel productive and builds trust.
- First token replaces the loader without layout jump (reserve line height).
- **Streaming caret:** blinking 1 px accent caret (opacity only).

### 2.4 Rules
- No spinners longer than 1 s without text context.
- If > 8 s: show "Still working…" with cancel button.
- Cancel instantly aborts the stream (and upstream generation).

```css
.skeleton { position: relative; overflow: hidden; background: var(--muted); }
.skeleton::after {
  content: ""; position: absolute; inset: 0;
  background: linear-gradient(110deg, transparent 30%, rgb(255 255 255 / .35) 50%, transparent 70%);
  transform: translateX(-100%); animation: shimmer 1.4s infinite;
}
@keyframes shimmer { to { transform: translateX(100%); } }
@media (prefers-reduced-motion: reduce) { .skeleton::after { animation: none; } }
```

---

## 3. 3D Motion

**Where to use (sparingly):** landing hero, empty states, and card tilt. Never in data-dense work screens.

### 3.1 Hero scene (marketing page)
- **Concept:** a floating "document stack" — translucent pages orbiting a glowing node (the AI core). As the user scrolls, pages stream into the node, and a citation line connects back to a page (visualizing RAG).
- **Tech:** React Three Fiber + drei, ~20 low-poly planes, instanced; one directional + ambient light; no heavy textures (< 300 KB total). Lazy-loaded with `next/dynamic` (`ssr:false`), static gradient poster shown first (LCP safe).
- **Interaction:** gentle pointer-follow rotation (±6°), eased with lerp (0.06); idle float (sine, 6 s period).
- **Performance:** cap DPR at 1.5, pause rendering when off-screen (`IntersectionObserver`), disable on low-end devices (`navigator.hardwareConcurrency < 4` or `saveData`) → fallback to CSS-3D or static image.

### 3.2 3D card tilt (feature cards, pricing)
- Pointer-driven `rotateX/rotateY` up to ±8°, `perspective: 900px`, `transform-style: preserve-3d`; inner layers offset on Z (`translateZ(20px)`) for depth; specular highlight follows cursor via radial gradient.
- Return to rest with `spring.soft` on pointer leave.

```tsx
function Tilt3D({ children }) {
  const x = useMotionValue(0), y = useMotionValue(0);
  const rx = useSpring(useTransform(y, [-.5, .5], [8, -8]), spring.soft);
  const ry = useSpring(useTransform(x, [-.5, .5], [-8, 8]), spring.soft);
  return (
    <motion.div
      style={{ rotateX: rx, rotateY: ry, transformPerspective: 900, transformStyle: "preserve-3d" }}
      onPointerMove={(e) => {
        const r = e.currentTarget.getBoundingClientRect();
        x.set((e.clientX - r.left) / r.width - .5);
        y.set((e.clientY - r.top) / r.height - .5);
      }}
      onPointerLeave={() => { x.set(0); y.set(0); }}
    >{children}</motion.div>
  );
}
```

### 3.3 In-app 3D touches
- **Citation → source panel:** the source passage "flips in" (`rotateY` 12°→0, 260 ms) when opened.
- **Empty "no documents" state:** a lightweight CSS-3D stack of pages that fans out on hover.
- **Action card confirm:** card tilts forward and "stamps" down (`translateZ`, scale 1.02→1) with a soft shadow collapse.

**Reduced motion:** all 3D → static; hero shows poster image.

---

## 4. Entrance Reveal

### 4.1 Page-load choreography (landing)
Sequence (total ≤ 900 ms):
1. Nav fades in (0 ms).
2. Headline: **word-by-word mask reveal** — each word slides up from 100% inside an `overflow:hidden` wrapper, stagger 40 ms, 600 ms, `--ease-out`.
3. Sub-copy fade + 12 px rise (+200 ms).
4. CTA buttons scale from .96 with fade (+320 ms).
5. Hero 3D/visual fades up with slight blur-to-sharp (`filter: blur(8px)→0` — use sparingly, hero only) (+400 ms).

### 4.2 Scroll-triggered reveal
- `whileInView` with `viewport={{ once: true, margin: "-80px" }}`.
- Default: `opacity 0→1`, `y 24→0`, 480 ms, `--ease-out`.
- Grids: container `staggerChildren: 0.07`.
- Section headings use the same word-mask reveal as the hero for consistency.

```tsx
const container = { hidden: {}, show: { transition: { staggerChildren: 0.07 } } };
const item = { hidden: { opacity: 0, y: 24 }, show: { opacity: 1, y: 0, transition: { duration: .48, ease: [.22,1,.36,1] } } };

<motion.ul variants={container} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-80px" }}>
  {features.map(f => <motion.li key={f.id} variants={item}>…</motion.li>)}
</motion.ul>
```

### 4.3 In-app entrances (subtler, faster)
- **Route content:** 8 px rise + fade, 200 ms (no stagger beyond first view).
- **Chat messages:** user message slides up 8 px; assistant message fades in with avatar scale (.9→1). Citations chips follow after text completes, staggered 50 ms.
- **Modals/sheets:** backdrop fade 160 ms; panel `scale(.97→1)` + fade (desktop) or slide-up sheet (mobile) with `spring.snappy`.
- **Toasts:** slide from bottom-right 16 px + fade; auto-dismiss with a thin progress line.
- **Lists:** new items insert with layout animation (`layout` prop + `AnimatePresence`), others glide to make room.

**Rule:** reveals run once per session per element; revisiting a page shouldn't replay long sequences.

---

## 5. Micro-interactions

| Interaction | Behavior |
|---|---|
| **Send button** | On click: icon shifts right 4 px & fades, new "stop" icon morphs in (cross-rotate 90°, 140 ms). Disabled state when empty, with soft 40% opacity. |
| **Composer focus** | Border animates to accent, glow ring expands (opacity), textarea auto-grows smoothly (animate container height with layout animation), `Cmd/Ctrl+Enter` hint fades in. |
| **File drop zone** | On drag-over: dashed border animates (marching ants), icon bounces up 4 px, background tint; on drop: items fly into list with stagger, each with its own progress ring. |
| **Upload success** | Checkmark path draw + tiny confetti-free "pulse ring" expanding once from the icon. |
| **👍 / 👎 feedback** | Icon scales 1→1.25→1 with spring pop; fills with color + checkmark label; 👎 opens inline reason chips sliding down (height via layout). |
| **Copy button** | Icon morphs copy → check (crossfade + scale), tooltip "Copied" 1.2 s, then reverts. |
| **Citation click** | Chip presses (scale .96), side panel slides in, matched passage gets a 1.2 s yellow-to-transparent highlight sweep, scroll eases to it. |
| **Agent action card** | Preview card with editable fields; **Confirm** button uses *press-and-hold-free* single click with a 400 ms progress fill → success tick; **Reject** shakes lightly (2 px) then collapses. Failure shows inline error with retry; never a silent fail. |
| **Toggle switches** | Thumb stretches slightly during travel (squash & stretch 1.15× width), color transitions 200 ms. |
| **Collections drag-and-drop** | Dragged card lifts (scale 1.03, shadow-lift, 2° tilt); drop target outlines and gently scales; on drop, card settles with `spring.snappy`. |
| **Eval run** | Progress bar fills per case; metric numbers **count up** (tabular-nums, 600 ms ease-out) to final values; deltas flash ▲/▼ once. |
| **Dashboard charts** | Lines draw in (`pathLength`), bars grow from baseline; hover crosshair snaps to nearest point with value tooltip. |
| **Input validation** | Invalid field gets 2 px horizontal shake (180 ms) + inline message sliding down; success gets subtle check. |
| **Theme switch** | Circular reveal from toggle (View Transitions API with fallback to crossfade). |
| **Keyboard** | `⌘K` command palette scales/fades in, results highlight with sliding pill; visible focus rings always. |
| **Haptics (mobile)** | Light haptic on confirm/reject via `navigator.vibrate(10)` where supported. |

---

## 6. Parallax Effect

**Where:** marketing/landing page only. Not used inside the app shell.

### 6.1 Layered scroll parallax (hero + features)
| Layer | Speed (relative to scroll) | Content |
|---|---|---|
| Background gradient mesh | 0.2× | Slow-moving color blobs |
| Floating doc cards (far) | 0.4× | Blurred, small, low opacity |
| Floating doc cards (near) | 0.8× | Sharper, larger, slight rotation |
| Foreground text/UI mockup | 1× | Headline, product screenshot |
| Foreground sparks/citation lines | 1.2× | Accent lines that overshoot |

```tsx
function ParallaxLayer({ speed = 0.4, children }) {
  const ref = useRef(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "end start"] });
  const y = useTransform(scrollYProgress, [0, 1], [`${-60 * speed}px`, `${60 * speed}px`]);
  const smooth = useSpring(y, { stiffness: 80, damping: 24, mass: .4 });
  return <motion.div ref={ref} style={{ y: smooth }}>{children}</motion.div>;
}
```

### 6.2 Pointer parallax (hero)
- Layers shift opposite to cursor by `speed × 12 px` max, eased (lerp) for a floating feel; combines with 3D hero tilt.

### 6.3 Scroll-linked storytelling ("How it works")
Sticky section with 3 steps (Upload → Ask → Act). As the user scrolls, the left text changes step (crossfade) while the right mockup transitions: documents fly in → chat answer streams with citation lines → action card stamps. Progress dots on the side fill with scroll progress.

### 6.4 Guardrails
- Max parallax offset ±80 px; no parallax on text blocks smaller than 18 px.
- Disabled on touch devices with small viewports (< 768 px) → use simple reveals; disabled on `prefers-reduced-motion`.
- Use `will-change: transform` only during active scroll; remove afterwards.
- Verify CLS = 0 and scroll stays at 60 fps in Chrome performance profiler; Lighthouse performance ≥ 90 on landing.

---

## 7. Key Screen Notes

| Screen | Layout | Motion highlights |
|---|---|---|
| **Landing** | Hero + 3D, "how it works" sticky story, feature tilt cards, trust/security section | Word reveal, parallax, 3D hero, scroll reveals |
| **Chat** | 3-pane: threads (left), conversation (center), sources/actions (right, collapsible) | Phase loader, source chips, streaming, citation highlight, action stamp |
| **Documents** | Grid/list toggle, drag-drop zone, status pills | Card hover, upload rings, status morph |
| **Evals** | Run table, metric cards, trend chart | Count-up numbers, chart draw-in |
| **Monitoring** | KPI cards (latency, cost, feedback), trace list | Row hover, tooltip crosshair |

## 8. Visual Language

- **Type:** Inter (UI), JetBrains Mono (citations/trace IDs); tabular numbers for metrics.
- **Color:** neutral base, single accent (indigo-violet), semantic colors for success/warn/error, always paired with icons.
- **Shape:** 16 px card radius, 10 px controls, soft layered shadows.
- **Dark mode:** first-class; shadows replaced with subtle borders + glow.
- **Density:** comfortable by default; compact mode for power users (evals/monitoring).

## 9. QA Checklist for Motion

- [ ] All animations disabled/simplified under `prefers-reduced-motion`
- [ ] Only `transform`/`opacity` animated (verify in Performance panel)
- [ ] No layout shift (CLS < 0.05) from loaders, reveals, or streamed text
- [ ] Hover effects have focus/touch equivalents
- [ ] Interactions respond < 100 ms; no animation delays user input
- [ ] 3D/parallax lazy-loaded; landing LCP < 2.5 s; INP < 200 ms
- [ ] Screen-reader announcements for status changes (`aria-live="polite"` on loader/status/toasts)
- [ ] Tested on low-end Android, Safari iOS, Firefox, Chrome
