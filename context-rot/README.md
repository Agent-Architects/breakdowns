# Context rot: how one stale fact spreads, and the state file that stops it

You commented ROT, so here's the full breakdown.

**The short version.** One wrong or out-of-date fact in your agent's context acts like mold: every decision built on top of it inherits the error. It gets much worse when that fact is saved into a file the agent reloads every session, like `CLAUDE.md`, because then it comes back fresh every time. The fix is a dated state file: a `STATE.md` where every fact says when it was true and when it was last checked, plus a checklist of the work, so the agent can tell old from current and you can `/compact` or `/clear` without losing anything.

## What context rot actually is

The term has two flavors, and they stack.

**Flavor 1: too much context.** Anthropic's docs define it plainly: as token count grows, accuracy and recall degrade, "a phenomenon known as *context rot*" ([context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)). Chroma tested 18 models and found "model performance consistently degrades with increasing input length", and that "even a single distractor reduces performance" ([Chroma, Context Rot](https://www.trychroma.com/research/context-rot)).

**Flavor 2: wrong context.** This is the one the short is about. In the lesson I say "a bad, out-of-date fact" is "like mold in your agent's context window, infecting all of its future decisions."

Why they stack: a stale fact is the worst kind of distractor. It's on topic, it sounds right, and it's phrased with confidence. A long session gives it more places to hide.

## How one stale fact spreads

Say your agent learns on Monday that the API runs on port 3000. On Wednesday you move it to 8080. Here's where the old fact can live, and how long it survives:

| Where the fact lives | How it gets there | How long it survives |
|---|---|---|
| The conversation | The agent read it once, early | Until `/clear`. `/compact` may keep it in the summary |
| Tool results | An old log or config dump the agent printed | Until compaction summarizes it away |
| A notes file the agent wrote | "Remember: API is on 3000" | Until someone edits the file |
| Auto memory (`MEMORY.md`) | Claude saved it as a learning | Every session, and re-injected after compaction |
| Root `CLAUDE.md` | You or the agent wrote it in | Every session, and re-read from disk after `/compact` |

