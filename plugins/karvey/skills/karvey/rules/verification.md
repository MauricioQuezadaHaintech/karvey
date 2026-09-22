# Rule: Verification (before reporting "done")

Every phase closes by reporting a result. This rule defines what makes a report **true**. It is
applied by every phase at close, enforced as a checklist by `karvey-guard`, and audited by
`karvey-qa` (Dimension 2) and `karvey-health`.

**The core rule:** *state what you verified, not what you expect.* If a deliverable makes a claim
about a file, a resource or a deployment, it was verified **in that session**, with a command, and
the evidence is cited. Everything below is a way that rule fails in practice. They are written as
symptoms because that is how they show up — all of them passed a check that felt sufficient.

## The failure modes

1. **A review appended at the end leaves the body lying.** Whoever arrives next reads top-down and
   stops at the old question without ever reaching the revision that closed it. When something is
   closed, **the body is corrected**; the revision stays as history, not as the only truth. Same for
   flags and markers: if a question was answered, rewrite the paragraph so a grep no longer counts it.

2. **Verifying the citation is not verifying what it cites.** A commit message naming a change, a
   comment naming a control, a spec naming a test — none of them prove the thing exists. **Where a
   control exists that measures it, run the control.**

3. **A comment describes the contract the author had in mind, not the one the code honors.** Rules,
   docs and headers that assert behavior are claims to test, not evidence.

4. **A green test over a function nobody calls is the most credible way to believe something is
   done.** Before trusting a suite, **count the call sites of what it proves**.

5. **"It failed" and "it never ran" are different, and they look identical in a dashboard.** The
   discriminator is **duration**: jobs of a few seconds across every run mean nothing executed.

6. **A pipe whose first link fails silently does not return an error — it returns a false answer.**
   `curl <host-that-does-not-resolve> | sha256sum` returns the hash of the empty string, **with exit
   code 0**. Verify each link produced something before believing the last one.

7. **Exit 0 is not success for every tool.** Some builders and submitters return 0 while the build
   failed. Query the job's real status instead of trusting the shell.

8. **A filename does not tell you which version it is.** A commit that replaces an asset **keeps the
   name**, so seeing the same name served proves nothing. Compare content: hash, bytes, dimensions.
   "Identical" is a measurement, not an impression.

9. **Do not conclude the app's logic from the bundle.** Calls counted in a production bundle may come
   from a dependency, not from your source. Read the source. For "is my version published?", the
   cheap answer is a build stamp the app exposes.

10. **And the reverse: do not conclude what is seen from the source.** Whoever looks at the render and
    whoever reads the code see different things and both are right; the diagnosis comes from crossing
    them. Reading only the source, "there is no defect"; seeing only the screenshot, the natural fix
    is to edit the text — and that touches approved copy to hide a styling problem.

11. **A versioned file does not prove what is applied.** Infrastructure, IAM and settings are verified
    against the live resource, with a read-only check.

12. **A switch is not a permission.** A flag says "this may be shown", never "this may be collected or
    promised". Before turning something on, look at what else hangs off it.

13. **Merging onto someone else's file: bring their branch first.** Announcing it is not enough and a
    passing test is not enough — git can fast-forward over a correction **without a single conflict**
    and revert it silently.

14. **A frozen baseline ages.** A test comparing against an old baseline confirms you broke nothing
    *relative to something that no longer exists*. Re-point the baseline, with the reason written
    beside it.

15. **A decision is applied, not pasted on top — and it is easy to over-apply.** Go to the code or the
    mockup and look for what contradicts it. Ask also **what the decision did not say**: reading "it
    is not fixed in advance" as "the concept does not exist" deletes a state that was legitimate.
    A test written on a wrong assumption makes the error invariant.

16. **Sweeping by word can leave the sentence just as false.** Replacing a term while the promise
    survives changes nothing. Sweep by **what the sentence promises**, not by how it says it.

17. **Describing a file from memory is not verifying it: open it.** If an entry claims something about
    a file, that file was read in that session.

18. **Before declaring something blocked on a pending decision, cross it against the decision log** —
    and against wherever product offers are recorded. A block is written as *"searched the log, no
    answer exists"*, or it is not written. See `karvey-decisions`.

## How it is applied

- **At every phase close:** the report cites the command and its output for each claim. A claim that
  cannot be verified is stated as unverified, **with the reason**, and never dropped.
- **`karvey-guard`** ships this list as a pre-report checklist (`--verify`).
- **`karvey-qa`** treats an unverifiable claim in a deliverable as a Dimension-2 finding.
- **Teams amplify all of it** (`team.md`): a false claim crossing between agents is acted on before
  it is corrected, so the correction arrives after the damage.
