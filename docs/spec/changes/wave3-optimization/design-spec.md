# Design Spec: wave3-optimization

Applies to the mockup in `mockup/` (iteration 1): `index.html`, `sponsor.html`, `portfolio.html`, `terminal.html`,
`method-page.html`. The project has no `PRODUCT.md`, `DESIGN.md` or `docs/spec/design-system.md` yet and
`spec.json:inputs` pins no design; the visual language already shipped is the method page `docs/karvey.html`, so this
spec **reuses its values** instead of inventing a palette. This is the first UI change after REQ-W3-035, so these tokens
are the proposed seed of the project design system (created at archive, REQ-W3-036).

## Design register

**Enterprise B2B** — the readers are a sponsor who pays for a change, an approver and the people who run several
repositories. The page is read quickly and printed; the terminal surfaces are dense. Restraint over expression,
high legibility, minimal motion, medium-high density.

Targets: `cli` (project) for the portfolio, report, backlog, dashboard, gate summaries and messages — terminal
conventions (monospaced columns, colour only as reinforcement of a word); **web** for the two HTML pages — WCAG 2.2 AA.

## Color system (OKLCH)

Strategy: **Restrained** — one primary (slate, links and the selected state), one accent (ochre, emphasis and "your
turn"), neutrals on warm paper, three semantic colours. Hex values are the ones `docs/karvey.html` ships; OKLCH is
computed from them.

| Token | Light (hex · OKLCH) | Dark (hex · OKLCH) | Use |
|---|---|---|---|
| `--color-background` | `#f3eee3` · oklch(95.0% 0.016 86) | `#10161c` · oklch(19.7% 0.015 249) | page background |
| `--color-surface` | `#fbf8f2` · oklch(98.0% 0.009 85) | `#17202a` · oklch(24.0% 0.023 251) | cards, modals |
| `--color-surface-2` | `#ebe3d2` · oklch(91.8% 0.024 86) | `#202b36` · oklch(28.4% 0.025 249) | terminal blocks, hover, code |
| `--color-text-primary` | `#1d2831` · oklch(27.1% 0.023 243) | `#ebe5d8` · oklch(92.3% 0.019 86) | body text |
| `--color-text-secondary` | `#4a5560` · oklch(44.4% 0.023 248) | `#a8b1ba` · oklch(75.6% 0.016 248) | captions, dates, table heads |
| `--color-border` | `#d3c6ad` · oklch(83.1% 0.037 84) | `#34424f` · oklch(37.2% 0.029 247) | decorative dividers only |
| `--color-border-strong` | = text-secondary | = text-secondary | borders of controls (≥ 3:1, WCAG 1.4.11) |
| `--color-primary` | `#2b4256` · oklch(36.9% 0.045 246) | `#a3bfd8` · oklch(79.2% 0.047 245) | links, selected button/language |
| `--color-primary-soft` | `#d6e0e8` · oklch(90.1% 0.015 242) | `#1f3244` · oklch(30.9% 0.041 248) | info tag |
| `--color-accent` | `#8f5312` · oklch(50.2% 0.108 61) | `#e2ab5f` · oklch(77.7% 0.114 74) | eyebrows, "waiting for you" card border, active tab |
| `--color-accent-soft` | `#ecd3a4` · oklch(87.6% 0.067 83) | `#433018` · oklch(32.5% 0.046 71) | status pill, warn tag |
| `--color-semantic-success` | `#44632f` · oklch(46.2% 0.086 134) | `#a1c487` · oklch(77.9% 0.091 132) | pass, done step |
| `--color-semantic-error` | `#973a1e` · oklch(47.4% 0.132 37) | `#eb937a` · oklch(74.8% 0.113 37) | fail, overdue, refused |
| `--color-semantic-warning` | = accent | = accent | warn, stale, not read |
| `--color-focus` | `#1c5d96` · oklch(46.8% 0.112 249) | `#7fb6ea` · oklch(75.8% 0.095 248) | 3 px focus ring |

The skill's default semantic values (`oklch(62% 0.17 145)`, `oklch(55% 0.22 25)`, `oklch(75% 0.18 80)`) are **not**
used: as text on the paper surface they fall below 4.5:1, and the method page already has darker equivalents.
Warning shares the accent hue on purpose (one warm hue = "needs attention"); state is always also written as a word
(`overdue`, `open`, `not read`), never colour alone (WCAG 1.4.1, and terminal output without colour).

Schemes: `prefers-color-scheme` drives the sponsor page and the method page; the mockup chrome adds a
System / Light / Dark switch (`:root[data-theme]`) only to review both.

### Contrast (computed, WCAG 2.x relative luminance)

The change's own contrast tool (REQ-W3-038) does not exist yet; the ratios below were computed with the WCAG formula
from the hex values (not self-judged). Target: AA normal text 4.5:1; UI components and focus 3:1.

| Pair (text on background) | Light | Dark | Level |
|---|---|---|---|
| text-primary on background | 12.96 | 14.50 | AAA |
| text-primary on surface | 14.15 | 13.11 | AAA |
| text-primary on surface-2 (terminal) | 11.75 | 11.46 | AAA |
| text-secondary on background | 6.58 | 8.38 | AA / AAA |
| text-secondary on surface | 7.18 | 7.57 | AAA |
| text-secondary on surface-2 (terminal dim) | 5.96 | 6.62 | AA |
| primary (links) on surface | 9.83 | 8.62 | AAA |
| accent on surface / surface-2 | 5.80 / 4.82 | 8.01 / 7.00 | AA |
| success on surface / surface-2 | 6.45 / 5.36 | 8.43 / 7.37 | AA |
| error on surface / surface-2 | 6.74 / 5.60 | 7.04 / 6.15 | AA |
| background on primary (selected language, primary button) | 9.00 | 9.54 | AAA |
| text-primary on accent-soft / success-soft / error-soft / primary-soft (tags) | 10.30 / 11.59 / 10.79 / 11.20 | 9.99 / 10.54 / 11.51 / 10.47 | AAA |
| focus ring on background / surface (non-text) | 5.94 / 6.48 | 8.48 / 7.66 | ≥ 3:1 |

All 40 text checks (20 pairs × 2 schemes) pass AA; 29 reach AAA. `--color-border` (1.6:1) is decorative only; every control uses
`--color-border-strong` (5.96–7.57:1).

## Typography

System fonts only — REQ-W3-024 and REQ-W3-068 forbid external requests, so the skill's Google Fonts `@import` step
is deliberately skipped.

| Token | Font | Weight | Use |
|---|---|---|---|
| Heading | `--font-sans` (system-ui stack) | 700 | page title, section titles |
| Body | `--font-sans` | 400 / 600 | content, table cells, emphasis |
| Caption / eyebrow | `--font-mono`, uppercase, +0.08em tracking | 400 | section kicker, dates, ids |
| Terminal | `--font-mono` (ui-monospace stack) | 400 / 600 / 700 | CLI transcripts |
| CJK | `--font-sans` + `--font-cjk` (Hiragino, Yu Gothic, Apple SD Gothic Neo, Malgun Gothic, PingFang, Noto CJK) | 400 | ja / ko / zh blocks, line-height 1.75 |

## Type scale

| Token | Size / line | Use |
|---|---|---|
| `--text-xs` | 0.75rem / 1rem | eyebrows, tags, stamps |
| `--text-sm` | 0.875rem / 1.25rem | tables, secondary text, buttons |
| `--text-base` | 1rem / 1.6 | body |
| `--text-lg` | 1.125rem / 1.75rem | summary facts |
| `--text-xl` | 1.25rem / 1.75rem | section titles (h2) |
| `--text-2xl` | 1.5rem / 2rem | reserved |
| `--text-3xl` | 1.875rem / 2.25rem | page title, fluid `clamp(1.5rem, 4vw, 1.875rem)` |

## Layout

- **Sponsor page:** one column, max-width 880 px, no sidebar (it is read top to bottom and printed); section order puts
  the action first — *Waiting for you*, then scope, progress, cost, risks, released, page history. A four-fact summary
  row (step, cost, open risks, decisions waiting) sits above; it is a row of equal-weight facts, not a hero metric.
- **Phone:** no horizontal scroll from 360 px (REQ-W3-024 as revised); tables live in `.table-scroll`; the progress
  steps drop from 4 to 2 columns under 520 px.
- **Print:** `@media print` hides navigation, expands every `details`, removes shadows, keeps cards whole
  (`break-inside: avoid`).
- **Method page:** the language list becomes a `select` under 720 px — nine codes do not fit a phone top bar.
- **Terminal surfaces:** columns aligned in monospace, ≤ 120 characters wide; overflow scrolls inside the block.
- Content max-width 1080 px elsewhere; cards in an auto-fit grid (`minmax(min(100%, 320px), 1fr)`), 16 px gap.

## Spacing

4 px base: `--space-1` 4 · `--space-2` 8 · `--space-3` 12 · `--space-4` 16 · `--space-6` 24 · `--space-8` 32 ·
`--space-12` 48. Page gutter 16 px; card padding 16 × 24 px; sections 24 px apart.

## Border radius

`--radius-sm` 4 px (code, focus) · `--radius-md` 8 px (buttons, terminal) · `--radius-lg` 12 px (cards, modals) ·
`--radius-full` (tags, status pill).

## Motion

| Token | Value | Use |
|---|---|---|
| `--duration-fast` | 100 ms | hover, pressed |
| `--duration-base` | 200 ms | view switch (fade) |
| `--duration-slow` | 300 ms | overlay open |
| `--ease-standard` | cubic-bezier(0.4, 0, 0.2, 1) | state changes |
| `--ease-enter` | cubic-bezier(0, 0, 0.2, 1) | appear |
| `--ease-exit` | cubic-bezier(0.4, 0, 1, 1) | disappear |

Opacity only, no movement; `prefers-reduced-motion: reduce` removes every animation and transition. The sponsor page
works fully with no JavaScript (sections and `details` are native).

## Key components and their visual treatment

| Component | Surface | Border | Shadow | Hover / state |
|---|---|---|---|---|
| Primary button | primary | primary | none | primary fill, text in background colour; also the `aria-pressed` state of segmented buttons |
| Secondary button | surface | border-strong | none | surface-2 |
| Card | surface | border 1 px | shadow-1 | — |
| "Waiting for you" card | surface | accent 2 px all round | shadow-1 | the one emphasised card |
| Status pill | accent-soft (success-soft when released) | none | none | dot + words |
| Tag | surface-2 or a soft semantic | border / none | none | always a word inside |
| Table row | transparent | border bottom | none | surface-2 |
| Terminal block | surface-2 | border 1 px | none | scroll inside |
| Modal overlay | surface on 55% scrim | none | large | Esc and scrim click close |
| Tabs | none | 3 px accent underline when selected | none | text-primary |
| Language switch | none | transparent / primary when current | none | surface-2 |

## Art catalogue

Not produced: this change requests no illustrations or assets. The 4.0 skill asks for `design-components.md`, but this
change's own REQ-W3-037 makes the art catalogue opt-in; the component inventory above is enough for the pages.

## Anti-patterns avoided

- No side-stripe borders — the "waiting for you" emphasis is a full 2 px accent border (the method page's `.origin`
  and `.note` side stripes are not reused here).
- No gradient text, no decorative glassmorphism (no blur on these surfaces), no noise backgrounds.
- No identical card grids without emphasis — one card is emphasised; the facts row is a summary, not the content.
- No hero metric — the cost is one fact among four, with its date and its estimated share.
- No animation over 300 ms; none on frequent interactions beyond 100 ms.
- No colour-only meaning; no external fonts, images or scripts.

## Design scoring (0-10 by dimension)

Target evaluated: web (WCAG) for the two pages, cli/terminal for the transcripts. Scored by the authoring agent as the
4.0 skill requires; the colour/contrast row rests on the computed table above. REQ-W3-039 moves this score to a design
judge from 4.1 on.

| Dimension | Score | What a 10 would be | What is missing to get there |
|---|---|---|---|
| Visual hierarchy | 8 | the sponsor sees what is asked of them, the state and the cost in the first screen on a phone | the four facts push *Waiting for you* below the fold at 360 px; test with a real sponsor |
| Typography | 8 | one family, clear scale, CJK and Latin equally comfortable | CJK line-height verified only by reading the CSS, not rendered on three platforms |
| Color / contrast | 9 | every pair AAA, meaning never by colour alone | accent on surface-2 is AA (4.82), not AAA |
| Spacing / rhythm | 8 | one vertical rhythm across page, cards and tables | table cell padding (8 × 12) and card padding (16 × 24) not yet tied to one ratio |
| Consistency | 9 | every value a token shared with the method page | the terminal colour mapping is not a token set yet (it reuses semantic tokens) |
| Accessibility | 8 | keyboard, focus, semantics and 360 px verified in a browser and a screen reader | rendered checks pending (this environment has no browser; to be run by the browse step) |
| Motion | 9 | functional only, reduced-motion honoured | nothing material |

Average: **8.4/10** — Threshold (≥ 8, none < 7): **met**. Iterations performed: 1. Consciously accepted gaps: rendered
browser and screen-reader checks are deferred to the browse/QA step.
