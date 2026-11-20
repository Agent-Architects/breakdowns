---
name: when-to-consult-advisor
description: "Decide when to call the advisor tool (a stronger model you can consult mid-task in Claude Code). Use this at decision points: before committing to a plan or architecture, before any irreversible or outward-facing action (migrations, deletes, deploys, sends, publishes, payments, enabling a schedule), after the same error or failed fix comes back twice, when sources or evidence conflict, when requirements are ambiguous, before declaring a multi-step task done, and before shipping anything security-, money- or data-sensitive. Covers software development, knowledge work and automation building. Do not consult for routine edits, lookups or anything you can verify yourself in one step."
---

# When to consult your advisor

You can call the advisor tool to get a second opinion from a stronger model. It reads the
whole conversation, including every tool call and result, and sends back guidance. Each call
costs tokens at the advisor's rates, so call it where a wrong move is expensive, not on
every turn.

## The rule of thumb

Consult the advisor when **a mistake here would be expensive to undo, or you have already
been wrong once**. Do not consult it when you can check the answer yourself in one cheap step
(run the test, read the file, grep the code).

## Always consult (any kind of work)

1. **Before you commit to a plan** on a task that will take many steps or touch many files.
   Ask: "Here is my plan. What is wrong with it, and what am I missing?"
2. **Before an irreversible or outward-facing action**: deleting data, a database migration,
   force-pushing, deploying, sending an email or message, publishing, spending money,
   changing permissions, enabling a scheduled job.
3. **When the same failure comes back.** The same error twice, or a fix that did not fix it.
   Stop looping and ask what you are missing before the third attempt.
4. **Before you say "done"** on a multi-step task. Ask the advisor to check the result
   against the original request.
5. **When you are unsure and guessing.** If you notice you are choosing between two
   reasonable readings of the request, or filling a gap with an assumption that matters.

## Software development

| Moment | Why it pays off |
|---|---|
| Choosing an architecture, data model or library | Hard to change later; a weak early choice spreads everywhere |
| Planning a refactor that touches many files | One wrong pattern gets copied 50 times |
| Writing or reviewing a migration, schema or data backfill | Data loss is not undoable |
| A bug you cannot reproduce, or a fix that did not hold | You are likely missing the real cause |
| Flaky or intermittent failures (timing, concurrency, caching) | Easy to "fix" the symptom, not the cause |
| Security-sensitive code: auth, permissions, secrets, input handling | Mistakes are invisible until exploited |
| Performance work that changes behavior (caching, batching, async) | Correctness bugs hide inside speed-ups |
| Deleting code or dependencies you did not write | You may not know what still depends on it |
| Tests pass but you changed or skipped a test to get there | A second look catches "made the test agree with the bug" |
| Before opening a PR on a large diff | Cheaper than a failed review cycle |

## Knowledge work (research, writing, analysis)

| Moment | Why it pays off |
|---|---|
| Sources disagree, or a key fact has only one source | Picking the wrong one poisons the whole output |
| Before a recommendation or decision memo | The reasoning is the product; check it |
| Summarizing for someone who will act on it without reading the originals | Errors become their decisions |
| Numbers, money, legal, medical or contract language | High cost of a confident mistake |
| Final draft of anything public or sent to a client | Tone and accuracy can't be pulled back |
| You can't tell what the person actually wants | Ask the advisor how to read the request, or ask the person |

## Automation building (workflows, agents, scheduled jobs, integrations)

| Moment | Why it pays off |
|---|---|
| Designing the workflow before building it | Triggers, steps and failure paths are the whole design |
| Anything that sends, posts, pays or deletes on its own | It will run without a human watching |
| Before turning on a schedule, webhook or trigger | One bad run can repeat hundreds of times |
| Retries and duplicates (what happens if a step runs twice?) | Double sends and double charges come from here |
| Handling credentials, tokens or account access | Leaks and over-broad access are hard to undo |
| Error handling and alerts (how will anyone know it broke?) | Silent failures are the most expensive kind |
| Changing a workflow that is already live | You are editing something people depend on |

## Do NOT consult for

- Routine edits, renames, formatting, small one-file changes.
- Lookups you can do yourself: reading a file, searching the code, checking docs.
- Anything you can verify in one cheap step (run it, test it, read the output).
- Restating what you already know, or asking it to do the work for you.

## How to ask (gets better answers)

Give the advisor a focused question, not "thoughts?":

- **State the decision**: "I'm about to X. Before I do, check Y."
- **Name your doubt**: "I'm not sure whether A or B; here is why I lean A."
- **Ask for what would change your mind**: "What would make this the wrong call?"

When the advice conflicts with what you can see (a file, a test result, an error), trust the
evidence, tell the user about the conflict, and do not follow the advice blindly.

## Make it a habit (optional)

Put a short version in your project's `CLAUDE.md` so every session uses it:

```markdown
## Advisor
Consult the advisor before: committing to a multi-step plan, any irreversible or
outward-facing action, the third attempt at the same failure, and declaring a multi-step
task done. Don't consult for routine edits or anything you can verify yourself in one step.
```
