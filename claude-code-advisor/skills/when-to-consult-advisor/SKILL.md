---
name: when-to-consult-advisor
description: "Decide whether to call the advisor tool (a stronger model you can consult mid-task in Claude Code). Default is NOT to call it. Call it only at four moments on long or high-stakes work: once before committing to the plan, before an irreversible or outward-facing action with real blast radius (delete, migrate, deploy, send, publish, pay, enable a schedule), after the same problem has beaten you twice, and once before declaring a long task done. Budget: 0 calls on short tasks, about 1 to 3 on a long one. Never for routine edits, lookups, or anything you can verify yourself."
---

# When to consult your advisor

The advisor is a stronger model you can call mid-task. Every call re-reads the whole
conversation at the stronger model's rates, so it is expensive. **The default is: don't call it.**
Do the work, check it yourself, and save the advisor for the few moments where a second,
smarter opinion clearly pays for itself.

## The four moments (and only these)

1. **Before committing to the plan on a long task.** Once, after you've read enough to have a
   real plan, not before. Short tasks don't need this.
2. **Before an irreversible or outward-facing action with real blast radius.** Deleting data,
   a database migration, a deploy, sending or publishing something, spending money, changing
   permissions, switching on a schedule or webhook. Not for reversible local edits.
3. **After the same problem has beaten you twice.** Two failed fixes or the same error twice.
   Before the third attempt, ask what you're missing. One failure is normal; just debug it.
4. **Once before declaring a long task done**, to check the result against the original request.

## Budget

- Short task (a few steps, one or two files): **0 calls**.
- Long task (many steps, many files, hours of work): **about 1 to 3 calls** in total.
- If you've called it 3 times on one task, the problem is probably the plan or the request.
  Stop and ask the user instead.

## Never call it for

- Routine edits, renames, formatting, small changes.
- Lookups you can do yourself: read the file, search the code, check the docs.
- Anything you can verify in one cheap step: run the test, run the command, read the output.
- A single failure you haven't tried to debug yet.
- Reassurance. If you're not actually unsure, don't ask.

## Examples by kind of work

**Software development**: before committing to an architecture or data model on a new
feature; before running a migration or backfill; when a bug survived two fixes.

**Knowledge work**: before a recommendation someone will act on, when your key sources
disagree; before sending a final client-facing or public document.

**Automation building**: before switching on a workflow that sends, posts, pays or deletes
on its own; when a live workflow keeps failing after two fixes.

## How to ask

Make the question specific: "I'm about to X. Check Y before I do," or "Two fixes failed:
A and B. What am I missing?" If the advice contradicts what you can see (a file, a test result),
trust the evidence and tell the user about the conflict.

## Optional: add it to CLAUDE.md

```markdown
## Advisor
Default: don't call it. Only on long or high-stakes work: once before committing to the plan,
before an irreversible or outward-facing action, after the same problem beat you twice, and once
before declaring done. About 1 to 3 calls per long task, 0 on short ones.
```
