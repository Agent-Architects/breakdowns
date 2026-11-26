# Make your agent use its skills when it should

You commented LEARN, so here's the full breakdown.

**The short version.** Your agent doesn't load a skill because it's installed. At startup it only sees each skill's name and description, and it decides from that alone whether to open the full SKILL.md. If the description doesn't sound like the way you actually ask, or you have a pile of skills with overlapping descriptions, the skill just sits there. The fix is a loop you run every week: one skill reads your transcripts to find where your agent skipped or misused a skill (analyze), Anthropic's skill-creator tests the description on 20 prompts and rewrites it (prevent and optimize), you approve the change and re-test in a fresh chat (fix). Everything you need to run it is in this folder.

## Why your agent skips your skills

In the short I say: "when your agents boot up, they only have the description of each skill that you have installed loaded in the context window and have to decide to load the full SKILL.md file."

That's straight from the docs:

- "until a Skill is triggered, only its name and description occupy context." ([Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview))
- "The `description` is what Claude matches your request against when determining whether to trigger the Skill, so it must say both what the Skill does and when to use it." (same page)
- Codex works the same way: "ChatGPT or Codex can choose a skill when your task matches the skill `description`." ([Codex docs, Build skills](https://learn.chatgpt.com/docs/build-skills))

This is the model's judgment over a text list, not keyword matching. Words still matter because the model compares your words with the description's words. Anthropic's own troubleshooting step is "Check the description includes keywords users would naturally say" ([Claude Code skills](https://code.claude.com/docs/en/skills)).

And it leans toward not loading. Anthropic's skill-creator says: "currently Claude has a tendency to 'undertrigger' skills, to not use them when they'd be useful." ([skill-creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md))

The usual reasons a skill silently never runs:

| Cause | Where |
|---|---|
| Vague description ("Helps with documents") or one that describes how it works instead of the job you ask for | Both |
| No "use when" part | Both |
| The request is simple enough that the model just does it itself. skill-creator: "Simple, one-step queries like 'read this PDF' may not trigger a skill even if the description matches perfectly" | Both |
| Broken YAML or frontmatter not on line 1: the skill loads with no description, `/name` works, auto never fires | Claude Code |
| Misspelled field (`Description:`, `when-to-use`), silently ignored | Claude Code |
| Too many skills: the listing gets about 1% of the context window and drops descriptions starting with the skills you use least | Claude Code |
| Too many skills: the list gets 2% of the window, descriptions get shortened first, then skills get left out with a warning | Codex |
| Main use case buried at the end of a long description, cut off by the cap (1,536 chars in Claude Code, 1,024 in the open spec and Codex) | Both |
| Another skill with an overlapping description wins | Both |
| First-person description ("I can help you...") | Claude |

Sources: [Claude Code skills](https://code.claude.com/docs/en/skills), [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices), [Agent Skills spec](https://agentskills.io/specification), [Codex docs](https://learn.chatgpt.com/docs/build-skills).

That "use least, lose the description first" one is nasty. A skill you rarely use loses its description, so it gets used even less.

## Treat it like an experiment

In the short I say this is "fundamentally a problem of behavior, so we can solve it from a scientific mindset." Two skills, two jobs:

| Step | Tool | What happens |
|---|---|---|
| Analyze | self-improve (included here) | Reads your last week of transcripts, finds every time a skill ran, and sorts each run: followed, drifted (skipped or bent a step), skill-caused (the skill itself was wrong or stale), not reached (the agent never read that part), missing (no rule covers it). Also collects every time you corrected the agent. |
| Prevent | skill-creator (Anthropic) | You write 20 test prompts: 8 to 10 that should load the skill, 8 to 10 near misses that shouldn't. |
| Optimize | skill-creator (Anthropic) | Its description loop runs every prompt 3 times, rewrites the description from the failures for up to 5 rounds, and picks the winner by its score on held-out prompts it didn't tune on. Optional HTML report. |
| Fix | You | Read the before and after, apply the change you approve, re-test in a fresh chat. |

self-improve looks backward at what your agent actually did. skill-creator looks forward at what it would do for a set of prompts. Neither one changes a file without you.

**Credit:** skill-creator is Anthropic's, not mine. Source: [anthropics/skills, skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator). It's Apache-licensed per the LICENSE.txt in that folder. Install it from there or the plugin marketplace, I'm not repackaging it here.

The real unlock, like I say in the short, is putting this on a schedule. Every week you collect more data about how your agent behaves around each skill, and the descriptions keep getting tighter. `schedule.md` has the exact setup.

## What's in this folder

| File | What it is |
| :- | :- |
| `README.md` | This page: why skills get skipped, install, and the weekly audit step by step |
| [`weekly-audit-prompt.md`](weekly-audit-prompt.md) | Copy-paste prompts: one to run by hand, one for a scheduler |
| [`schedule.md`](schedule.md) | Exact steps to run the audit every week in Claude Code (Desktop app, or `claude -p` with cron or launchd) and Codex, plus an example for agent frameworks with their own cron |
| [`skills/self-improve/`](skills/self-improve/) | The self-improve skill: `SKILL.md`, `references/`, `scripts/retro.py` (Python standard library only, read-only, redacts keys, tokens and emails in its output) |
| [`examples/trigger-evals.example.json`](examples/trigger-evals.example.json) | A 20-prompt example eval set in skill-creator's format, so you can see the shape |

## What you need

- Claude Code (tested on 2.1.332) and/or Codex. self-improve reads both tools' transcripts.
- Python 3 for `retro.py` (standard library only).
- For the skill-creator description loop: Claude Code (the loop shells out to the `claude` command) and **Python 3.10 or newer** (its scripts use `str | None` annotations; the default `python3` on a stock Mac is 3.9, so call `python3.11` or similar explicitly). This part does not run in Codex. For a Codex-only skill use the manual check in step 6.

## Install

### 1. self-improve

Copy the folder so the file ends up at `<skills folder>/self-improve/SKILL.md`:

```bash
# Claude Code (personal skill, all projects)
mkdir -p ~/.claude/skills && cp -R skills/self-improve ~/.claude/skills/

# Codex (personal skill)
mkdir -p ~/.agents/skills && cp -R skills/self-improve ~/.agents/skills/
```

Claude Code picks up new skills in the current session (run `/reload-skills` if it doesn't show). Codex: restart it if the skill doesn't appear. Check with `/skills`.

### 2. skill-creator (Anthropic)

Pick one:

- Claude Code plugin: `/plugin install skill-creator@claude-plugins-official`
- Or clone https://github.com/anthropics/skills and copy `skills/skill-creator` into `~/.claude/skills/`

The description loop needs the `scripts/` folder, so make sure `run_loop.py`, `run_eval.py` and `improve_description.py` are in the copy you use. If you installed it as a plugin, find its folder (it is under `~/.claude/plugins/`) and run the scripts from there.

## The weekly audit, step by step

Use a work folder for the outputs, for example `~/skill-audits/<date>/`.

### 1. Pick your most-used skills

```bash
python3 ~/.claude/skills/self-improve/scripts/retro.py triggers ~/.claude/projects/* --since 7 --max 1 --out ~/skill-audits/$(date +%F)/triggers-all.md
```

Add `~/.codex/sessions` as another target if you use Codex. Read the table at the top: `skill | triggers | read | partial-read | ...`. Take the top 3 skills by triggers. Ignore rows that are built-in slash commands (for example `exit`), the script counts those too.

Claude Code's `/skill-doctor` also shows how often each skill is used and flags skills that were never invoked.

### 2. Analyze with self-improve

Open a fresh chat and run the prompt in `weekly-audit-prompt.md` (version A), or just say:

> Run the self-improve skill for `<skill>` over the last 7 days. Work folder `~/skill-audits/<date>`. Apply nothing.

It follows its own procedure: collect (`triggers`, `signals`, `hooks`, `tokens`, `lint`), review each trigger (followed, drifted, skill-caused, not reached, missing), map your corrections to the file that should change, judge hooks, check token and context cost, then write one report per skill and stop. Read the report. Every finding has `transcript:line` evidence, a proposed diff and a "check next cycle" line.

Look especially for: **not reached** (the rule was in the skill but the agent never read that part: a structure problem, fix by moving the rule up or splitting the file, not by adding emphasis), and the corrections where you had to push the agent back to a skill.

### 3. Prevent: write the trigger test

For each skill with a description problem (skipped, never read, or you had to remind the agent), write 20 prompts as JSON, in the format of `examples/trigger-evals.example.json`:

```json
[{"query": "the prompt, as you would really type it", "should_trigger": true}]
```

- 8 to 10 should-trigger prompts: different phrasings of the same job, formal and casual, with real file names and backstory, some where you never say the skill's name. Take real phrasings from the `Asked before:` lines in `triggers.md` and the corrections in `signals.md`.
- 8 to 10 should-not prompts that are near misses: they share words with the skill but need something else. "Write a fibonacci function" as a negative for a PDF skill is too easy, it tests nothing.

skill-creator can generate and review the set with you (its Description Optimization Steps 1 and 2). This review step matters: bad eval prompts produce bad descriptions.

### 4. Optimize: run the loop

From the skill-creator folder, using Python 3.10 or newer:

```bash
python3.11 -m scripts.run_loop \
  --eval-set ~/skill-audits/<date>/<skill>/trigger-evals.json \
  --skill-path ~/.claude/skills/<skill> \
  --model <the model id you use day to day> \
  --max-iterations 5 --verbose \
  --report none --results-dir ~/skill-audits/<date>/<skill>/loop
```

What it does: splits the set 60/40, runs every prompt 3 times per round with `claude -p` (a run counts if Claude calls the Skill tool for it), asks Claude to rewrite the description from the failures, re-scores on train and held-out prompts, and returns `best_description` chosen by the held-out score. Leave `--report none` off to get an HTML report that opens in your browser. It never edits your SKILL.md.

Heads up: it runs many `claude -p` calls (20 prompts x 3 runs for each evaluation, several rounds), so it uses a noticeable amount of your plan or API usage. I haven't measured the cost, start with one skill. It sends your SKILL.md text to `claude -p`, so don't run it on a skill containing secrets. Use the same model you normally work with so the test matches your real behavior.

### 5. Fix: apply, then re-test

1. Read the before and after description and the scores. Check it is under 1,024 characters, third person, main use case first, and that it describes the job the way you ask for it. Don't paste in a list of the failed prompts, generalize (the loop is told the same).
2. Apply the diff you approve: put `best_description` in the skill's frontmatter, and apply any other change from the self-improve report (through your normal path, a branch and PR if the skill is in git).
3. Re-score the new description on the same set:

```bash
python3.11 -m scripts.run_eval --eval-set ~/skill-audits/<date>/<skill>/trigger-evals.json --skill-path ~/.claude/skills/<skill>
```

4. Re-test by hand: open a new chat, ask 2 or 3 of the should-trigger prompts as real tasks, and check the skill really loaded (Claude Code shows a `Skill` tool call; Codex announces the skill it's using and opens its SKILL.md). A fresh chat is a clean test, the old chat already has your earlier instructions in it.

### 6. No Claude Code? Manual check

Take the 5 or so ways you actually ask for the job. In a fresh Codex chat, ask each as a real task, 3 times each, and check whether the skill loaded. Add 2 near-miss prompts that should not load it. Rewrite the description: what it does in one line (third person, main use case first), then "Use when the user asks to ..." with your phrasings in quotes.

### 7. Repeat weekly

Keep the reports in one dated folder. Each report has a "check next cycle" line per finding. A finding that shows up twice means the text fix isn't enough: self-improve's rule is "if a rule keeps being skipped after two cycles, propose enforcing it in a script, a check or a hook", and "prefer moving or deleting text over adding it".

To make steps 1 and 2 run by themselves every week, see `schedule.md`. The eval loop (steps 3 to 5) is deliberately a human-in-the-loop step: you review the eval set, then run it.

## Copy-paste: a description that fires

Every source agrees on roughly this shape:

```text
description: <What it does, third person, one line, main use case first>. Use when the user asks to <job>, including "<real phrase 1>", "<real phrase 2>", "<real phrase 3>", even if they don't say "<formal term>". Not for <near-miss job>.
```

- What it does and when to use it, both.
- Third person.
- Main use case first, so truncation doesn't eat it.
- A little pushy ("even if they don't say..."). skill-creator recommends this because Claude undertriggers.
- Only add a "Not for" line if it really gets picked for the wrong job.
- Cover the idea, not just the one phrase that failed. agentskills.io: "Avoid adding specific keywords from failed queries, that's overfitting."
- Under 1,024 characters so it works everywhere.

## Copy-paste: quick trigger check (no scripts)

Paste this into a fresh chat in the folder with your skills.

```text
Audit my skills' triggers. Do not edit any file until I approve.

For each skill in my skills folders (Claude Code: ~/.claude/skills and .claude/skills; Codex: ~/.agents/skills and .agents/skills):
1. Show me its name and description word for word (and when_to_use if it has one). Flag broken frontmatter, misspelled field names, a description over 1,024 characters, or one written in first person.
2. Ask me how I usually ask for that job. Wait for 3 to 5 real phrasings from me.
3. For each phrasing, tell me honestly whether an agent that only sees the name and description would pick this skill, and why or why not.
4. Propose a new description: one line on what it does (third person, main use case first), then "Use when the user asks to ..." with my phrasings in quotes, then "Not for ..." only if it overlaps another skill.
5. Point out any two skills whose descriptions overlap.

At the end give me a test list: each phrasing as a real task, one fresh chat each, run 3 times, plus 2 near-miss requests that should NOT load the skill. Tell me what a load looks like in my tool so I can check it actually ran.
```

## Known limits

- self-improve starts from the skill runs and corrections it can find in your transcripts. A skill that never fired and was never mentioned leaves no trace, that is what the description eval in steps 3 and 4 covers.
- The script matches with regular expressions, so its output has noise. Its own procedure says to confirm each finding by reading the turn (`retro.py context <transcript> --line N`).
- The description loop tests a temporary copy of your description as a command, next to your installed skill. Treat the score as a strong signal and confirm in a fresh chat.
- Model behavior varies run to run. Re-run next week.

## Sources

- Anthropic, Agent Skills overview: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
- Anthropic, Skill authoring best practices: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- Claude Code docs, Skills: https://code.claude.com/docs/en/skills
- Claude Code docs, headless mode: https://code.claude.com/docs/en/headless
- Claude Code docs, Desktop scheduled tasks: https://code.claude.com/docs/en/desktop-scheduled-tasks
- Anthropic, skill-creator: https://github.com/anthropics/skills/tree/main/skills/skill-creator
- Agent Skills specification: https://agentskills.io/specification
- agentskills.io, Optimizing skill descriptions: https://agentskills.io/skill-creation/optimizing-descriptions
- OpenAI Codex docs, Build skills: https://learn.chatgpt.com/docs/build-skills
- OpenAI Codex docs, non-interactive mode: https://learn.chatgpt.com/docs/non-interactive-mode
- OpenAI Codex docs, scheduled tasks: https://learn.chatgpt.com/docs/automations
