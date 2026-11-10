# The context playbook: how to engineer your agent's context

You commented, so here's the full playbook.

The carousel said one thing: **every token you load competes for attention. Load less, get more right.**

Your agent doesn't remember anything between requests. Every turn, the whole window gets sent again: system prompt, tools, instruction files, skill descriptions, the conversation so far and every tool result. The more you stuff in, the more the model has to sort through, and the worse it gets at finding the part that matters.

This page has the five things slide 10 promised:

1. [All 7 steps](#1-all-7-steps), each with how to do it in Claude Code and Codex
2. [The load-order map](#2-the-load-order-map): what is always in the window and what loads later
3. [Token budget checklist](#3-token-budget-checklist)
4. [Starter templates](#4-starter-templates): a CLAUDE.md and a minimal skill
5. [Every source, linked](#5-every-source-linked)

Like the other breakdowns, it's written so you can hand it straight to your coding agent.

---

## The picture

```
            what the model sees on EVERY request
   +------------------------------------------------+
   | system prompt                       always     |
   | tool definitions                    always     |
   | CLAUDE.md / AGENTS.md (root)        always     |
   | skill names + descriptions          always     |
   | conversation history                grows      |
   | tool results                        grows      |
   | skill body                          on trigger |
   | nested CLAUDE.md                    on demand  |
   | files the agent read                on demand  |
   | the response                        counts too |
   +------------------------------------------------+
        re-sent in full, turn after turn
```

Context engineering is deciding what goes in that box, when it goes in, and when it comes out.

---

## 1. All 7 steps

### Step 1: Treat the window like a budget

**The point.** The context window is finite and every token spends some of it. Anthropic calls this the model's "attention budget". Every new token depletes it a little.

**Why it matters.** The Messages API is stateless, so you send the full conversation on every request. A big file you loaded on turn 2 is still being paid for on turn 40. Prompt caching makes repeated tokens cheaper, but they still take up the same space in the window. Caching changes the price, not the space.

**How to do it.**

- In Claude Code, run `/context`. It shows a live breakdown of what's in your window by category. Do this once on a fresh session so you know your baseline before you've typed anything.
- Look for the big always-on items: a long CLAUDE.md, lots of installed skills, MCP servers with dozens of tools you never use.
- Remove or move anything that doesn't earn its place on every single turn (steps 3 to 5 show where it goes).
- Run `/clear` between unrelated tasks instead of dragging one conversation across everything you do today.

### Step 2: More context, less accuracy

**The point.** Models get worse at using what's in the window as the window grows.

**Why it matters.** Three findings, all linked in section 5:

- **Context rot.** As the token count grows, accuracy and recall degrade. Chroma tested 18 models and found performance drops as input length increases, even on simple tasks.
- **Lost in the middle.** Accuracy is usually highest when the relevant information is at the start or the end of the context, and drops significantly when it's in the middle.
- **Distractors.** Content that's on topic but doesn't actually answer the question hurts. Even a single distractor reduces performance.

Behind all of this: a transformer relates every token to every other token, which Anthropic describes as n² pairwise relationships for n tokens. Double the tokens and attention gets spread a lot thinner.

**How to do it.**

- Don't paste whole logs, whole docs folders or whole codebases "just in case". The near-miss content is exactly the distractor that hurts.
- Put the thing that matters where the model sees it best: the task and the key constraint at the start of your message, and a short restatement at the end of long prompts.
- If the agent starts missing things it clearly saw earlier, that's context rot. Start a fresh session with a short summary instead of pushing on.

### Step 3: Load skills only when needed

**The point.** Progressive disclosure: load the name and description always, the body only when it's triggered, and extra files only when they're needed.

**Why it matters.** Anthropic's skills docs give the cost of each level:

| Level | What loads | When | Cost |
|---|---|---|---|
| 1 | `name` + `description` from the frontmatter | always, at startup | about 100 tokens per skill |
| 2 | the body of `SKILL.md` | when the skill is triggered | under 5k tokens |
| 3 | files in the skill folder (references, scripts) | as needed | nothing until accessed |

Scripts are the cheapest part: the script's code never loads into the window, only its output does.

**How to do it.**

- Put skills in `.claude/skills/<skill-name>/SKILL.md` (project) or `~/.claude/skills/<skill-name>/SKILL.md` (personal).
- Write the description as a trigger: what it does and **when to use it**. A vague description means the skill never gets picked, however good the body is.
- Keep `SKILL.md` under 500 lines. Move long reference material into `references/` and tell the body when to open each file.
- Move deterministic work (validation, formatting, API calls) into `scripts/`, so only the output costs tokens.
- Delete skills you don't use. Every skill in the listing adds to your context on every turn, whether or not it's ever used. In Claude Code the whole skill listing gets a budget of 1% of the window.

### Step 4: Instruction files stack up

**The point.** Instruction files above your working folder load at launch. Files below it load on demand.

**Why it matters.** Claude Code has four scopes of CLAUDE.md: managed policy (org-wide), user (`~/.claude/CLAUDE.md`), project (`./CLAUDE.md`) and local (`./CLAUDE.local.md`). Everything in the directory hierarchy above where you started loads at launch, in full, every session. A CLAUDE.md in a subfolder only loads when the agent reads or edits files in that subfolder.

Anthropic's own guidance is to target under 200 lines per CLAUDE.md, because longer files use more context and reduce adherence.

AGENTS.md (used by Codex and many other tools) works the same way. You can nest one in each folder, and the closest AGENTS.md to the file being edited wins. Your chat prompt overrides all of them.

**How to do it.**

- Keep the root file to rules that are true for every task. Anything that starts with "when working on X..." moves into X's folder.
- Use `@path/to/file` imports to keep the root file readable. Note that imports don't save context: an imported file loads together with the file that imports it. Imports go a maximum of four hops deep.
- Put area-specific rules in a CLAUDE.md (or AGENTS.md) inside that area's folder, so they only load when the agent works there.
- Run `/memory` in Claude Code to list your CLAUDE.md and CLAUDE.local.md files across user and project scopes and open any of them to edit.

### Step 5: Keep paths, load just in time

**The point.** Don't preload content. Hold lightweight identifiers (file paths, queries, links) and load the data when the task needs it.

**Why it matters.** This is how Anthropic describes good agents: they keep references and pull data in at runtime with tools, instead of front-loading everything. The window only holds what this task touches.

**How to do it: the INDEX.md route.**

```
CLAUDE.md                  # trunk: routes to the top-level folders
billing/
  INDEX.md                 # routes to invoices, refunds, webhooks
  refunds.md               # leaf: the actual detail
auth/
  INDEX.md
infra/
  INDEX.md
```

- Every folder with subfolders gets an `INDEX.md`: one line on what's there and a routing line per subfolder.
- Write routing lines as conditions: "If the task is about refunds or failed charges, read `billing/refunds.md`."
- Let the agent search instead of reading: `grep` for the symbol, then open the one file that matters.
- For a full walkthrough of this pattern, see the [context tree breakdown](../context-tree/).

### Step 6: Clear and compact before it rots

**The point.** Old tool output goes first. Then summarize and restart.

**Why it matters.** Tool results are the fastest-growing thing in an agent session: test logs, file reads, search results. Anthropic calls tool result clearing one of the safest, lightest-touch forms of compaction. Compaction proper means summarizing a conversation that's nearing the limit and starting again from the summary.

In Claude Code:

- Compaction happens automatically as you approach the limit.
- `/compact` replaces the conversation with a structured summary. You can add a focus: `/compact keep the failing test names and the plan`.
- After compaction, the project-root CLAUDE.md is re-read from disk and re-injected. Nested CLAUDE.md files are not: they were part of the history, so they get summarized away and reload when the agent touches that folder again.
- Up to 5 of the files the agent read or edited are re-read (most recently modified first; a file over 5,000 tokens comes back as a path only), and invoked skills are re-injected (up to 5,000 tokens each, 25,000 total).

**How to do it.**

- Compact at a natural break (task done, plan agreed), not mid-debug.
- Have the agent keep notes outside the window: a `NOTES.md` or progress file it updates as it goes. Notes survive compaction and new sessions. Anthropic calls this structured note-taking.
- Starting something unrelated? `/clear` beats `/compact`.

### Step 7: Give subagents a fresh window

**The point.** Subagents burn the tokens. You get the summary.

**Why it matters.** Each subagent starts with a fresh, isolated context window. It can explore with tens of thousands of tokens and hand back a condensed summary, often 1,000 to 2,000 tokens. The verbose output stays in the subagent's context, and only the relevant summary comes back to your main conversation.

The trade-off is real. In Anthropic's research system, agents used about 4x more tokens than chat and multi-agent systems about 15x. Token usage by itself explained 80% of the performance variance on their BrowseComp evaluation. So spend tokens where the work is, not on every small question.

**How to do it.**

- Use subagents for searches, codebase exploration, log digging and reviews: anything that reads a lot and returns a little.
- In Claude Code, define them as markdown files in `.claude/agents/<name>.md` (this project) or `~/.claude/agents/<name>.md` (every project), or just ask Claude to create one for you. Give each one a narrow job and tell it exactly what to return: "Return the 5 most relevant file paths and one line on why each matters."
- Don't use them for small tasks. A 30-second lookup in the main window is cheaper than a subagent.

---

## 2. The load-order map

This is slide 02 as a table. "Always" means it's in the window on every request, before you type anything.

| Layer | When it loads | When it leaves | How to keep it lean |
|---|---|---|---|
| System prompt | always | never | set by the harness |
| Tool definitions (incl. MCP tools) | always | never | disconnect MCP servers you don't use |
| Root CLAUDE.md / AGENTS.md (and files above your folder) | always, at launch | never; the project-root file is re-read after `/compact` | under 200 lines, only rules true for every task |
| `@imports` inside those files | with the file that imports them | with that file | imports organize, they don't save tokens |
| Skill names + descriptions | always, at startup | never | about 100 tokens each, delete unused skills |
| Conversation history | grows every turn | at `/compact` or `/clear` | compact at task breaks |
| Tool results | grows every turn | when cleared or compacted | use subagents for verbose output |
| Skill body (`SKILL.md`) | when the skill is triggered | stays; re-injected after compaction | under 5k tokens, under 500 lines |
| Skill files (`references/`, `scripts/`) | when accessed | stays until compacted | scripts cost only their output |
| Nested CLAUDE.md (subfolder) | when the agent reads or edits files in that folder | at compaction; reloads on demand | area rules only |
| Files the agent reads | when read | stays until compacted | route with INDEX.md, grep before reading |
| The response | as it's written | becomes history | it counts toward the window too |

---

## 3. Token budget checklist

Every number here comes from the sources in section 5. Run through it on a fresh session with `/context` open.

- [ ] **Know your baseline.** `/context` on a fresh session, before your first message. That's what every request costs before any work.
- [ ] **Skill listing.** About 100 tokens per skill, on every turn. The whole listing is budgeted at 1% of the window, and each entry is capped at 1,536 characters.
- [ ] **Skill bodies.** Under 5k tokens each, only when triggered. Keep `SKILL.md` under 500 lines and move detail into `references/`.
- [ ] **Skill metadata limits.** `name` max 64 characters, `description` max 1,024 characters.
- [ ] **Root CLAUDE.md.** Under 200 lines. Longer files use more context and reduce adherence.
- [ ] **Imports.** Max four hops deep, and they load with the file that imports them, so they don't cut cost.
- [ ] **Auto memory.** If you use it, only the first 200 lines or 25KB of `MEMORY.md` loads at session start.
- [ ] **Caching.** Cache reads are billed at 0.1x the base input price on most models (lower on some). Cached prefixes still fill the window.
- [ ] **After compaction.** Up to 5 recently modified files come back (files over 5,000 tokens as a path only), plus invoked skills at up to 5,000 tokens each and 25,000 total.
- [ ] **Subagents.** Expect 1,000 to 2,000 tokens back per subagent, from tens of thousands spent in its own window.
- [ ] **Multi-agent cost.** About 4x chat tokens for a single agent and about 15x for multi-agent. Use it where the work is big enough.

---

## 4. Starter templates

### A starter CLAUDE.md (about 60 lines)

Copy it to the root of your project and fill in the brackets. It also works as `AGENTS.md`.

```markdown
# [Project name]

[One or two lines: what this project is and who it's for.]

## Hard rules (every task)

- Never commit to main. Create a branch: feat/*, fix/*, chore/*.
- Never push, deploy or delete files without asking first.
- Never put secrets in code, logs or commit messages.
- If you are not sure, say what you checked and ask. Do not guess.

## How to verify work

- Tests: `[npm test]`
- Lint and types: `[npm run lint && npm run typecheck]`
- Before saying a task is done, run the relevant check and report the result.

## How to work

- Read the INDEX.md for the area a task touches before changing anything there.
- Search before reading: grep for the symbol, then open the one file that matters.
- Keep changes small and surgical. Do not refactor code the task did not ask about.
- For searches across many files, use a subagent and ask it for paths plus one
  line each, not file dumps.
- Keep a short progress log in NOTES.md for anything longer than one session.

## Where to go next

- If the task is about [billing, invoices, refunds or payments], read `billing/INDEX.md`.
- If the task is about [login, sessions, users or permissions], read `auth/INDEX.md`.
- If the task is about [deploys, queues, alerts or servers], read `infra/INDEX.md`.
- If the task is about [docs, guides or specs], read `docs/INDEX.md`.

Read only the index for the area the task touches. Do not open the other branches.

## Skills

Skills live in `.claude/skills/`. Use them for repeatable procedures:
- `[release-checklist]`: shipping a release.
- `[key-rotation]`: rotating and revoking API keys.

## Context hygiene

- Do not paste whole logs into the conversation. Read the tail, or grep for the error.
- At a natural break, suggest /compact with a focus line.
- For an unrelated new task, suggest /clear.
```

### A minimal skill

```
.claude/skills/key-rotation/
├── SKILL.md
├── references/
│   └── providers.md
└── scripts/
    └── verify_keys.py
```

`SKILL.md`:

```markdown
---
name: key-rotation
description: Rotate and revoke API keys for staging and production. Use when asked to rotate, renew, revoke or audit API keys or secrets.
---

# Key rotation

1. List keys older than the age limit for the requested environment.
2. Create a new key with the provider, then update the secret store.
3. Run `scripts/verify_keys.py --env <env>` and confirm every service reports OK.
4. Only after verification passes, revoke the old key.

## When to open the extra files

- Provider-specific steps (which console, which CLI flag): read `references/providers.md`.
- Do not read the script. Run it and use its output.

## Rules

- Never print a key value in the conversation or in logs.
- Never revoke an old key before the new one is verified.
```

`references/providers.md`:

```markdown
# Providers

## [Provider A]
- Create: [console path or CLI command]
- Revoke: [console path or CLI command]
- Gotcha: [e.g. new keys take a few minutes to propagate]

## [Provider B]
- Create: ...
- Revoke: ...
```

The description does the routing. The body only loads when a task matches it. The reference only loads when the body says to. The script never loads at all; only its output does.

### Starter prompt: audit your context

```text
Audit my agent's context setup. Do not change anything yet.

1. Run /context (or estimate) and list what is always loaded before my first
   message: system prompt, tools and MCP servers, instruction files, skill
   listing.
2. For each instruction file that loads at launch: its length in lines, and
   which sections apply to every task vs only one area.
3. List every installed skill with its description, and flag any description
   that does not say when to use it.
4. List MCP servers or tools I have not used in this project.

Finish with the 5 changes that would remove the most always-loaded context,
biggest first, and where each piece should move (nested CLAUDE.md, INDEX.md,
skill body, references/, or delete).
```

---

## 5. Every source, linked

Every number on the slides and on this page, with where it comes from.

| Claim | Source |
|---|---|
| Context is a finite resource with an "attention budget"; n² pairwise relationships for n tokens; aim for the smallest set of high-signal tokens; just-in-time loading with lightweight identifiers; compaction, tool result clearing, structured note-taking; subagents return condensed summaries, often 1,000-2,000 tokens, after using tens of thousands | Anthropic, Effective context engineering for AI agents: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents |
| Skill levels: ~100 tokens per skill always, under 5k tokens on trigger, files cost nothing until accessed; name max 64 characters, description max 1,024; script code never loads, only its output | Agent Skills overview: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview |
| Name and description pre-loaded at startup, body when relevant, bundled files as needed | Anthropic, Equipping agents for the real world with Agent Skills: https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills |
| Skill listing budget is 1% of the window, entries capped at 1,536 characters; keep SKILL.md under 500 lines; every listed skill adds context every turn; skills live in `.claude/skills/<name>/SKILL.md` or `~/.claude/skills/<name>/SKILL.md` | Claude Code skills: https://code.claude.com/docs/en/skills |
| `/context`, `/compact [instructions]`, `/clear`, `/memory` | Claude Code commands reference: https://code.claude.com/docs/en/commands |
| CLAUDE.md scopes; above the working directory loads at launch, subdirectories on demand; under 200 lines; imports max four hops and don't reduce context cost; project-root CLAUDE.md re-read after /compact; MEMORY.md first 200 lines or 25KB | Claude Code memory: https://code.claude.com/docs/en/memory |
| Auto-compaction near the limit; /compact replaces the conversation with a structured summary; /context breakdown; up to 5 read or edited files re-read after compaction (over 5,000 tokens: path only); invoked skills re-injected (5,000 each, 25,000 total); nested CLAUDE.md summarized away | Claude Code context window: https://code.claude.com/docs/en/context-window |
| Each subagent starts with a fresh, isolated context window; only the relevant summary returns; subagent files live in `.claude/agents/` or `~/.claude/agents/` | Claude Code subagents: https://code.claude.com/docs/en/sub-agents |
| Accuracy highest at the start or end of the context, significantly worse in the middle | Liu et al., Lost in the Middle: How Language Models Use Long Contexts (TACL): https://arxiv.org/abs/2307.03172 |
| Performance degrades as input length grows (18 models); even a single distractor hurts | Chroma, Context Rot: https://www.trychroma.com/research/context-rot |
| The closest AGENTS.md to the edited file wins; chat prompts override | AGENTS.md: https://agents.md |
| The Messages API is stateless: you always send the full conversation | Working with messages: https://platform.claude.com/docs/en/build-with-claude/working-with-messages |
| Cache reads are 0.1x base input price (some models lower) | Prompt caching: https://platform.claude.com/docs/en/build-with-claude/prompt-caching |
| The context window includes the response; as tokens grow, accuracy and recall degrade (context rot); cached prefixes still occupy the window | Context windows: https://platform.claude.com/docs/en/build-with-claude/context-windows |
| Agents use about 4x the tokens of chat, multi-agent about 15x; token usage explains 80% of the variance on BrowseComp; subagents run in parallel with their own windows | Anthropic, How we built our multi-agent research system: https://www.anthropic.com/engineering/multi-agent-research-system |

Pricing and limits change. These were checked on 2026-11-09.

---

## Want the full lesson?

This is the short version. The full video lessons go deeper: how to set up instruction files, skills and subagents step by step, and how to measure what your agent actually loads.

It's all inside my Skool community, **Agent Architects**: https://www.skool.com/agent-architects
