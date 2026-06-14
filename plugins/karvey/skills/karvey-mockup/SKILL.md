---
name: karvey-mockup
description: Generate a navigable HTML mockup with 3 levels of depth from approved requirements. Iterate with user until approved, then advance to graphic design. Triggers include "karvey mockup", "generar mockup", "generate mockup", "crear prototipo", "create prototype", "wireframe".
allowed-tools: Read, Write, Edit, Bash, Glob, AskUserQuestion
argument-hint: <change-id> [--iteration N] [--shotgun | --variants N]
---

# Karvey Mockup — Navigable HTML Prototype

## Purpose

Generate a navigable HTML file with 3 levels of depth before defining the graphic design. The engineer navigates the mockup in the browser, gives feedback, and it's iterated until approval. Only afterward does it advance to graphic design and architecture.

## Target agnosticism

The mockup **adapts to the target declared** in `docs/spec/project.json` (the `targets` field) — see `karvey/rules/targets.md`. **Don't assume web by default:**

- **web** → navigable HTML (App Shell + views + overlays, as described below)
- **mobile (ios/android)** → screen flow (a sequence of screens with transitions, not a desktop sidebar)
- **cli** → command transcript (example terminal input/output)
- **api/backend** → request/response examples (sample payloads per endpoint)

The levels, rules, and HTML structure in the following sections apply to the **web** target. For other targets, generate the target's equivalent artifact and likewise save it under `docs/spec/changes/{change-id}/` (adjusting the extension where appropriate, e.g. `mockup.md` for a CLI transcript or API examples). The rest of the flow (iteration, approval, knowledge sync) is identical.

## Generation modes

- **Normal mode (default)**: a single mockup proposal, iterated with the user until approval (Steps 1 to 6).
- **Shotgun mode (opt-in)**: generate **N variants** of the mockup at once (default **3**) with distinct design approaches, and offer a **comparison board** so the user can pick one or combine elements from several. Activated with the `--shotgun` flag (3 variants) or `--variants N` (N variants). Inspired by `/design-shotgun`. See **Step 3B**.

If the user doesn't pass a flag, always use normal mode.

## Navigation levels

