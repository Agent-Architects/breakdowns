# The subagent test: do you need the history, or just the answer?

You commented SUBAGENT, so here's the full breakdown.

**The short version.** Before your main agent goes off and does a side task, ask one question: do I need the history of how this got done, or just the conclusion and the outputs? If it's just the answer, hand it to a subagent with a fresh context window. It does the reading, you get the summary. If you need some of the history, have the subagent write a handoff doc or its outputs to files, and your main session reads only what it needs.

## The one question

In the lesson I say: "do you really just need the conclusion and the outputs? If the answer is you just want the conclusion and outputs, you can generally delegate that to a subagent or a separate agent session."

Here's why it matters. Every file your main session reads lands in its context window and stays there. If the thing you need is one line buried five folders deep, your main session pays for every file it opened on the way. A subagent pays that bill in its own window and hands back the line.

Claude Code's docs put it the same way: use a subagent "when a side task would flood your main conversation with search results, logs, or file contents you won't reference again: the subagent does that work in its own context and returns only the summary."

## The decision table

| What you need back | Use | Why |
|---|---|---|
| Just the conclusion and the outputs | A fresh subagent | It starts with a clean window, explores, returns a summary |
| The conclusion plus some detail you'll want later | A subagent that writes a handoff doc or output files | The summary stays small, the detail lives on disk |
| The subagent needs everything you've discussed so far | A fork (`/subtask` in Claude Code) | A fork inherits the whole conversation and shares the parent's prompt cache |
| Lots of back-and-forth, or phases that share context (plan, build, test) | Stay in the main conversation | Handing off would lose the shared context |
| A quick, targeted change, or latency matters | Stay in the main conversation | A fresh subagent has to gather context first |
| A question about something already in the conversation | `/btw` | No tools, and the answer isn't added to history |
| A reusable procedure you want run in the main context | A skill | Skills run in the main conversation, not an isolated window |

The rows below the first three all come straight from the "Choose between subagents and main conversation" section of the subagents docs.

## How Claude Code subagents work

What the docs confirm:

- **Fresh window.** "Each subagent starts with a fresh, isolated context window. It doesn't see your conversation history, the skills you've already invoked, or the files Claude has already read." Claude writes a delegation message summarizing the task, and the subagent works from that.
- **Only the summary comes back.** The verbose output "stays in the subagent's context while only the relevant summary returns to your main conversation." Anthropic's context engineering post puts numbers on it: a subagent might use "tens of thousands of tokens or more" exploring and return a summary of "often 1,000-2,000 tokens."
- **It still loads your CLAUDE.md files** (user, project, local, managed), plus a git status snapshot. The built-in Explore and Plan agents skip both. If a rule must reach the subagent, restate it in the delegation.
- **Where they live.** Markdown files with YAML frontmatter in `.claude/agents/` (this project) or `~/.claude/agents/` (all your projects). You can also just ask Claude to write one for you.
- **Frontmatter.** Only `name` and `description` are required. `tools` is an allowlist, `disallowedTools` a denylist, `model` takes `sonnet`, `opus`, `haiku`, `fable`, a full model ID, or `inherit`. There are more (`maxTurns`, `effort`, `memory`, `isolation`, `skills` and others), but those four are what you need to start.
- **The description is the trigger.** Claude reads it to decide when to delegate. Add "use proactively" if you want it to delegate without being asked.
- **It costs real usage.** A subagent "sends its own requests, which count toward the same usage limits as your main conversation."

### The built-in Explore agent

Claude Code ships a built-in **Explore** subagent: "A fast, read-only agent optimized for searching and analyzing codebases." Write and Edit are denied. It starts without your CLAUDE.md files and git status "to keep research fast and inexpensive."

When Claude calls it, it picks a thoroughness level: **quick**, **medium**, or **very thorough**. So for a lot of "go find the one line" jobs, you don't need to write anything. Just say "use Explore to find where the retry limit is set and give me the file and line."

If you want Explore on a cheaper model, the docs say a user or project subagent named `Explore` overrides the built-in and keeps its own `model` field.

