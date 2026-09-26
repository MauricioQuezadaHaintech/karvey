# Judge rubric: design_graphic

Inputs: `design-delta.md`, the mockup files the design-spec's "Applies to" line names (each at most 200 KB),
`contrast.json` (the output of `karvey-contrast-check.py --delta {change} --json`) and `spec.json:goal`. The contrast
result is the deterministic sub-score: cite it, never recompute or contradict it. Each lens answers its questions
with findings that cite a line of these files. The design phase does not score itself (REQ-W3-039).

## Lens: design

- Does the delta add or modify only what the mockup needs, reusing the design system's tokens and components
  instead of redefining them?
- Does every text/background pair the mockup uses appear in `contrast.json`, and does any pair fall below its level?
- Is meaning ever carried by colour alone, or is every state also written as a word?
- Do the screens hold one visual hierarchy (what the reader must do first is seen first) at the narrowest width?
- Is focus visible on every control, and is motion limited to state changes with reduced motion honoured?
- Does any value in the mockup (colour, size, spacing) appear in neither the design system nor the delta?
