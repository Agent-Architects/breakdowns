# Teach your agent to climb the context tree

You commented, so here's the full breakdown.

The reel said one thing: your agent's instruction files are a tree.

- The **trunk** is your root instructions file, `CLAUDE.md` or `AGENTS.md`. Your agent always reads it first.
- From the trunk, the agent can only see the **first level of branches**. So the trunk lists every top-level folder and a one-line summary of what is inside. One branch leads to apples, one leads to oranges.
- When the agent climbs onto a branch, that branch becomes a new trunk. Each folder has its own `INDEX.md` that lists the next branches. The apples folder routes to juice and jello.
- The whole thing is a **fractal**: trunks branching into branches, all the way up.
- This is **progressive disclosure**. The agent only loads what it needs for the task in front of it. It is the same reason skills work so well.

This page turns that picture into a layout you can build today. It's written so you can hand it straight to your coding agent. The starter prompts are at the bottom.

---

## The picture

```
                         [ juice ]   [ jello ]       [ marmalade ]
                               \       /                   |
                          apples/INDEX.md            oranges/INDEX.md
                                    \                   /
                                     \                 /
                                CLAUDE.md / AGENTS.md   <- trunk, always loaded
                                          |
                                     your agent
```

At every fork, the agent reads one small index file, picks one branch, and ignores the rest.

---

## Why one giant instruction file fails

Most people start with one instructions file and keep adding to it. Every time the agent makes a mistake, a new rule goes in. Six months later it's 1,500 lines and the agent seems to be getting worse, not better.

Three things go wrong:

1. **Context cost.** The root file is loaded into every session, for every task. If 90% of it is about things the current task never touches, you pay for that 90% on every single turn, and it crowds out room for the actual work.
2. **Attention.** Models follow instructions less reliably as the pile of instructions grows. A rule about database migrations sitting next to a rule about email tone means both get a little less attention. The one that matters for this task gets buried.
3. **Conflicts and drift.** In a long file, the same rule ends up written twice in slightly different words. Nobody notices until the agent follows the older one.

A tree fixes all three. The trunk stays small, so it's cheap to load and easy to follow. Detail lives where it's relevant, and it only gets loaded when the task goes there.

---

## The tree layout

Here's a real example: a workspace for an agent that helps run a small online business.

```
workspace/
├── CLAUDE.md                  # trunk: who you are, hard rules, the branch list
├── content/
│   ├── INDEX.md               # routes to video, newsletter, social
│   ├── video/
│   │   ├── INDEX.md           # routes to scripts, editing
│   │   ├── scripts/
│   │   │   └── INDEX.md       # leaf: how to write a script, template, examples
│   │   └── editing/
│   │       └── INDEX.md       # leaf: tools, export settings, review steps
│   ├── newsletter/
│   │   └── INDEX.md           # leaf: format, send process, list rules
│   └── social/
│       └── INDEX.md           # leaf: per-platform rules, posting checklist
├── sales/
│   ├── INDEX.md               # routes to leads, proposals
│   ├── leads/
│   │   └── INDEX.md
│   └── proposals/
│       └── INDEX.md
├── operations/
│   ├── INDEX.md               # routes to finance, support
│   ├── finance/
│   │   └── INDEX.md
│   └── support/
│       └── INDEX.md
└── .claude/skills/
    ├── write-script/SKILL.md
    └── weekly-report/SKILL.md
```

If you use `AGENTS.md` instead of `CLAUDE.md`, the idea is identical. Swap the file name.

The rule of thumb: **every folder that has subfolders gets an `INDEX.md`.** Every folder is reachable from the trunk by following index files, one hop at a time.

---

## What goes where

### The trunk (root `CLAUDE.md` / `AGENTS.md`)

The trunk is the only file the agent is guaranteed to read. Keep it to what must be true for every task:

- One or two lines on what this workspace is for
- Hard rules that apply everywhere (never delete files without asking, never push to main, never send a message without approval)
- How to verify work in general (the commands to test, lint, or check)
- **The branch list:** every top-level folder with a one-line summary and a routing line

What doesn't go in the trunk: anything that only applies to one area. If a rule starts with "when writing scripts..." it belongs in the scripts branch.

Target size: under 100 lines. Many good trunks are under 50.

### A branch (`folder/INDEX.md` with subfolders)

A branch is a trunk for the level above it. It contains:

- One line on what this area covers
- Rules that apply to everything in this area, and only this area
- The list of sub-branches, each with a summary and a routing line

A branch should not repeat the trunk's rules. The agent already has them.

### A leaf (`folder/INDEX.md` with no subfolders)

A leaf is where the real detail lives:

- The step-by-step process for this kind of task
- Templates, examples, and gotchas
- Pointers to files in the folder (data, past work, reference docs) and when to open each one

Leaves can be longer than branches, but if a leaf gets past a few hundred lines, it's a sign it should split into its own branches.

---

## How to write routing lines

Routing lines are the most important lines in the whole tree. They're how the agent decides which branch to climb. A bad routing line is a branch the agent never finds.

Write them as conditions, not labels:

```markdown
## Where to go next

- If the task is about videos, newsletters or social posts, read `content/INDEX.md`.
- If the task is about leads, follow-ups or proposals, read `sales/INDEX.md`.
- If the task is about money, invoices or customer support, read `operations/INDEX.md`.

Read only the index for the area the task touches. Do not open the other branches.
```

What makes a good routing line:

