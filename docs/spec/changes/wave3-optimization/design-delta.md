# Design delta: wave3-optimization

The project has no `docs/spec/design-system.md` yet, so every token of this change's design-spec is **added** (light and
dark rows from the Color system table). Written after the fact for the E1.F11.T4 dogfooding run of the design judge
(F-68). Iteration 3 (2026-09-27, the design judge's findings F-86..F-101) declares every value the pages use:
the soft semantic fills, the scrim, the print colours, the shadows, the font stacks, the type, spacing and radius
scales, the 44 px touch size and the print page width, the components the sponsor page introduces, and every text or
focus pair the pages draw (27 pairs; `contrast.json` recomputed with `karvey-contrast-check.py --delta`).

## Added
| Token | Scheme | Base value | New value |
|-------|--------|------------|-----------|
| `--color-background` | light | — | `#f3eee3` |
| `--color-background` | dark | — | `#10161c` |
| `--color-surface` | light | — | `#fbf8f2` |
| `--color-surface` | dark | — | `#17202a` |
| `--color-surface-2` | light | — | `#ebe3d2` |
| `--color-surface-2` | dark | — | `#202b36` |
| `--color-text-primary` | light | — | `#1d2831` |
| `--color-text-primary` | dark | — | `#ebe5d8` |
| `--color-text-secondary` | light | — | `#4a5560` |
| `--color-text-secondary` | dark | — | `#a8b1ba` |
| `--color-border` | light | — | `#d3c6ad` |
| `--color-border` | dark | — | `#34424f` |
| `--color-primary` | light | — | `#2b4256` |
| `--color-primary` | dark | — | `#a3bfd8` |
| `--color-primary-soft` | light | — | `#d6e0e8` |
| `--color-primary-soft` | dark | — | `#1f3244` |
| `--color-accent` | light | — | `#8f5312` |
| `--color-accent` | dark | — | `#e2ab5f` |
| `--color-accent-soft` | light | — | `#ecd3a4` |
| `--color-accent-soft` | dark | — | `#433018` |
| `--color-semantic-success` | light | — | `#44632f` |
| `--color-semantic-success` | dark | — | `#a1c487` |
| `--color-semantic-error` | light | — | `#973a1e` |
| `--color-semantic-error` | dark | — | `#eb937a` |
| `--color-focus` | light | — | `#1c5d96` |
| `--color-focus` | dark | — | `#7fb6ea` |
| `--color-border-strong` | both | — | = text-secondary |
| `--color-semantic-warning` | both | — | = accent |
| `--color-semantic-success-soft` | light | — | `#dbe6cf` |
| `--color-semantic-success-soft` | dark | — | `#243420` |
| `--color-semantic-error-soft` | light | — | `#f1d5c9` |
| `--color-semantic-error-soft` | dark | — | `#3f2219` |
| `--color-semantic-warning-soft` | both | — | = accent-soft |
| `--color-scrim` | both | — | `rgba(16, 22, 28, 0.55)` |
| `--color-print-paper` | both | — | `#ffffff` |
| `--color-print-ink` | both | — | `#000000` |
| `--color-print-rule` | both | — | `#cccccc` |
| `--shadow-1` | light | — | `0 1px 0 rgba(40,30,10,.05), 0 6px 18px -12px rgba(40,30,10,.25)` |
| `--shadow-1` | dark | — | `0 1px 0 rgba(0,0,0,.3), 0 8px 20px -14px rgba(0,0,0,.8)` |
| `--shadow-2` | both | — | `0 20px 50px -20px rgba(0,0,0,.5)` |
| `--font-sans` | both | — | `system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif` |
| `--font-mono` | both | — | `ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace` |
| `--font-cjk` | both | — | `"Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic", "Apple SD Gothic Neo", "Malgun Gothic", "PingFang SC", "Microsoft YaHei", "Noto Sans CJK JP", "Noto Sans CJK KR", "Noto Sans CJK SC"` |
| `--text-xs` | both | — | `0.75rem` |
| `--text-sm` | both | — | `0.875rem` |
| `--text-base` | both | — | `1rem` |
| `--text-lg` | both | — | `1.125rem` |
| `--text-xl` | both | — | `1.25rem` |
| `--text-2xl` | both | — | `1.5rem` |
| `--text-3xl` | both | — | `1.875rem` |
| `--space-1` | both | — | `4px` |
| `--space-2` | both | — | `8px` |
| `--space-3` | both | — | `12px` |
| `--space-4` | both | — | `16px` |
| `--space-6` | both | — | `24px` |
| `--space-8` | both | — | `32px` |
| `--space-12` | both | — | `48px` |
| `--radius-sm` | both | — | `4px` |
| `--radius-md` | both | — | `8px` |
| `--radius-lg` | both | — | `12px` |
| `--radius-full` | both | — | `9999px` |
| `--size-touch` | both | — | `44px` |
| `--size-print-page` | both | — | `794px` |
| `--duration-fast` | both | — | 100 ms |
| `--duration-base` | both | — | 200 ms |
| `--duration-slow` | both | — | 300 ms |
| `--ease-standard` | both | — | cubic-bezier(0.4, 0, 0.2, 1) |
| `--ease-enter` | both | — | cubic-bezier(0, 0, 0.2, 1) |
| `--ease-exit` | both | — | cubic-bezier(0.4, 0, 1, 1) |

## Modified
| Token | Scheme | Base value | New value |
|-------|--------|------------|-----------|

## Components
| Component | Action |
|-----------|--------|
| Primary button | added |
| Secondary button | added |
| Card | added |
| "Waiting for you" card | added |
| Status pill | added |
| Tag | added |
| Risk state tag | added |
| "Your approval" tag | added |
| Table row | added |
| Terminal block | added |
| Modal overlay | added |
| Tabs | added |
| Language switch | added |
| Progress steps | added |
| Summary fact tile | added |
| Section TOC | added |
| Details expander | added |
| Toast | added |

## Pairs
| Text token | Background token | Level |
|------------|------------------|-------|
| `--color-text-primary` | `--color-background` | AA |
| `--color-text-primary` | `--color-surface` | AA |
| `--color-text-primary` | `--color-surface-2` | AA |
| `--color-text-secondary` | `--color-background` | AA |
| `--color-text-secondary` | `--color-surface` | AA |
| `--color-text-secondary` | `--color-surface-2` | AA |
| `--color-primary` | `--color-surface` | AA |
| `--color-accent` | `--color-surface` | AA |
| `--color-accent` | `--color-surface-2` | AA |
| `--color-semantic-success` | `--color-surface` | AA |
| `--color-semantic-error` | `--color-surface` | AA |
| `--color-background` | `--color-primary` | AA |
| `--color-text-primary` | `--color-accent-soft` | AA |
| `--color-text-primary` | `--color-primary-soft` | AA |
| `--color-text-primary` | `--color-semantic-success-soft` | AA |
| `--color-text-primary` | `--color-semantic-error-soft` | AA |
| `--color-text-primary` | `--color-semantic-warning-soft` | AA |
| `--color-semantic-success` | `--color-surface-2` | AA |
| `--color-semantic-error` | `--color-surface-2` | AA |
| `--color-semantic-warning` | `--color-surface-2` | AA |
| `--color-accent` | `--color-background` | AA |
| `--color-primary` | `--color-background` | AA |
| `--color-background` | `--color-text-primary` | AA |
| `--color-print-ink` | `--color-print-paper` | AA |
| `--color-focus` | `--color-background` | UI (non-text) |
| `--color-focus` | `--color-surface` | UI (non-text) |
| `--color-focus` | `--color-surface-2` | UI (non-text) |
