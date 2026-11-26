# Weekly skill audit prompts

Two versions. A is for running it yourself in a chat. B is for a scheduler (no one is there to answer questions, so it never asks and never changes anything).

Before first use: replace `<YOU>` paths if your folders differ, and make sure `self-improve` is installed (see README step 1). skill-creator is only needed for the manual step after the scheduled run.

## A. Run it yourself (fresh chat)

```
Run my weekly skill audit. Apply nothing until I approve.

1. Find my most-used skills. Run the self-improve skill's retro.py "triggers" command with no --skill over my last 7 days of transcripts (Claude Code: every folder in ~/.claude/projects; Codex: ~/.codex/sessions if it exists). Read the table at the top and pick the 3 skills with the most triggers. Skip built-in slash commands (exit, clear, compact, model, resume and similar), skip self-improve and skill-creator themselves. Tell me the 3 and their counts.

2. For each of those 3 skills, follow the self-improve procedure steps 1 to 6: collect (triggers, signals, hooks, tokens, lint), review each trigger (followed, drifted, skill-caused, not reached, missing), map my corrections, judge hooks, token and context pass, then write the report with the report template. Every finding needs transcript:line evidence and a proposed diff. Work folder: ~/skill-audits/<today's date>/. Do not edit any skill, rules file, hook or memory.

3. For each skill where a finding is "not reached", "missing", or I had to remind the agent to use it, draft a 20-prompt trigger eval set for skill-creator's description optimization: 10 should_trigger true (different phrasings of the same job, formal and casual, some that never name the skill, taken from real "Asked before" lines and my corrections) and 10 should_trigger false (near misses that share words with the skill but need something else). Save as ~/skill-audits/<today's date>/<skill>/trigger-evals.json in the format [{"query": "...", "should_trigger": true}]. Remove secrets, names of other people and anything private from the prompts.

4. Write ~/skill-audits/<today's date>/SUMMARY.md: the 3 skills with trigger counts, the top 3 findings across all of them (one line each: skill, what happened, proposed change, expected effect), and which skills have an eval set ready for me to review. Then tell me the same in the chat.

Do not run the skill-creator optimization loop. I review the eval sets first.
```

After it finishes: review `SUMMARY.md`, edit each `trigger-evals.json` (README step 3), run the loop (step 4), apply and re-test (step 5).

## B. Scheduler version (Claude Code Desktop task, `claude -p`, or Codex scheduled task)

Paste this as the task's instructions. It does the read-only part only. Run it from the folder `~/skill-audits` (create it first).

```
Run the self-improve skill as the weekly skill audit. Do not ask me questions and do not change any skill, rules file, hook, memory or schedule.

1. Create the folder ~/skill-audits/<today's date as YYYY-MM-DD>/.
2. Run the self-improve skill's retro.py "triggers" command, with no --skill, over my last 7 days of transcripts (every folder in ~/.claude/projects, and ~/.codex/sessions if it exists), writing triggers-all.md in that folder. Pick the 3 skills with the most triggers, skipping built-in slash commands (exit, clear, compact, model, resume and similar) and skipping self-improve and skill-creator.
3. For each of the 3 skills, follow the self-improve procedure steps 1 to 6 and write its report in that folder, with transcript:line evidence and a proposed diff for each finding. Status must be PROPOSED, nothing applied.
4. For each skill with a "not reached" or "missing" finding, or where I had to remind the agent to use it, write a 20-prompt trigger eval set at <skill>/trigger-evals.json in that folder: 10 should_trigger true, 10 should_trigger false (near misses), real phrasings from the transcripts, no secrets or other people's details. Format: [{"query": "...", "should_trigger": true}].
5. If last week's folder in ~/skill-audits has an eval set for the same skill, also run skill-creator's run_eval.py on this week's current description with that set and add the pass rates to the report ("did the fix hold?"). Skip this step if skill-creator is not installed.
6. Write SUMMARY.md in that folder: the 3 skills with trigger counts, top 3 findings (skill, what happened, proposed change, expected effect), and the skills with an eval set ready for review. Print the same summary as your final message.
```

Notes:

- Step 5 calls `claude -p` many times (each prompt runs 3 times), so it costs usage. Delete step 5 if you want the scheduled run to stay cheap. Call it with Python 3.10 or newer.
- The scheduled run never edits skills. That is on purpose: self-improve "proposes only", and skill-creator's loop needs you to review the eval set first.