- **Starts with the trigger**, "If the task is about...", so the agent can match it against what it was asked.
- **Names the words a user would actually say.** "Invoices" and "refunds", not "financial operations".
- **Points to one exact file path.** No "see the content folder".
- **Says what's inside**, like apples or oranges, so the agent can decide without opening it.

Compare:

- Weak: `content/ - content stuff`
- Strong: `If the task is about writing or editing videos, newsletters or social posts, read content/INDEX.md.`

---

## How skills fit in

Skills are the same idea, built into the harness.

A skill is a folder with a `SKILL.md` file. The top of that file has a short frontmatter block with a `name` and a `description`. Only the name and description are loaded into context up front. The body of the skill, plus any extra files it points to, only loads when the agent decides the skill is relevant to the task.

```markdown
---
name: write-script
description: Write a short-form video script. Use when asked for a script, hook, or talking points for a reel or short.
---

# Write a script
(full process, template and examples, only loaded when used)
```

So the description is a routing line. It's the same "if the task is about X" sentence, just placed where the harness reads it for you.

How to split the work between the tree and skills:

- **Tree:** knowledge about *where things are and what's true here.* Folders, data, rules for an area, past work.
- **Skills:** a *repeatable procedure* the agent runs. Write a script, publish a post, run the weekly report.
- A leaf `INDEX.md` can point to a skill: "To write a new script, use the `write-script` skill."

Write skill descriptions with the same care as routing lines. A skill with a vague description never gets loaded, no matter how good its body is.

---

## Migrating a big CLAUDE.md into a tree

You don't have to start over. Here's the order:

1. **Back it up.** Copy the current file to `CLAUDE.md.bak` (or rely on git) so you can compare later.
2. **Tag every section.** Go through the file and label each rule or section with the area it applies to: "everywhere", "content", "sales", and so on.
3. **Pick your first-level branches.** Usually 3 to 7 areas fall out of the tags. If you have more than 7, group some.
4. **Create the folders and `INDEX.md` files.** Move each tagged section into the index for its area. Move deeper detail into leaves.
5. **Rewrite the trunk.** Keep only the "everywhere" rules, then add the branch list with routing lines.
6. **Turn procedures into skills.** Any section that reads like "to do X, follow these steps" is a skill candidate.
7. **Dedupe.** Search the whole tree for rules that now appear twice. Keep each rule in the highest folder where it's always true, and delete the copies.
8. **Test with real tasks.** Give the agent 5 typical requests and ask it to say which files it read and why. If it reads the wrong branch, or no branch, fix the routing line.

Move in small steps. Migrating one area at a time is safer than one big rewrite.

---

## Checks for a healthy tree

Run through this list after building it, and again every few weeks:

- [ ] **Short files.** Trunk under about 100 lines. Branch indexes under about 60. Leaves split once they get long.
- [ ] **Everything is reachable.** Every folder can be reached from the trunk by following routing lines. No orphan folders the agent can't find.
- [ ] **No duplicated rules.** Each rule lives in exactly one place, the highest folder where it's always true.
- [ ] **Every routing line points to a real file.** No broken paths after renames.
- [ ] **Routing lines say what's inside.** Each one has a summary, not just a folder name.
- [ ] **Skill descriptions say when to use them.** "Use when..." is in every description.
- [ ] **The agent picks the right branch.** Spot check: ask it which files it would read for a task, without doing the task.

---

## Starter prompts

Copy any of these into Claude Code, Codex, Cursor or whatever agent you use.

### 1. Audit your current setup

```text
I want to turn my agent's instructions into a "context tree": a short root
instructions file (CLAUDE.md or AGENTS.md) that routes to folders, and an
INDEX.md in each folder that routes further. Detail only loads when a task
needs it (progressive disclosure).

Do not change anything yet. Inspect and report:

1. How long is my root instructions file, and which sections apply to every
   task vs only one area?
2. Which top-level folders exist, and which have no instructions or index
   pointing to them?
3. Which rules appear more than once, in any file?
4. Which sections describe a repeatable procedure that should be a skill?

Finish with a proposed tree: the first-level branches (3 to 7), what each
covers, and which existing sections move into each one.
```

### 2. Build the tree

```text
Build a context tree for this workspace using the plan we agreed on.

- Keep the root CLAUDE.md / AGENTS.md under 100 lines: purpose, hard rules
  that apply everywhere, how to verify work, and a branch list.
- Every branch in the list gets a routing line in this form:
  "If the task is about <things a user would actually say>, read
  <folder>/INDEX.md."
- Every folder with subfolders gets an INDEX.md with: one line on what it
  covers, rules for this area only, and routing lines to its subfolders.
- Leaf INDEX.md files hold the detailed process, templates and pointers to
  files in that folder.
- Never repeat a rule. Put it in the highest folder where it is always true.

Show me the new root file and the list of files you created before you
delete anything from the old instructions file.
```

### 3. Check the tree

```text
Check my context tree and report problems. Do not fix anything yet.

1. List every folder and whether it is reachable from the root file by
   following routing lines. Flag orphans.
2. List every routing line whose file path does not exist.
3. List any rule that appears in more than one file.
4. Flag any instructions file over 100 lines (root) or 60 lines (branch).
5. For each of these 5 tasks, say which files you would read, in order,
   and why: <paste 5 real tasks you give your agent>.

Finish with a short list of fixes, smallest first.
```

---

## Sources

- Claude Code memory and CLAUDE.md: https://code.claude.com/docs/en/memory
- Claude Code skills: https://code.claude.com/docs/en/skills
- AGENTS.md format: https://agents.md
