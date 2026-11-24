# GitHub is your agent database: version and share your skills

You commented SKILLS, so here's the full breakdown.

**The short version.** Your agent's skills, rules and notes are just text files. Put them in one private GitHub repo and you get three things for free: a dated history of every change, a diff you can read before you trust a new version, and one source your whole team pulls from. In Claude Code a skill is a folder with a `SKILL.md` file, and the docs say to commit project skills "so your team gets it too" ([skills](https://code.claude.com/docs/en/skills)). A repo can also be a plugin marketplace that teammates add with one command ([create a marketplace](https://code.claude.com/docs/en/plugin-marketplaces)). Keep secrets and big media out. Everything below was checked against the official docs on Nov 24, 2026.

## Why a repo

In the lesson I put it like this: files and folders are your agent's personality and memory, but a file has no built-in date for what it says. Git adds that. Your agent can read the history, see when each change was made, and "almost see back in time" to how the project got here.

For text that isn't too big, you can treat GitHub like a database of knowledge. You host and version your skills there, track the changes that make them better, and share them with teammates so everyone works from the same data. For video files, big files or large amounts of data, use something other than GitHub.

There's also a practical reason. Claude Code cloud sessions don't read your personal skills folder, `~/.claude/skills/`. The docs say to commit the skill to the repository's `.claude/skills/` instead, or turn it on in your claude.ai account ([skills](https://code.claude.com/docs/en/skills)).

## What goes in