- **Level 1 — App Shell**: Main navigation (sidebar/topbar with the product's sections)
- **Level 2 — Section**: Views of each section (lists, forms, dashboards)
- **Level 3 — Detail**: Detail views (modals, side panels, sub-views, wizards)

## Execution steps

### Step 1 — Load context

Read:
- `docs/spec/changes/{change-id}/spec.json`
- `docs/spec/changes/{change-id}/requirements.md`
- `docs/spec/changes/{change-id}/proposal.md`

Verify that `approvals.requirements.approved = true`. If not, stop and ask to approve requirements first.

**Check whether a UI applies:** Read `spec.json` → the `layers` field. If it only includes `[DB]` and/or `[Backend]` without `[Frontend]`, ask the user: "This change doesn't seem to have a user interface. Does it need a visual mockup or do we go straight to architecture?" If it doesn't need one, skip to karvey-architecture.

Detect iteration: if `docs/spec/changes/{change-id}/mockup.html` exists, increment the iteration number.

### Step 2 — Map screens from requirements

Build the screen map by reading the requirements:

```
Level 1 (Navigation):
  - {Section A} → requirements {N.N, N.N}
  - {Section B} → requirements {N.N, N.N}

Level 2 (Views per section):
  Section A:
    - List View: {what it shows}
    - Form View: {what it captures}
  Section B:
    - Dashboard View: {what it shows}

Level 3 (Details):
  - Confirmation modal
  - Detail panel
  - Step-by-step wizard
```

### Step 3 — Generate mockup.html

Generate a single self-contained HTML file:

**HTML structure:**
```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>MOCKUP — {change-id} — Iteration {N}</title>
  <!-- Tailwind CDN — for prototyping only, does not imply its use in the real project -->
  <script src="https://cdn.tailwindcss.com"></script>
  <style>/* additional styles */</style>
</head>
<body>
  <!-- Mockup banner, always visible -->
  <!-- App Shell with Level 1 navigation -->
  <!-- Level 2 views container (changes with navigation) -->
  <!-- Level 3 overlays (modals, panels) -->
  <!-- Navigation JavaScript -->
</body>
</html>
```

> Set `lang` on `<html>` to the project's language (per spec.json `language`).

**Construction rules:**

1. **Persistent banner** at the top: `🔧 MOCKUP — {change-id} — Iteration {N} — {date}`
2. **Level 1 navigation**: sidebar or topbar with placeholder icons (gray circles) and section names
3. **Level 2 views**: represent each screen as a view with:
   - The screen title
   - A table/list with real columns (real labels, example data coherent with the domain)
   - Buttons with real labels ("Transfer call", "Confirm", not "Button 1")
   - Forms with real fields and correct types
   - Loading states represented with gray skeletons
4. **Level 3**: modals and panels implemented as overlays shown/hidden with pure JS
5. **Navigation JS**: `showView(viewId)`, `showModal(modalId)`, `closeModal(modalId)` — no external dependencies
6. **Neutral palette**: grays only. The real project's color and design system will come in karvey-design-graphic.
7. **Basic responsive**: work at a minimum width of 1280px+
8. **Example data**: use fictitious but domain-coherent data (tenant names, real call types, etc.)

**Forbidden elements in the mockup:**
- Lorem ipsum (use real domain text)
- "Button 1", "Section A" (use real labels)
- External images (use divs with bg-gray-300)
- Heavy JS frameworks (only Tailwind CDN and native JS)

### Step 3B — Shotgun mode (only if `--shotgun` or `--variants N`)

Replaces Step 3/4 when shotgun mode is active. Instead of a single mockup, generate **N variants** (default 3) that explore distinct design approaches over the **same** screen map from Step 2 (same screens, real data, and labels — the approach varies, not the scope). Examples of variation axes: information density (compact vs. spacious), navigation pattern (sidebar vs. topbar vs. tabs), visual hierarchy, the main task's flow.

1. **Load taste preferences** (if they exist): read `docs/spec/changes/{change-id}/taste.md` and/or `docs/spec/taste.md`. Apply those preferences to all variants so as not to repeat already-discarded approaches.
2. **Generate N variants**, each self-contained and following all the "Construction rules" from Step 3 (neutral palette, real data, native JS, banner, etc.):
   ```
   docs/spec/changes/{change-id}/mockup-variant-1.html
   docs/spec/changes/{change-id}/mockup-variant-2.html
   docs/spec/changes/{change-id}/mockup-variant-N.html
   ```
   Each variant's banner includes its approach: `🔧 MOCKUP — {change-id} — Variant {k}/{N}: {approach} — {date}`.
3. **Generate a comparison board** `docs/spec/changes/{change-id}/mockup-board.html`: a self-contained page that shows the N variants side by side in `<iframe>`s (or cards with a screenshot/link to each file), each with its approach name and a 1-line summary of how it differs. The board lets you open each variant full size.
4. Update `spec.json` (see Step 4) with `approvals.mockup.variants: N` in addition to the normal fields.

**Choice and taste:** offer the user to open the board (`open docs/spec/changes/{change-id}/mockup-board.html`) and ask them to choose a variant or indicate what to combine ("the navigation from #1 with the tables from #3"). On receiving the choice:
- Consolidate the chosen variant (or the combination) as `mockup.html`, which becomes the working mockup for the normal iteration cycle (Step 6).
- **Remember the taste**: append to `docs/spec/changes/{change-id}/taste.md` which approach/elements they preferred and which they discarded, in short bullets, to guide future iterations and future shotgun runs for this change.

### Step 4 — Write the file

```
docs/spec/changes/{change-id}/mockup.html
```

Update `spec.json`:
- `phase: "mockup-generated"`
- `approvals.mockup.generated: true`
- `updated_at: {timestamp}`

### Step 4B — Update the knowledge graph

Sync knowledge per `karvey/rules/knowledge-sync.md` (Obsidian if available; at minimum `/graphify docs/spec/ --update`) to reflect the `mockup.html` created or modified.
If `docs/spec/graphify-out/` doesn't exist, invoke `/graphify docs/spec/` without `--update`.

### Step 5 — Present to the user

**Shotgun mode:** present the comparison board instead of a single file (`open docs/spec/changes/{change-id}/mockup-board.html`), list the N variants with their approach, and ask the user to choose one or indicate what to combine. After the choice, continue with the normal iteration cycle (Step 6) on the consolidated `mockup.html`.

**Normal mode:**

```
🖥️ Mockup generated — Iteration {N}

File: docs/spec/changes/{change-id}/mockup.html
Open with: open docs/spec/changes/{change-id}/mockup.html

Screens included ({N} total):
  Level 1 — Navigation:
    - {section 1}
    - {section 2}
  Level 2 — Views:
    - {section 1}: {view A}, {view B}
    - {section 2}: {view C}
  Level 3 — Details:
    - {modal/panel 1}
    - {modal/panel 2}

What feedback do you have? Describe the changes and I'll generate Iteration {N+1}.
Or type "approved" to advance to graphic design.
```

### Step 6 — Iteration cycle

If the user gives feedback:
1. Read the feedback in detail
2. Identify which screens/components to change
3. Edit `mockup.html` applying the changes
4. Increment the iteration number in the banner
5. Sync knowledge per `karvey/rules/knowledge-sync.md` (Obsidian if available; at minimum `/graphify docs/spec/ --update`)
6. Return to Step 5

If the user approves:
- Update `spec.json`: `approvals.mockup.approved: true`
- Output:
```
✅ Mockup approved — Iteration {N}

Next step:
/karvey-design-graphic {change-id}
```

## Safety

- Verify that requirements are approved before generating
- If the mockup has >20 screens, ask whether to split it into modules
- In shotgun mode, if `--variants N` requests more than 5 variants, ask first (cost/noise); each variant and the board must open without errors in a modern browser
- The HTML file must open without errors in a modern browser (Chrome/Safari/Firefox)
- Don't use `document.write` or `eval` in the generated JS


## Advance to the next phase

When you finish this phase and have the corresponding approval, **actively ask the user**: "Shall we advance to the Graphic Design phase now?"
- If they confirm → run `/karvey-design-graphic {change-id}`.
- If they prefer to review or adjust first → wait. Advancing is always with the user's OK (a gate of the method).
- If you resume in another session, `/karvey {change-id}` indicates which phase you're on and which one comes next.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`. Karvey = Afán, an ona/selknam word.*
