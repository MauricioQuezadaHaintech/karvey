# Design delta: wave3-optimization

The project has no `docs/spec/design-system.md` yet, so every token of this change's design-spec is **added** (light and
dark rows from the Color system table). Written after the fact for the E1.F11.T4 dogfooding run of the design judge
(F-68); the design-spec itself is unchanged.

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