| Put this in | What it is | Where Claude Code reads it |
|---|---|---|
| Skills | A folder with a `SKILL.md`, plus optional reference files and scripts | `.claude/skills/<name>/SKILL.md` in a project, `~/.claude/skills/<name>/SKILL.md` for you, or `skills/<name>/SKILL.md` inside a plugin ([skills](https://code.claude.com/docs/en/skills)) |
| Rules and instruction files | `CLAUDE.md`, `AGENTS.md`, and topic files like `testing.md` | `./CLAUDE.md` or `./.claude/CLAUDE.md`, and `.claude/rules/*.md` ([memory](https://code.claude.com/docs/en/memory)) |
| Knowledge base | Plain Markdown notes your skills point to | Wherever a skill or `CLAUDE.md` links to it |
| Workflows | Step-by-step procedures you repeat | Best written as skills, so they load only when used |

A few facts that shape the layout:

- **Only the description loads up front.** "Skill descriptions are loaded into context so Claude knows what's available, but full skill content only loads when invoked" ([skills](https://code.claude.com/docs/en/skills)). So a big library of skills is cheap until one is used.
- **Keep `SKILL.md` short.** The docs say to keep it under 500 lines and move detailed reference material into separate files that `SKILL.md` links to ([skills](https://code.claude.com/docs/en/skills)).
- **Put the use case first in the description.** `description` plus `when_to_use` is cut at 1,536 characters ([skills](https://code.claude.com/docs/en/skills)).
- **Keep each `CLAUDE.md` short too.** The target is under 200 lines per file. Rules that matter for only part of a codebase can go in path-scoped rules that load only for matching files ([memory](https://code.claude.com/docs/en/memory)).
- **`AGENTS.md` works.** Claude Code can read `AGENTS.md` as your project instructions when there's no `CLAUDE.md` in the folder or above it (v2.1.277 or later) ([memory](https://code.claude.com/docs/en/memory)).

For how to route an agent through a knowledge base without loading all of it, see [Teach your agent to climb the context tree](../context-tree/).

## A suggested repo layout

One private repo, skills-first. The skills sit inside a plugin so the same repo also works as a plugin marketplace. Rules and knowledge sit next to it as plain Markdown.

```text
agent-context/
  README.md                       what's in here and how to install it
  .gitignore                      secrets, local files, media
  .claude-plugin/
    marketplace.json              the catalog teammates add
  plugins/
    team-skills/
      .claude-plugin/
        plugin.json               the plugin's name
      skills/
        release-notes/
          SKILL.md
          reference.md
        weekly-report/
          SKILL.md
          scripts/
            collect.sh
  rules/
    writing-style.md
    security.md
  knowledge/
    INDEX.md
    product.md
    customers.md
```

The plugin parts follow the docs: `marketplace.json` lives in `.claude-plugin/` at the repo root, each plugin has its own `.claude-plugin/plugin.json`, and skills go in `skills/` at the plugin root, never inside `.claude-plugin/` ([create a plugin](https://code.claude.com/docs/en/plugins/create), [create a marketplace](https://code.claude.com/docs/en/plugin-marketplaces)). The plugin docs list skills, agents, hooks and MCP servers as plugin components. Rules files aren't on that list, so bring `rules/` and `knowledge/` in with a clone, as below.

## How agents and teammates pull it in

| Way | Best for | How |
|---|---|---|
| Commit skills into the project | One project's own skills | Put them in that repo's `.claude/skills/`. Anyone who clones the project gets them ([skills](https://code.claude.com/docs/en/skills)) |
| Plugin marketplace | Sharing skills with a team, with updates | Teammates add the repo once and install by name ([host a marketplace](https://code.claude.com/docs/en/plugins/host-marketplace)) |
| Clone plus symlinks | Your own machine, or rules files | Clone the repo, then link folders into `~/.claude/skills/` or `.claude/rules/` |
| Git submodule | Pinning one version of the context repo inside a project | `git submodule add` records the context repo in the project ([git-submodule](https://git-scm.com/docs/git-submodule)) |

**Plugin marketplace.** Teammates run this in a Claude Code session:

```text
/plugin marketplace add your-org/agent-context
/plugin install team-skills@agent-context
```

The install id is the plugin's `name`, an `@`, and the marketplace `name` ([create a marketplace](https://code.claude.com/docs/en/plugin-marketplaces)). Plugin skills are namespaced, so `release-notes` runs as `/team-skills:release-notes` ([create a plugin](https://code.claude.com/docs/en/plugins/create)). Run `claude plugin validate .` before you push a change.

- **Private repos work.** Claude Code uses the git credentials already on each person's machine. It has no token of its own. On GitHub, `gh auth login` followed by `gh auth setup-git` stores one ([host a marketplace](https://code.claude.com/docs/en/plugins/host-marketplace)).
- **One repo, everyone.** Run `claude plugin marketplace add your-org/agent-context --scope project` once inside a project and commit the `.claude/settings.json` it writes. Each teammate who trusts the folder gets the marketplace registered ([host a marketplace](https://code.claude.com/docs/en/plugins/host-marketplace)).
- **Updates.** Auto-update is off until a user turns it on under **Marketplaces** in `/plugin`. Without it, people run `/plugin marketplace update agent-context` ([host a marketplace](https://code.claude.com/docs/en/plugins/host-marketplace)).
- **Versions.** If `plugin.json` has a `version`, people stay on their cached copy until you change it. Leave `version` out and they track your commits instead ([host a marketplace](https://code.claude.com/docs/en/plugins/host-marketplace)).

**Clone plus symlinks.** A skill folder in the personal or project location can be a symlink, and Claude Code loads it once even if several locations point at the same target ([skills](https://code.claude.com/docs/en/skills)). `.claude/rules/` supports symlinks too. A link that points outside your project needs a one-time approval per project, and only rules without a `paths` field load from it ([memory](https://code.claude.com/docs/en/memory)). After a `git pull`, run `/reload-skills` if a new skill doesn't show up ([skills](https://code.claude.com/docs/en/skills)).

**Submodule.** A submodule checks out the commit the project recorded, so every teammate gets the same version until someone moves it. Clone with `git clone --recurse-submodules` ([git-clone](https://git-scm.com/docs/git-clone)), or run `git submodule update --init` after a plain clone. To move to the latest, `git submodule update --remote` uses the remote branch instead of the recorded commit ([git-submodule](https://git-scm.com/docs/git-submodule)). A `CLAUDE.md` can pull in a rules file from it with `@path/to/file` imports. Relative paths resolve from the file that holds the import ([memory](https://code.claude.com/docs/en/memory)).

If several agents edit the context repo at once, give each its own folder and branch. See [Run 10 agents on one project: git worktrees](../git-worktrees/).

## Versioning: dated commits and reading the diff

**Commit small and often.** In the lesson I call it frequent atomic commits: one small, self-contained change, one commit. Weeks later you can ask your agent to read the history and see what changed. That gives it another form of long-term memory.

Commands worth knowing:

| You want | Run |
|---|---|
| Everything that changed lately | `git log --since="2 weeks ago"` ([git-log](https://git-scm.com/docs/git-log)) |
| The full history of one skill, with diffs | `git log -p -- plugins/team-skills/skills/release-notes/` ([git-log](https://git-scm.com/docs/git-log)) |
| Follow one file across renames | `git log --follow -- path/to/SKILL.md` ([git-log](https://git-scm.com/docs/git-log)) |
| What the last commit changed | `git diff HEAD^ HEAD` ([git-diff](https://git-scm.com/docs/git-diff)) |
| A short summary of changed files | `git diff --stat HEAD^ HEAD` ([git-diff](https://git-scm.com/docs/git-diff)) |

`git log` lists commits newest first by default ([git-log](https://git-scm.com/docs/git-log)).

**Read the diff before you trust a skill change.** A skill is more than text. It can grant tools without a permission prompt with `allowed-tools`, and a `` !`command` `` line runs a shell command before Claude even sees the skill ([skills](https://code.claude.com/docs/en/skills)). The docs say to "review the `allowed-tools` of skills checked into a repository before you run Claude Code there." For instruction files, Claude Code asks for approval the first time a project imports files from outside it, "to protect you from files other people commit to a shared project" ([memory](https://code.claude.com/docs/en/memory)). When you pull someone's update, look at what changed, not just that it changed.

**Branch for risky edits.** From the lesson: make a branch before a big or risky change, to your knowledge work or your code. If it goes badly, delete the branch. If it works, merge it or open a pull request.

## Sharing: private repo plus collaborators

1. Create the repo on GitHub and pick a visibility. The valid values are `public` and `private`. You can add a README and a `.gitignore` at the same time ([create a repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository)).
2. Open the repo, then **Settings**, then **Collaborators** in the Access section, then **Add people**. The person gets an email and has access once they accept ([invite collaborators](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/inviting-collaborators-to-a-personal-repository)).

Know what you're granting. Collaborators on a repo owned by a personal account can read and push. They "can't have read-only access." For finer control, create the repo in an organization instead ([permission levels](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/permission-levels-for-a-personal-account-repository)).

The same goes for agents. Let them do the git work, but don't let them push to the shared copy freely. That cloud copy is the backup you trust to be there if your local one gets wiped.

## What not to put there

**Secrets and `.env` files.** List them in `.gitignore`. Know its limit: it only keeps untracked files untracked. "Files already tracked by Git are not affected." To stop tracking a file, run `git rm --cached <file>`, then add it to `.gitignore` ([gitignore](https://git-scm.com/docs/gitignore)).

If a secret does get committed, revoke or rotate it first. Rewriting history doesn't reach copies in other people's clones or in forks ([removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)). The same page suggests turning on push protection to catch hardcoded secrets before they land.

**Personal notes.** `CLAUDE.local.md` is for your own per-project preferences. The docs say to add it to `.gitignore` ([memory](https://code.claude.com/docs/en/memory)).

**Large media.** GitHub's limits ([large files](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)):

| Size | What happens |
|---|---|
| Over 25 MiB | Can't be added through the browser |
| Over 50 MiB | Git warns you |
| Over 100 MiB | GitHub blocks it. You need Git LFS |
| Whole repo | Ideally under 1 GB, under 5 GB strongly recommended |

Even with Git LFS, keep plugin files out of it. Claude Code's clone of a marketplace never downloads LFS content, so those files arrive as pointer files ([host a marketplace](https://code.claude.com/docs/en/plugins/host-marketplace)). Store videos and big datasets somewhere else, and keep a Markdown note in the repo that says where.

## Copy-paste starter

**A `.gitignore` to start from:**

```gitignore
# secrets
.env
.env.*
*.pem
*.key

# personal notes
CLAUDE.local.md

# media and big files live elsewhere
*.mp4
*.mov
*.zip
```

**`plugins/team-skills/.claude-plugin/plugin.json`:**

```json
{
  "name": "team-skills",
  "description": "Our shared skills"
}
```

No `version`, so teammates track your commits ([host a marketplace](https://code.claude.com/docs/en/plugins/host-marketplace)).

**`.claude-plugin/marketplace.json`** (requires `name`, `owner` and `plugins`, and each entry needs `name` and `source`, per [create a marketplace](https://code.claude.com/docs/en/plugin-marketplaces)):

```json
{
  "name": "agent-context",
  "owner": { "name": "Your Team" },
  "plugins": [
    { "name": "team-skills", "source": "./plugins/team-skills" }
  ]
}
```

**A skill:**

```markdown
---
name: release-notes
description: Write release notes from merged changes. Use when asked for release notes, a changelog or a summary of what shipped.
---

1. Read the commits since the last release tag.
2. Group them into Added, Changed and Fixed.
3. Follow the tone in [reference.md](reference.md).
```

**A prompt for your agent:**

> Set up a GitHub repo called agent-context as the shared, versioned home for my agent context. Make it private.
>
> 1. Use this layout: `.claude-plugin/marketplace.json` at the root, one plugin at `plugins/team-skills/` with `.claude-plugin/plugin.json` and a `skills/` folder, plus `rules/` and `knowledge/` folders for plain Markdown.
> 2. Copy my existing skills into `plugins/team-skills/skills/`, one folder per skill, each with a `SKILL.md`. Copy, don't move.
> 3. Copy my rules files into `rules/`. Add a `knowledge/INDEX.md` that lists each note with one line on when to read it.
> 4. Add a `.gitignore` for `.env` files, keys, `CLAUDE.local.md` and media. Before the first commit, search every file for API keys, tokens and passwords, and show me anything you find.
> 5. Run `claude plugin validate .` and fix what it reports.
> 6. Make one commit per step with a clear message.
> 7. Show me `git status` and the full diff, then stop. Don't push until I say so.
> 8. Write a README with the two commands a teammate runs to install it.

## Want more like this?

More agent breakdowns and the full lessons are inside my Skool community, **Agent Architects**: https://www.skool.com/agent-architects