## Read-only helpers are the best place to start

In the lesson I call read-only helpers "some of the most useful" subagents. A helper that only reads files and summarizes them is low risk and saves the most context, because reading is exactly the work that floods a window.

One gotcha from the docs: if you give a subagent `Bash`, it "can still change files through Bash." So a read-only helper should get `Read`, `Grep`, `Glob`, and web tools, and nothing that can run commands or write. Leaving `Agent` out of `tools` also stops it spawning subagents of its own.

### Copy-paste: a read-only researcher

Save as `.claude/agents/researcher.md` (or `~/.claude/agents/researcher.md` for every project):

```markdown
---
name: researcher
description: Read-only researcher. Use proactively when a task needs many files or web pages read to find a few facts. Returns findings with paths or URLs, never file dumps.
tools: Read, Grep, Glob, WebFetch, WebSearch
model: sonnet
---

You are a read-only researcher. You never edit, write, or run commands.

How to work:
1. Restate the question in one line before you start.
2. Search before reading: Grep and Glob to find candidates, then Read only
   the parts that matter.
3. For the web, prefer official docs and primary sources. Note the URL of
   everything you rely on.
4. Stop as soon as you can answer. Do not read "just in case".

What to return (keep it under about 300 words):
- Answer: 1 to 3 sentences.
- Evidence: each fact with its file path and line, or its URL.
- Not found: anything you looked for and could not confirm.
- Next: the one file or page the main agent should open, if any.

Never paste whole files or pages into your answer.
```

Swap `model: sonnet` for `model: haiku` if the job is simple lookups and you want it cheaper. The docs list routing tasks to lower-cost models like Haiku as one of the reasons subagents exist.

## When you do need some of the history: write it down

In the lesson I say: "you can have that sub-agent or agent session just store a handoff document or store its output documents in files and folders."

Anthropic's multi-agent research post describes the same move. Instead of pushing everything back through the lead agent, "subagents call tools to store their work in external systems, then pass lightweight references back to the coordinator." They say this cuts the "game of telephone" and "reduces token overhead from copying large outputs through conversation history."

How I'd do it:

1. Pick a folder per task, like `notes/<task>/`.
2. Tell the subagent to write its full findings there (`findings.md`, raw data, drafts) and return only a short summary plus the file paths.
3. Your main session reads the summary. It opens a file only when it needs the detail.
4. For long jobs, have it keep a `handoff.md`: what's done, what's left, decisions made, open questions. A fresh session can pick up from that.

This needs a subagent that can write, so it's a different agent from the read-only one above. Add `Write` to its `tools` and say in the prompt which folder it may write to. The `tools` field picks tools, it doesn't fence off folders, so the folder rule is an instruction, not a lock.

## Copy-paste: a prompt for your main agent

Put this in your CLAUDE.md, or paste it at the start of a session:

```text
Before any side task, ask yourself: do I need the history of how this gets
done, or only the conclusion and the outputs?

- Only the conclusion: delegate to a subagent (researcher or Explore). Give it
  an objective, the output format you want back, which tools and sources to
  use, and what is out of scope. Ask for paths or URLs plus one line each,
  never file dumps.
- Conclusion plus detail for later: have the subagent write its full findings
  to notes/<task>/ and return a short summary with the file paths.
- The task needs our whole conversation: use a fork instead of a fresh
  subagent.
- A quick lookup you can do in a few tool calls, or anything with lots of
  back-and-forth: do it yourself in this session.

Subagents do not see this conversation. Restate any rule they must follow.
```

The four parts of that delegation (objective, output format, tools and sources, boundaries) come from Anthropic's research post: "Each subagent needs an objective, an output format, guidance on the tools and sources to use, and clear task boundaries."

## When not to use a subagent

Every subagent spends its own tokens, so don't spawn one for everything.

