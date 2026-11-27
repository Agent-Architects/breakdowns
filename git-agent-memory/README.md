# Git is your agent's memory

You commented MEMORY, so here's the full breakdown.

**The short version.** Your agent's files and folders are its memory, but a file only holds what's true now. It doesn't say when something changed or why. Git adds that. Every commit is a snapshot with a date, an author and a message, so your agent can read the history and see how the project got to where it is. Commit small and often (frequent atomic commits), write messages that say why, and when you come back to a project weeks later, ask your agent to read `git log` before it touches anything. Commands below are from the official Git docs ([git-log](https://git-scm.com/docs/git-log), [git-commit](https://git-scm.com/docs/git-commit)), checked on Nov 27, 2026.

## Why files alone aren't enough

Files and folders work as your agent's personality and memory: instructions, notes, skills, code. But a file has no built-in timeline. When your agent reads `notes.md` it sees the latest version, with no idea what it said last week, which line is new, or which fact is stale.

Git fills that gap. Every commit records ([git-commit](https://git-scm.com/docs/git-commit), [git-log](https://git-scm.com/docs/git-log)):

| A commit has | What your agent gets from it |
|---|---|
| A date | When each change happened, so it can sort old facts from new ones |
| A message | Why the change was made, in your words or your agent's |
| The exact diff | What changed, line by line, before and after |
| An author | Who made it: you, a teammate or an agent |

That's time-based memory. Your agent can look back through the history and almost see back in time to the project you're working on.

## The mantra: frequent atomic commits

**Atomic** means one small, self-contained change per commit. **Frequent** means you commit every time you finish one, not once at the end of the day.

Why it matters for memory:

- **Each snapshot means one thing.** Your agent can compare what the project looked like right before a change with right after it.
- **The log reads like a diary.** Ten small commits with clear messages tell a story. One giant "updates" commit tells nothing.
- **You can undo one thing** without undoing everything else ([git-revert](https://git-scm.com/docs/git-revert)).

A good commit message says *why*, not just *what*:

```text
fix: retry the upload when Drive returns 429

The nightly export failed twice this week on rate limits.
```

Not this:

```text
updates
```

## Ask your agent to read the history

This is the payoff. You open a project you haven't touched in weeks and, before anything else:

```text
Before you change anything, read the git history of this repo for the last 3 weeks
(git log --since="3 weeks ago" --stat). Tell me in 5 bullets what changed, what was
being worked on last, and anything that looks half-finished. Then check git status for
uncommitted work.
```

More prompts that work:

```text
Find when we changed how <feature> works and why. Use git log -S "<a function or phrase>"
and show me the commit messages and the diff.
```

```text
This line in <file> looks wrong. Run git blame on it, find the commit that added it,
and tell me what that commit was trying to do before you change it.
```

```text
Compare this skill with how it looked a month ago (git log -p --since="1 month ago" -- <path>).
What did we add, what did we remove, and did any of it make things worse?
```

## Commands your agent will use

| You want | Run |
|---|---|
| Recent history, one line per commit | `git log --oneline -20` |
| Everything since a date | `git log --since="2 weeks ago"` |
| Which files each commit touched | `git log --stat` |
| The full diff of each commit | `git log -p` |
| History of one file or folder | `git log -p -- path/to/file` |
| Follow a file across renames | `git log --follow -- path/to/file` |
| Commits that added or removed a string | `git log -S "some text"` |
| Commits whose message mentions a word | `git log --grep="upload"` |
| Commits by one author (say, your agent) | `git log --author="name"` |
| One commit in full | `git show <commit>` |
| Who last changed each line, and when | `git blame path/to/file` |
| What's changed but not committed yet | `git status` and `git diff` |

Sources: [git-log](https://git-scm.com/docs/git-log), [git-show](https://git-scm.com/docs/git-show), [git-blame](https://git-scm.com/docs/git-blame), [git-status](https://git-scm.com/docs/git-status), [git-diff](https://git-scm.com/docs/git-diff). `git log` lists newest first by default.

## Rules to give your agent

Paste this into your agent's instruction file (`CLAUDE.md`, `AGENTS.md` or similar):

```markdown
## Git as memory
- At the start of a session in a repo, read `git log --oneline -20` and `git status` before changing anything.
- Commit after each small, self-contained change. One change, one commit.
- Commit messages: a short summary line, then one line on why. Never "updates" or "wip".
- Before changing code you didn't write, check `git log -p -- <file>` or `git blame` for why it is the way it is.
- Never commit secrets (.env, keys, tokens). Git history keeps them even after you delete the file.
```

## Catches

- **Uncommitted work isn't in the history.** If you or your agent never commit, there's nothing to read. That's why "frequent" matters.
- **Bad messages make bad memory.** The diff shows *what* changed. Only the message says *why*.
- **History keeps everything.** A key you commit and then delete is still in the history. Keep secrets out from the start ([GitHub on removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)).
- **Git is for text.** Notes, skills, instructions and code are perfect. Videos, big files and large data belong somewhere else.
- **A long history costs tokens.** Ask for `--oneline`, a date range or one path instead of the whole `git log -p`.

## Related breakdowns

- [GitHub is your agent database](../github-agent-database/): put your skills and notes in one private repo, version them and share them with your team.
- [Run 10 agents on one project: git worktrees](../git-worktrees/): give each agent its own working folder on its own branch.

## My take

Your agent already has files for memory. Git gives that memory a timeline. Commit small, write messages that say why, and make "read the git log" the first thing your agent does when you come back to a project. It's the cheapest long-term memory you'll ever set up.

## Sources

- [git-log](https://git-scm.com/docs/git-log), Git documentation
- [git-commit](https://git-scm.com/docs/git-commit), Git documentation
- [git-show](https://git-scm.com/docs/git-show), Git documentation
- [git-blame](https://git-scm.com/docs/git-blame), Git documentation
- [git-status](https://git-scm.com/docs/git-status) and [git-diff](https://git-scm.com/docs/git-diff), Git documentation
- [git-revert](https://git-scm.com/docs/git-revert), Git documentation
- [Removing sensitive data from a repository](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository), GitHub Docs
