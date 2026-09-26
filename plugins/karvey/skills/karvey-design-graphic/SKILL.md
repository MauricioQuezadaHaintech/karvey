---
name: karvey-design-graphic
description: Karvey phase 4 — design-spec.md, its delta over the design system, computed contrast, a design judge — after the mockup. Triggers include "karvey design-graphic", "diseño gráfico karvey", "karvey visual spec", "especificación visual karvey".
allowed-tools: Read, Write, Edit, Bash, Glob, AskUserQuestion
argument-hint: <change-id>
---

# Karvey Design Graphic

## Purpose

With the approved mockup as the structural wireframe, apply the **project design system** (`docs/spec/design-system.md`) to the change and record only what the change adds or modifies — its **design delta**. Contrast is computed by a tool, and the design score comes from a clean-context **design judge**, never from this phase (REQ-W3-035..039). Update the mockup HTML with the visual system.

## Execution steps

### Step 1 — Load context

Read:
- `docs/spec/changes/{change-id}/spec.json`
- `docs/spec/changes/{change-id}/mockup.html`
- `docs/spec/changes/{change-id}/prd.md`

Check the precondition: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-state.py" next "{change-id}" --json` (mockup approved; relay the blockers and stop if not), then `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-state.py" advance "{change-id}" design_graphic`.

**Read the project design system** `docs/spec/design-system.md` (tokens per scheme with `Changed by`, the component inventory, the pairs table with each pair's WCAG level). It is not redefined here: this phase maps it onto the change and declares only its delta. **No design system yet** → this is the first UI change: propose creating it — from this change's work (the delta becomes the seed at archive) or by importing a pinned `inputs.design_system` — and say which. Check whether a `PRODUCT.md` or `DESIGN.md` exists to understand the existing brand.

**Design produced by another agent or repo** (see `../karvey/rules/multi-agent.md` §3): if `spec.json:inputs.design` or `inputs.design_system` is set, read them **at the pinned commit** (`git -C {repo} show {commit}:{path}`). The design system is a hard input: tokens, type and components come from it and are not re-invented here — this phase maps them onto the change and declares its delta. If a designer agent delivers a new version, update the pin (`inputs.design = "{repo} {path} @{new-commit}"`) and record the re-pin in `revision_history`; `karvey-iterate` decides the ripple. When **this** phase is the one producing the design for other repos, finish by giving the consumers the reference to pin: `{repo} docs/spec/changes/{change-id}/design-spec.md @{commit}`.

### Step 2 — Identify the design register

Determine the product type:

**Enterprise product (B2B, internal tool):**
- Restrained palette, function over expressiveness
- High-legibility typography
- Minimal, non-distracting motion
- High information density

**Consumer product (B2C, user experience):**
- More expressive, brand-driven palette
- Typography with more personality
- Motion as part of the experience
- Moderate information density

Infer from `prd.md` and `spec.json.capability`.

**Target agnosticism (do NOT assume web).** The design guidance depends on the target declared in `docs/spec/project.json` (see `../karvey/rules/targets.md`):

- **web** → **WCAG** (contrast, focus, semantics, keyboard navigation)
- **iOS** → **Apple Human Interface Guidelines (HIG)** (Dynamic Type typography, safe areas, gestures, native controls)
- **Android** → **Material Design** (elevation, Material components, touch targets, theming)
- **desktop** → desktop conventions (density, menus, windows, OS shortcuts)
- **cli/terminal** → terminal conventions (column width, ANSI color, monospaced legibility, no assuming a GUI)

The color, typography, layout, and motion dimensions in the following steps are interpreted according to the target's guidance. If the project has multiple targets, define the visual system for each one while respecting its guidance. No phase assumes "web" by default.

### Step 3 — Define color system (OKLCH)

With a design system, use its colour tokens and add or modify only what the mockup needs (each modification recorded
with the system's current value as its base, Step 8). The strategies and starting values below apply only when there
is no design system yet. Choose a palette strategy:

**Restrained (recommended for B2B):**
- 1 accent color, the rest neutrals
- Accent: `oklch(55% 0.18 {hue})`
- Neutrals: gray scale `oklch(98% 0 0)` → `oklch(15% 0 0)`

**Committed:**
- 1 primary color + 1 supporting color
- Primary: `oklch(50% 0.20 {hue})`
- Supporting: `oklch(55% 0.15 {complementary hue})`

**Full palette:**
- Primary, secondary, accent, and semantic colors
- Appropriate for products with differentiated visual roles

Always define:
- `--color-primary`: primary action, CTA
- `--color-surface`: card/panel background
- `--color-background`: page background
- `--color-border`: subtle borders
- `--color-text-primary`: primary text
- `--color-text-secondary`: supporting text
- `--color-semantic-success`: `oklch(62% 0.17 145)`
- `--color-semantic-error`: `oklch(55% 0.22 25)`
- `--color-semantic-warning`: `oklch(75% 0.18 80)`

### Step 4 — Define typography

Choose 1-2 Google Fonts (or system fonts for B2B):

**For enterprise B2B:**
- Display/heading: Inter, DM Sans, or system-ui
- Body: same family, different weights

**For B2C:**
- Display: a font with character (Fraunces, Instrument Serif, Plus Jakarta Sans)
- Body: a high-legibility font (Inter, DM Sans)

Type scale:
```
--text-xs:   0.75rem / 1rem
--text-sm:   0.875rem / 1.25rem
--text-base: 1rem / 1.5rem
--text-lg:   1.125rem / 1.75rem
--text-xl:   1.25rem / 1.75rem
--text-2xl:  1.5rem / 2rem
--text-3xl:  1.875rem / 2.25rem
```

### Step 5 — Define layout and spacing

4px-based spacing system:
```
--space-1: 4px   --space-2: 8px   --space-3: 12px
--space-4: 16px  --space-6: 24px  --space-8: 32px
--space-12: 48px --space-16: 64px --space-24: 96px
```

Product grid:
- Sidebar: fixed 240px (or 64px collapsed)
- Content area: fluid with max-width based on density
- Content columns: 12 columns with a 24px gap

Border radius:
```
--radius-sm: 4px   --radius-md: 8px
--radius-lg: 12px  --radius-xl: 16px  --radius-full: 9999px
```

### Step 6 — Define motion

For B2B: functional motion, not decorative
```css
--duration-fast: 100ms
--duration-base: 200ms
--duration-slow: 300ms
--ease-standard: cubic-bezier(0.4, 0, 0.2, 1)
--ease-enter: cubic-bezier(0, 0, 0.2, 1)
--ease-exit: cubic-bezier(0.4, 0, 1, 1)
```

Rule: use `--duration-fast` for feedback, `--duration-base` for transitions, `--duration-slow` for overlays.

### Step 7 — Check for forbidden anti-patterns

Before writing the design-spec, confirm the system does NOT include:
- ❌ Decorative side-stripe borders (a color border on only one side of cards)
- ❌ Gradient text (text with a color gradient)
- ❌ Decorative glassmorphism (blur/transparency with no function)
- ❌ Card grids where every card is identical with no emphasis variation
- ❌ Hero metrics (a large number in the center of a screen as the only content)
- ❌ Backgrounds with noise patterns or excessive texture
- ❌ Animations longer than 500ms on frequent interactions

### Step 7B — Contrast is computed, not judged

Contrast is a number, not an opinion: after writing the delta (Step 8), run the contrast tool over the design
system with the delta applied and keep its JSON beside the spec — it is the design judge's deterministic sub-score:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-contrast-check.py" --delta "{change-id}" --json > "docs/spec/changes/{change-id}/contrast.json"
```
Every declared text/background pair is computed in both schemes against its level (AA normal when undeclared).
A pair below its level is fixed in the delta (or its level is changed with a reason) before the gate; an
unparseable token (exit 1) is fixed, never assumed. Cite the result in `design-spec.md` — do not recompute ratios by
hand and **do not score the design yourself**: the design judge does (Step 9C).

