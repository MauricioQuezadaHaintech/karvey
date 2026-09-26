# Design system

Seed for the tests: the colour tokens of a design spec (fictional first UI change `sample-first-ui`).

## Colour

| Token | Light | Dark | Changed by |
|-------|-------|------|------------|
| `--color-background` | `#f3eee3` | `#10161c` | sample-first-ui |
| `--color-surface` | `#fbf8f2` | `#17202a` | sample-first-ui |
| `--color-surface-2` | `#ebe3d2` | `#202b36` | sample-first-ui |
| `--color-text-primary` | `#1d2831` | `#ebe5d8` | sample-first-ui |
| `--color-text-secondary` | `#4a5560` | `#a8b1ba` | sample-first-ui |
| `--color-border` | `#d3c6ad` | `#34424f` | sample-first-ui |
| `--color-border-strong` | = text-secondary | = text-secondary | sample-first-ui |
| `--color-primary` | `#2b4256` | `#a3bfd8` | sample-first-ui |
| `--color-primary-soft` | `#d6e0e8` | `#1f3244` | sample-first-ui |
| `--color-accent` | `#8f5312` | `#e2ab5f` | sample-first-ui |
| `--color-accent-soft` | `#ecd3a4` | `#433018` | sample-first-ui |
| `--color-semantic-success` | `#44632f` | `#a1c487` | sample-first-ui |
| `--color-semantic-error` | `#973a1e` | `#eb937a` | sample-first-ui |
| `--color-semantic-warning` | = accent | = accent | sample-first-ui |
| `--color-focus` | `#1c5d96` | `#7fb6ea` | sample-first-ui |

## Spacing

| Token | Light | Dark | Changed by |
|-------|-------|------|------------|
| `--space-1` | `4px` | = | sample-first-ui |
| `--space-4` | `16px` | = | sample-first-ui |

## Motion

| Token | Value | Changed by |
|-------|-------|------------|
| `--duration-fast` | `100ms` | sample-first-ui |

## Components

| Component | Changed by |
|-----------|------------|
| Card | sample-first-ui |
| Status pill | sample-first-ui |

## Pairs

| Text token | Background token | Level |
|------------|------------------|-------|
| `--color-text-primary` | `--color-background` | AAA normal |
| `--color-text-primary` | `--color-surface` | AAA normal |
| `--color-text-primary` | `--color-surface-2` | AAA normal |
| `--color-text-secondary` | `--color-background` | AA normal |
| `--color-text-secondary` | `--color-surface` | AA normal |
| `--color-text-secondary` | `--color-surface-2` | AA normal |
| `--color-primary` | `--color-surface` | AA normal |
| `--color-accent` | `--color-surface` | AA normal |
| `--color-accent` | `--color-surface-2` | AA normal |
| `--color-semantic-success` | `--color-surface` | AA normal |
| `--color-semantic-error` | `--color-surface` | AA normal |
| `--color-background` | `--color-primary` | AA normal |
| `--color-focus` | `--color-background` | UI |
