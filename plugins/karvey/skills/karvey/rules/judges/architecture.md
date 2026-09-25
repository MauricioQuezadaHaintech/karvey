# Judge rubric: architecture

Inputs: `architecture.md`, `requirements.md`, `spec.json:goal`. Each lens answers its questions with findings
that cite a line of these files.

## Lens: security

- Does the design name every trust boundary, and a control for each one, at the change's Security Tier?
- Can a value read from a file, a tool output or a user reach a command, a query or an approval unchecked?
- Are secrets, credentials and personal data kept out of the repository, the logs and the prompts?
- Does any component fail open where the requirement asks it to fail closed?

## Lens: methods

- Does every requirement map to a component, and every component to a requirement?
- Is each decision recorded with its options and the reason for the one taken?
- Is the test coverage plan concrete (suite, level, requirement) for every requirement?
- Is the migration and rollout safe for existing data and existing users?

## Lens: agents-cost

- Which steps does the design leave to the model's judgement where a script could decide deterministically?
- What does the design add to the context of every session (files read, prompts, tools), and is it bounded?
- Are subagents given closed inputs and a narrow tool list?
- Is the cost of the new steps measured, and can it be seen per change?