### Step 8 — Write design-spec.md

```markdown
# Design Spec: {change-id}

## Design register
{enterprise B2B | consumer B2C} — {rationale}

## Color system (OKLCH)
Strategy: {Restrained | Committed | Full palette}

| Token | OKLCH value | Use |
|-------|-------------|-----|
| --color-primary | oklch(...) | {use} |
| --color-surface | oklch(...) | {use} |
...

## Typography
| Token | Font | Weight | Use |
|-------|--------|------|-----|
| Heading | {font} | 600-700 | Page and section titles |
| Body | {font} | 400-500 | Content text |
| Caption | {font} | 400 | Metadata, labels |

## Type scale
(full table)

## Layout
- Sidebar: {fixed N px | collapsible | no sidebar}
- Grid: {description}
- Content max-width: {N px}

## Spacing
(4px base table)

## Border radius
(table)

## Motion
(variables table)

## Key components and their visual treatment
| Component | Surface | Border | Shadow | Hover state |
|------------|-----------|-------|--------|--------------|
| Primary button | | | | |
| Secondary button | | | | |
| Data card | | | | |
| Form input | | | | |
| Table row | | | | |
| Modal overlay | | | | |

## Anti-patterns avoided
(list of those that were checked)

## Contrast
Computed by `karvey-contrast-check.py --delta {change-id}` (`contrast.json`): {N} pairs × 2 schemes, {N} below level
({list or "none"}).
```

