---
name: karvey-design-graphic
description: Define the graphic design specification for an approved mockup. Uses impeccable-inspired design laws to establish color system, typography, layout, and motion. Updates the mockup HTML with the visual system. Triggers include "karvey design-graphic", "diseño gráfico", "graphic design", "especificación visual", "visual specification", "sistema de diseño", "design system".
allowed-tools: Read, Write, Edit, Bash, Glob, AskUserQuestion
argument-hint: <change-id>
---

# Karvey Design Graphic

## Purpose

With the approved mockup as the structural wireframe, define the complete visual design specification: color, typography, layout, motion, and micro-interactions. Update the mockup HTML with the defined visual system.

## Execution steps

### Step 1 — Load context

Read:
- `docs/spec/changes/{change-id}/spec.json`
- `docs/spec/changes/{change-id}/mockup.html`
- `docs/spec/changes/{change-id}/proposal.md`

Verify `approvals.mockup.approved = true`. If not, stop.

Check whether a `PRODUCT.md` or `DESIGN.md` exists in the project to understand the existing brand.

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

Infer from `proposal.md` and `spec.json.capability`.

**Target agnosticism (do NOT assume web).** The design guidance depends on the target declared in `docs/spec/project.json` (see `karvey/rules/targets.md`):

- **web** → **WCAG** (contrast, focus, semantics, keyboard navigation)
- **iOS** → **Apple Human Interface Guidelines (HIG)** (Dynamic Type typography, safe areas, gestures, native controls)
- **Android** → **Material Design** (elevation, Material components, touch targets, theming)
- **desktop** → desktop conventions (density, menus, windows, OS shortcuts)
- **cli/terminal** → terminal conventions (column width, ANSI color, monospaced legibility, no assuming a GUI)

The color, typography, layout, and motion dimensions in the following steps are interpreted according to the target's guidance. If the project has multiple targets, define the visual system for each one while respecting its guidance. No phase assumes "web" by default.

### Step 3 — Define color system (OKLCH)

Choose a palette strategy:

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

### Step 7B — Design scoring 0-10 by dimension

Before finalizing the visual system, evaluate the design-spec/mockup with a **0-10 score for each relevant design dimension**. The dimensions are interpreted according to the target's guidance (Step 2): WCAG for web, HIG for iOS, Material for Android, desktop/terminal conventions as applicable. Not all dimensions apply to all targets (e.g., "color/contrast" in a CLI is assessed over ANSI color; "motion" may not apply in a terminal).

Suggested dimensions (adjust to the target):

- **Visual hierarchy** — the eye finds what matters first; clear emphasis between primary/secondary/tertiary
- **Typography** — coherent scale, weights with purpose, legibility; on iOS respects Dynamic Type, in CLI monospaced legibility
- **Color / contrast** — intentional palette; sufficient contrast (WCAG AA/AAA on web; the target's equivalent)
- **Spacing / rhythm** — consistent base system, grouping by proximity, visual breathing room
- **Consistency** — reused tokens, uniform components, no ad-hoc values
- **Accessibility** — visible focus, keyboard navigation, touch targets, semantics; per the platform's checklist
- **Motion** — functional and non-distracting, reasonable durations, respects `prefers-reduced-motion` (or the target's equivalent)

For **each dimension**:

1. Assign a **0-10 score**.
2. **Explicitly explain what a 10 would be** in that dimension for this design and target (the concrete bar for excellence, not a generic one).
3. State **what is missing to reach a 10** from the current score (actionable gap).

Scoring table:

| Dimension | Score (0-10) | What a 10 would be | What is missing to get there |
|-----------|-------------|-----------------|-----------------------|
| Visual hierarchy | | | |
| Typography | | | |
| Color / contrast | | | |
| Spacing / rhythm | | | |
| Consistency | | | |
| Accessibility | | | |
| Motion | | | |

**Acceptable threshold:** average ≥ 8 and no dimension < 7. If not met, **iterate the design-spec/mockup** (return to steps 3-6 depending on the weak dimension) and re-evaluate. Repeat until the threshold is met or until the remaining gap is a conscious scope decision documented in the design-spec.

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

## Design scoring (0-10 by dimension)
Target evaluated: {web (WCAG) | iOS (HIG) | Android (Material) | desktop | cli/terminal}

| Dimension | Score (0-10) | What a 10 would be | What is missing to get there |
|-----------|-------------|-----------------|-----------------------|
| Visual hierarchy | | | |
| Typography | | | |
| Color / contrast | | | |
| Spacing / rhythm | | | |
| Consistency | | | |
| Accessibility | | | |
| Motion | | | |

Average: {N}/10 — Threshold (≥8, none <7): {met | not met}
Iterations performed: {N} — Consciously accepted gaps: {description or "none"}
```

Write to `docs/spec/changes/{change-id}/design-spec.md`.

### Step 9 — Update mockup.html with the visual system

Edit `mockup.html` to:
1. Add the CSS custom properties (`:root { --color-primary: ...; ... }`)
2. Replace hardcoded colors with the variables
3. Add the font via Google Fonts `@import`
4. Apply the motion system to existing transitions
5. Update the banner: `🎨 MOCKUP WITH GRAPHIC DESIGN — {change-id} — {date}`

### Step 9B — Update knowledge graph

Sync the knowledge per `karvey/rules/knowledge-sync.md` (Obsidian if available; at minimum `/graphify docs/spec/ --update`) to reflect `design-spec.md` and the updated `mockup.html`.
If `docs/spec/graphify-out/` does not exist, invoke `/graphify docs/spec/` without `--update`.

### Step 10 — Output

```
✅ Design spec generated

Files created/updated:
  - docs/spec/changes/{change-id}/design-spec.md
  - docs/spec/changes/{change-id}/mockup.html (updated with visual system)

Design system:
  - Register: {B2B/B2C}
  - Color strategy: {name}
  - Typography: {font(s)}
  - Anti-patterns checked: ✅
  - Design scoring: {N}/10 average (threshold ≥8, none <7) — {met | not met}

Update spec.json: approvals.design_graphic = true

Next step:
/karvey-architecture {change-id}
```

Update `spec.json`: `approvals.design_graphic.approved: true`, `phase: "design-graphic-approved"`.


## Advance to the next phase

When you finish this phase and have the corresponding approval, **actively ask the user**: "Shall we advance to the Architecture phase now?"
- If they confirm → run `/karvey-architecture {change-id}`.
- If they prefer to review or adjust first → wait. Advancing is always with the user's OK (the method's gate).
- If you resume in another session, `/karvey {change-id}` shows which phase you are in and which one is next.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