- **Small lookups.** If it's one grep and one read, do it in the main session. A fresh subagent "starts fresh and may need time to gather context."
- **Token cost.** In Anthropic's data, agents use about 4x more tokens than chat, and multi-agent systems about 15x. They say multi-agent setups need tasks where the value is high enough to pay for that.
- **Scale it to the job.** Their own rule of thumb: simple fact-finding needs 1 agent with 3 to 10 tool calls, direct comparisons 2 to 4 subagents, complex research more than 10. Over-spawning on simple queries was a common early failure for them.
- **Tightly coupled work.** Anthropic notes tasks where every agent needs the same context, or with lots of dependencies, aren't a good fit, and that most coding tasks are less parallelizable than research.
- **Too many detailed reports.** The docs warn that many subagents each returning detailed results "can consume significant context" in your main conversation.

## What goes wrong

- **Vague delegation.** "Research X" gets you duplicated or misread work. Anthropic saw subagents run the exact same searches because the brief was too short.
- **Assuming it knows what you know.** It doesn't see your conversation. Restate the constraint.
- **Giving a "read-only" agent Bash.** It can still change files through Bash. Use `Read, Grep, Glob`.
- **Asking for everything back.** If it returns whole files, you've lost the point. Ask for paths, lines, and a short answer.
- **Expecting to resume Explore.** The docs say Explore and Plan "can finish without giving Claude an ID to resume them with." For work you'll continue, use `general-purpose` or your own subagent.
- **Long descriptions.** Subagent descriptions sit in context. Claude Code warns at startup when your custom ones pass 15,000 tokens combined. Keep them to a line or two.

## Sources

| Claim | Source |
|---|---|
| Use a subagent when a side task would flood the main conversation; it returns only the summary; own context window; requests count toward the same usage limits; route to lower-cost models like Haiku; descriptions over 15,000 tokens warn at startup | Claude Code subagents: https://code.claude.com/docs/en/sub-agents |
| Built-in Explore: fast, read-only, Write and Edit denied, skips CLAUDE.md and git status, quick / medium / very thorough; a custom `Explore` overrides it | Claude Code subagents, Built-in subagents: https://code.claude.com/docs/en/sub-agents |
| `.claude/agents/` and `~/.claude/agents/`; only `name` and `description` required; `tools`, `disallowedTools`, `model` values; "use proactively" | Claude Code subagents, Configure subagents and Frontmatter reference: https://code.claude.com/docs/en/sub-agents |
| `tools: Read, Grep, Glob, Bash` can still change files through Bash; omit `Agent` to stop a subagent spawning | Claude Code subagents, Control subagent capabilities: https://code.claude.com/docs/en/sub-agents |
| Fresh, isolated window that doesn't see history; CLAUDE.md and git status load (Explore and Plan skip them); restate rules in the delegation | Claude Code subagents, What loads at startup: https://code.claude.com/docs/en/sub-agents |
| Main conversation vs subagents criteria; `/btw`; skills run in the main context; many detailed results consume context | Claude Code subagents, Choose between subagents and main conversation and Common patterns: https://code.claude.com/docs/en/sub-agents |
| Forks inherit the whole conversation, `/subtask`, shared prompt cache | Claude Code subagents, Fork the current conversation: https://code.claude.com/docs/en/sub-agents |
| Explore and Plan can finish without a resumable ID | Claude Code subagents, Resume subagents: https://code.claude.com/docs/en/sub-agents |
| Agents use about 4x the tokens of chat, multi-agent about 15x; tasks need enough value; coupled tasks and most coding are a weaker fit; effort scaling rules; each subagent needs an objective, output format, tools and sources, task boundaries; artifact systems with lightweight references; handoffs to fresh subagents | Anthropic, How we built our multi-agent research system: https://www.anthropic.com/engineering/multi-agent-research-system |
| Subagents explore with tens of thousands of tokens and return a condensed summary, often 1,000 to 2,000 tokens; structured note-taking outside the window | Anthropic, Effective context engineering for AI agents: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents |

Product details checked on 2026-11-24.

## Want more like this?

More agent breakdowns and the full lessons are inside my Skool community, **Agent Architects**: https://www.skool.com/agent-architects