Write to `docs/spec/changes/{change-id}/design-spec.md`. Its first paragraph starts with an `Applies to` sentence
naming the mockup files it styles (the design judge reads exactly those).

Then write the **design delta** `docs/spec/changes/{change-id}/design-delta.md` — only what this change adds to or
modifies in the design system (a modified token carries the system's value now, so archive can detect a conflict):

```markdown
# Design delta: {change-id}

## Added
| Token | Scheme | Base value | New value |
|-------|--------|------------|-----------|
| `--color-info` | both | — | `#1c5d96` |

## Modified
| Token | Scheme | Base value | New value |
|-------|--------|------------|-----------|

## Components
| Component | Action |
|-----------|--------|
| {component} | added |

## Pairs
| Text token | Background token | Level |
|------------|------------------|-------|
```

A change that adds and modifies nothing writes a single line `empty`. Check that the delta tells the truth — every
difference between the design-spec and the design system must be declared:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-design.py" diff "{change-id}"
```
`undeclared modification: --color-…` → add the row to the delta (with its base value) or revert the value.

### Step 9 — Update mockup.html with the visual system

Edit `mockup.html` to:
1. Add the CSS custom properties (`:root { --color-primary: ...; ... }`)
2. Replace hardcoded colors with the variables
3. Use system fonts, or a font the design system declares that ships with the product (no external request)
4. Apply the motion system to existing transitions
5. Update the banner: `🎨 MOCKUP WITH GRAPHIC DESIGN — {change-id} — {date}`

### Step 9B — Visual components catalog (only on an asset request)

**Opt-in.** Produce `design-components.md` **only when the change asks for illustrations or assets** (the PRD or a
requirement says so). Otherwise skip this step and say so in the design-spec (`Art catalogue: not requested`).

The `design-spec.md` defines the system at the **token** level (palette, type, spacing, key components with their treatment). It does **not** enumerate, screen by screen and component by component, the concrete visual assets an illustrator or an AI art agent must produce. That is what `design-components.md` is for: an **art brief per component**.

**Derive it — do not invent it.** The catalog is derived from three sources and must cover them **exhaustively** — nothing invented, nothing omitted:
- **`mockup.html`** (approved) — every screen, modal/bottom sheet, and state that actually appears.
- **`design-spec.md`** — palette (hex + OKLCH, light AND dark), typography, tokens, illustration register.
- **`prd.md` / requirements** — the character/brand, the domain, and what each surface is for.

**Target agnosticism (do NOT assume web).** Adapt the components to the project's target(s) declared in `docs/spec/project.json` (see `../karvey/rules/targets.md`). The component inventory changes with the target: mobile → screens, bottom sheets, bottom-nav, push notifications; web → pages, side-nav, toasts, tables; CLI → screens/prompts, states, ANSI treatment; etc. If the project has multiple targets, add a section per target (e.g. "App" + "WebApp"). No component is assumed just because the web default has it.

Write to `docs/spec/changes/{change-id}/design-components.md` using this template:

```markdown
# Visual components catalog — {product / change-id}

**Purpose:** brief for a designer or AI agent that produces **illustrations/backgrounds per component**. Each item carries: what it is, content, states, and **required background art** (motif + style + palette). Navigable reference: `mockup.html`. Visual system: `design-spec.md`.

## Cross-cutting base (applies to all art)
- **Style:** {illustration style — trace, shapes, energy reference without copying any artist/brand}.
- **Palette (OKLCH → hex):** {light: hex list} · **Dark:** {dark: hex list}.
- **Character / brand:** {the hero of the art — how it can be illustrated across variants}.
- **Asset format:** vector/SVG preferred; PNG @1x/@2x/@3x for bitmap; backgrounds that **work in light and dark**; **safe zone** for text on top (do not saturate the center).

---

## A. Screens — {target / surface}

| # | Screen | Purpose | Required background/art |
|---|--------|---------|-------------------------|
| A1 | **{screen}** | {purpose} | {scene / motif / where the safe zone is} |
| … | | | |

## B. Modals / bottom sheets

| # | Modal | Content | Header illustration |
|---|-------|---------|---------------------|
| B1 | **{modal}** | {content} | {small header illustration} |
| … | | | |

## C. UI components

Per component: description, states, and **required background/fill art**. Cover at least: primary button, secondary button, input/textbox (+ variants: text, number, masked identifier/phone, select, date picker, textarea, search), chip, card, tile, avatar, badge, progress bar, tabs, bottom-nav (or the target's navigation), global states (loading/empty/error/success), and any **target-specific** component that appears in the mockup.

### C1. {component}
- **What it is:** {description}.
- **States:** {enumerate real states — normal, hover/pressed, disabled, loading, error, …}.
- **Art:** {required background/fill art, or "no illustration — define shine/shadow only"}.

### C2. {component}
- …

## D. Push notifications

| Type | Example copy | Illustration |
|------|--------------|--------------|
| **{type}** | "{copy in the product's voice}" | {icon/illustration} |
| … | | |

## E. {other surface — e.g. WebApp} (only if the change has it)

| Component | Description | Art |
|-----------|-------------|-----|
| **{component}** | {description} | {art} |

---

## F. Deliverable for the illustrator / AI agent
For each component in sections C, D and E, **1 base illustration** is expected (+ state variants where indicated), in the palette and style of "Cross-cutting base", with a **light and dark** version and a **safe zone for text**. Priority order:
1. {highest-visibility assets — e.g. hero scene + hero portrait}.
2. {navigation + tile/chip icon sets}.
3. {push notification icons}.
4. {badges / progress / accents}.
5. {modals and global states}.
```

Only include sections that the change actually has (drop E if there is no second surface; rename A's heading to the real target). Every screen/modal/state present in `mockup.html` must appear here.

### Step 9C — Design judge before the gate

The design score comes from a clean-context judge (lens `design`, `../karvey/rules/judges/design_graphic.md`), never
from this phase. Build its closed inputs — the delta, the "Applies to" mockups (≤ 200 KB each) and `contrast.json` —
run it as `../karvey/rules/judges.md` describes, and collect it:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-judges.py" inputs "{change-id}" design_graphic --json
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-judges.py" collect "{change-id}" design_graphic --results "{dir}" --transcript auto --json
```
A lane that skips design, or judges disabled, prints why and nothing runs. The gate summary shows the judge's
verdict and the contrast result side by side; the human decides.

### Step 10 — Output

```
✅ Design spec generated

Files created/updated:
  - docs/spec/changes/{change-id}/design-spec.md
  - docs/spec/changes/{change-id}/design-delta.md ({N} added · {N} modified · {N} components | empty)
  - docs/spec/changes/{change-id}/contrast.json
  - docs/spec/changes/{change-id}/design-components.md (only on an asset request)
  - docs/spec/changes/{change-id}/mockup.html (updated with visual system)

Design system:
  - Register: {B2B/B2C}
  - Color strategy: {name}
  - Typography: {font(s)}
  - Anti-patterns checked: ✅
  - Contrast: {N} pairs, {N} below level (karvey-contrast-check.py)
  - Design judge: {verdict} · {N} findings (lens design)
  - Components catalog: {not requested | N components briefed}

Approve the design spec to continue to /karvey-architecture {change-id}.
```

Record the artifact: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-state.py" generated "{change-id}" design_graphic`. This skill never approves its own output: ask the human, and only on their OK run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-state.py" approve "{change-id}" design_graphic --by "{name}" --role human --ref D-NN`.


## Advance to the next phase

Close the phase per `../karvey/rules/gates.md` (phase `design_graphic`, gate *what*): `generated`, then `karvey-state.py gate {change-id} design_graphic` says whether this phase asks the one gate question now (granular, or the last phase of the merged gate) or records `generated` and continues. The answer is recorded with `approve`/`approve-gate` or `outcome … changes_requested`; *Approve and advance* runs the skill `next` names with no second question. In a new session, `karvey-state.py next {change-id}` says where the change is.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `../karvey/TRADEMARK.md`.*
