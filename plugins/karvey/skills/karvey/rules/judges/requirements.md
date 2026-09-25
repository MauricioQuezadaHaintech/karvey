# Judge rubric: requirements

Inputs: `requirements.md`, `spec-delta.md`, `prd.md`, `spec.json:goal`. Each lens answers its questions with
findings that cite a line of these files.

## Lens: domain

- Does every requirement serve the goal in `spec.json:goal`, and does the goal need a requirement that is missing?
- Is each requirement stated in the domain's words, with its actors and data named, or does it hide a decision
  that the domain owner must take?
- Are the error scenarios the ones the domain actually meets (limits, empty states, concurrent use, legacy data)?
- Does any requirement contradict another, the PRD or a decision it cites?

## Lens: methods

- Is every requirement in EARS form, testable, and with one success and one error scenario?
- Is each requirement one behaviour (not two joined by "and"), with a measurable condition instead of an
  adjective ("fast", "simple")?
- Does the spec-delta list every requirement the change adds, modifies or removes?
- Could a test be written from the text alone, without asking the author?