The bottom two rows are the dangerous ones. Claude Code reads `CLAUDE.md` "at the start of every session" ([memory](https://code.claude.com/docs/en/memory)). After compaction, the project-root `CLAUDE.md` and auto memory are both re-injected from disk ([what survives compaction](https://code.claude.com/docs/en/context-window#what-survives-compaction)). That's great for true rules. For a false one, it means no amount of compacting or clearing will get rid of it. You have to fix the file.

That's what the lesson means by "even worse if you're saving that incorrect or stale fact in external files." One bad line, re-loaded into every session, for every task, until a human notices.

## The study: agents follow the stale file over the code

In the lesson I say studies have shown agents follow incorrect instruction files over the real code. Here's the one I'd point you to.

Xu and Wu, *Stale Instruction Files Override the Code in Coding Agents: A One-Sentence Fix* (arXiv, October 2026). They built 40 Python projects where the instruction file asks for one convention and the code uses another (for example `print` instead of logging), then had Claude Code and Codex CLI add a feature to each, across 320 runs ([paper](https://arxiv.org/abs/2610.30571)).

What they found:

- **90.1% of the agents' choices followed the stale file** (649 of 720). Only 4.2% followed the existing code.
- **Noticing didn't help.** Claude Code "pointed out the conflict in 79 of 80 runs and still followed the file."
- **Sometimes the agent rewrote working code to match the file.** Codex CLI did it in 20 of 80 runs, and the project's own tests then failed in 17 of them.
- **It happens in real repos too.** After Supabase moved its dashboard to React 19, a skill file kept telling agents for 13 days that it used React 18. In the Codex CLI repo, an `AGENTS.md` told agents for 24 days to update a document that had already been deleted.

Why it happens, in the authors' words: "the instruction file reaches the model as an instruction and the code as tool output, which models are trained to rank lower." That ranking exists for a good reason (it protects against prompt injection), but it means a stale instruction outranks the live code.

They also tested a fix. One sentence in the user-level instruction file (`~/.claude/CLAUDE.md`) raised code-following choices from 4.2% to 91.4%, stopped the rewrites, and got tests passing in every run. The sentence, exactly as in the paper:

```text
When a repository's documentation and its existing code disagree, follow the conventions used in the existing code, and in your final reply point out each inconsistency you found between the documentation and the code.
```

## The remedy: a dated state file

The idea from the lesson: keep a file in your workspace "that store[s] the current state of something that's labeled and dated. With what happened and when it happened." If the agent reads a fact stamped three weeks ago, it at least gets a clue that it should check before trusting it.

Three rules make it work:

1. **Every fact has a date.** Not "the API is on 8080" but "2026-11-24: API moved to 8080."
2. **The file says when it was last verified, and by what.** A date plus the command or file you checked.
3. **Status lives here, not in `CLAUDE.md`.** `CLAUDE.md` is for rules that stay true ("run tests before committing"). Anything that changes week to week (ports, versions, what's done, what's broken) goes in `STATE.md`.

It doubles as a work tracker. In the lesson I say: take things off a list as you complete them, so the agent tracks the work "in an external file rather than in its context window." Anthropic calls this structured note-taking: the agent writes notes "persisted to memory outside of the context window," and they "get pulled back into the context window at later times" ([effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)). In their long-running agent harness, every session ends with "a git commit and progress update," and the next session starts by reading the progress file and git log ([effective harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)).

### Copy-paste STATE.md template

Put this at the root of your project. Fill in the brackets.

```markdown
# STATE.md

Last verified: [2026-11-24 14:30] by [agent | me], checked against [git log, package.json, running the app]
Rule: any fact older than 7 days is a hint, not a fact. Re-check it before you act on it.

## Current state (one line per fact, newest date wins)

| Fact | Value | Since | Last verified | How to check |
|---|---|---|---|---|
| [API port] | [8080] | [2026-11-24] | [2026-11-24] | [grep PORT .env.example] |
| [Node version] | [22] | [2026-11-10] | [2026-11-24] | [node -v] |
| [Deploy target] | [staging only, prod frozen] | [2026-11-20] | [2026-11-22] | [ask me] |

## Work tracker

Goal: [one line: what "done" means for this piece of work]

- [x] [2026-11-23] [Add rate limiter to /login] (commit [abc1234])
- [ ] [In progress since 2026-11-24] [Move API to port 8080, update docker-compose]
- [ ] [Not started] [Update the README port examples]
- [ ] [Blocked since 2026-11-22] [Prod deploy: waiting on me to rotate the key]

## Decisions (do not re-open without asking)

- [2026-11-20] [Use integer cents for money, never floats.] Why: [rounding bugs in refunds]

## Log (newest first, never edit old lines, add a new one)

- [2026-11-24 14:30] [Moved API from 3000 to 8080. Old port is dead.]
- [2026-11-23 18:05] [Rate limiter shipped. Tests green.]

## Known stale

- [README still says port 3000. Fix pending, see tracker.]
```

Why each part is there:

- **Last verified** is the clue the lesson talks about. Old date, low trust.
- **Since** and **Last verified** are different on purpose. A fact can be old and still true. The second date says someone checked.
- **How to check** turns a stale fact into a 5-second command instead of a guess.
- **Log is append-only.** Old lines stay, with their dates, so nothing gets silently rewritten into a new "truth."
- **Known stale** gives the agent somewhere to put a problem it found but didn't fix.

If the tracker gets long, Anthropic's harness post has a useful detail: they kept their feature list as JSON because "the model is less likely to inappropriately change or overwrite JSON files compared to Markdown files" ([effective harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)).

## Tell the agent to read it and keep it current

Add this to your project `CLAUDE.md`. It's a rule that stays true, so it belongs there, and because the root `CLAUDE.md` is re-read after `/compact`, the instruction survives compaction too.

```markdown
## State

- STATE.md is the source of truth for current status, versions, ports and open work.
  This file (CLAUDE.md) holds rules only. Do not put changing facts here.
- At the start of every task, read STATE.md. If "Last verified" is older than 7 days,
  re-check the facts you need with their "How to check" command before using them.
- If STATE.md, this file or any doc disagrees with the code, trust the code, then
  update STATE.md and tell me what was wrong.
- When you finish or start a tracker item, update it with today's date.
- Before suggesting /compact or /clear, update STATE.md first.
```

And this prompt, to set it up the first time:

```text
Set up a STATE.md for this project. Do not change any code.

1. Read CLAUDE.md, any AGENTS.md, and the README. List every line that states a
   fact that can change (ports, versions, file paths, what's done, what's broken).
2. Check each fact against the real code or by running a command. Mark each one
   TRUE, STALE or UNCHECKABLE, and show me the evidence.
3. Create STATE.md from the template I pasted, with today's date on every row
   and a "How to check" command for each fact.
4. Propose edits that move changing facts out of CLAUDE.md into STATE.md. Show me
   the diff and wait for my OK before you edit CLAUDE.md.
5. Add what we're working on right now to the tracker, with dates.
```

Claude Code also has a built-in check for the instruction files themselves: `/doctor prompt-audit` looks for "references to files or commands that don't exist, and files that contradict each other," and nothing changes until you ask it to apply the edits ([memory](https://code.claude.com/docs/en/memory)). Run it when you set this up and every so often after.

### Optional: re-inject STATE.md after compact or clear

A `SessionStart` hook's plain-text output gets added to Claude's context, and its matcher can target `compact` or `clear`, so the state file lands in the window after every compaction and every `/clear` without the agent having to remember ([hooks](https://code.claude.com/docs/en/hooks), [hooks guide](https://code.claude.com/docs/en/hooks-guide)). Put this in `.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "compact|clear",
        "hooks": [
          { "type": "command", "command": "cat \"${CLAUDE_PROJECT_DIR}/STATE.md\"" }
        ]
      }
    ]
  }
}
```

## Compact or clear without fear

This is the real payoff. In the lesson I say the state file "allows you to compact or clear your context windows without fear for losing information." Here's what each command does ([commands](https://code.claude.com/docs/en/commands), [context window](https://code.claude.com/docs/en/context-window)):

| Command | What happens | What you lose without a state file |
|---|---|---|
| `/compact [instructions]` | Replaces the conversation with a structured summary. Root `CLAUDE.md` and auto memory come back from disk, plus up to 5 recently modified files | Whatever the summary didn't keep: the exact open items, small decisions, why you chose X |
| `/clear` | Starts a new conversation with empty context | Everything that was only in the chat |

Anthropic warns that "overly aggressive compaction can result in the loss of subtle but critical context" ([effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)). With the state written to a file, that loss doesn't matter. The summary can be lossy because the file isn't.

The routine:

1. Ask the agent: "Update STATE.md with where we are, then stop."
2. Read the diff. Make sure the tracker and the log say what you think they say.
3. `/clear` if the next task is unrelated, or `/compact keep the open tracker items` if it isn't.
4. First message after: "Read STATE.md and tell me the next unchecked item."

That's also how you stay out of what I call the dumb zone in the lesson: long sessions where the window is full of old tool output and the agent starts missing things. Write it down, clear, carry on.

## What goes wrong

- **Undated facts.** "API is on 3000" with no date looks exactly as current as the truth. Date every line.
- **Changing facts in `CLAUDE.md`.** It reloads every session and survives compaction, so a stale line there is the hardest kind to kill. Rules in `CLAUDE.md`, status in `STATE.md`.
- **The agent notices and obeys anyway.** That's the 79 of 80 result above. Add the one-sentence fix so noticing turns into trusting the code.
- **The state file becomes the new stale file.** If nobody updates it, it's just more mold. Make "update STATE.md" part of finishing every task, and keep the "Last verified" line honest.
- **Rewriting history.** If the agent edits old log lines, you lose the "when." Append only.
- **Saving a wrong fact to auto memory.** Run `/memory`, open the auto memory folder, and delete or fix it. It's plain markdown ([memory](https://code.claude.com/docs/en/memory)).

## Sources

| Claim | Source |
|---|---|
| As token count grows, accuracy and recall degrade, known as context rot | Anthropic, Context windows: https://platform.claude.com/docs/en/build-with-claude/context-windows |
| 18 models tested; performance consistently degrades with input length; even a single distractor reduces performance | Chroma, Context Rot: https://www.trychroma.com/research/context-rot |
| Stale instruction files: 40 projects, 320 runs, 90.1% (649 of 720) of choices followed the stale file; Claude Code flagged the conflict in 79 of 80 runs and still followed it; Codex CLI rewrote code in 20 of 80 runs, tests failed in 17; instruction vs tool output ranking; Supabase 13 days and Codex 24 days examples; the one-sentence fix raised code-following from 4.2% to 91.4% | Xu and Wu, Stale Instruction Files Override the Code in Coding Agents: A One-Sentence Fix: https://arxiv.org/abs/2610.30571 |
| CLAUDE.md is read at the start of every session; auto memory loads the first 200 lines or 25KB of MEMORY.md; review files periodically to remove outdated or conflicting instructions; `/doctor prompt-audit`; `/memory`; project-root CLAUDE.md survives `/compact` | Claude Code memory: https://code.claude.com/docs/en/memory |
| What survives compaction: root CLAUDE.md and auto memory re-injected from disk, up to five recently modified files re-read; `/compact` with a focus; `/clear` between tasks | Claude Code context window: https://code.claude.com/docs/en/context-window |
| `/compact [instructions]` summarizes the conversation; `/clear` starts a new conversation with empty context | Claude Code commands: https://code.claude.com/docs/en/commands |
| SessionStart matchers include `clear` and `compact`; plain-text stdout is added to context; `${CLAUDE_PROJECT_DIR}` is the project root; `\|` separates matcher alternatives | Claude Code hooks reference: https://code.claude.com/docs/en/hooks |
| Use a SessionStart hook with a `compact` matcher to re-inject critical context | Claude Code hooks guide: https://code.claude.com/docs/en/hooks-guide |
| Structured note-taking outside the context window; to-do lists and NOTES.md; aggressive compaction can lose subtle but critical context | Anthropic, Effective context engineering for AI agents: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents |
| Progress file plus git history between sessions; each session ends with a commit and progress update; feature list kept as JSON because models are less likely to overwrite it than Markdown | Anthropic, Effective harnesses for long-running agents: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents |

Checked on 2026-11-24.

## Want more like this?

More agent breakdowns and the full lessons are inside my Skool community, **Agent Architects**: https://www.skool.com/agent-architects
