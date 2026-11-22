# Run 10 agents on one project: git worktrees

You commented WORKTREE, so here is the full breakdown.

**The short version.** Many agents in one folder overwrite each other. One adds a line, another deletes it. A git worktree gives every agent its own folder, its own copy of the code and its own branch. When they finish, you merge the branches into one.

## What a worktree is

A normal repo has one working folder. `git worktree` adds more folders that share the same repository history. Each folder has a different branch checked out, so changes in one folder never touch the files in another. Commits made in any of them land in the same repo, ready to merge.

## Run many agents on one repo

**1. Start from a clean main branch.**

```bash
cd myapp
git switch main
git pull
```

**2. Make one worktree per agent, each on a new branch.**

```bash
git worktree add ../myapp-agent-a -b agent-a
git worktree add ../myapp-agent-b -b agent-b
git worktree add ../myapp-agent-c -b agent-c
git worktree list
```

The folders sit next to the repo, not inside it.

**3. Give each agent one folder and one task.** Open a terminal in `../myapp-agent-a`, start your coding agent there and give it task A. Repeat for B and C. Each agent commits to its own branch.

**4. Merge when they are done.** Back in the main folder:

```bash
git switch main
git merge agent-a
git merge agent-b
git merge agent-c
```

Merge one branch at a time and run your tests after each merge.

**5. Resolve conflicts.** If two agents changed the same lines, git stops and marks the file:

```
<<<<<<< HEAD
the version already on main
=======
the version from the branch
>>>>>>> agent-b
```

Keep the right code, delete the markers, then:

```bash
git add <file>
git commit
```

You can also ask an agent to resolve it: "Resolve the merge conflicts, keep both features, run the tests."

**6. Clean up.**

```bash
git worktree remove ../myapp-agent-a
git branch -d agent-a
git worktree prune
```

`git branch -d` only deletes a branch that is already merged.

## Pitfalls

- **One branch, one worktree.** Git refuses to check out a branch that is already checked out in another worktree. Give every agent a new branch.
- **Install dependencies in each folder.** `node_modules`, virtual environments and build output are not shared. Run your install step in every worktree.
- **Copy untracked files.** `.env` and other ignored files are not in the new folder. Copy what the agent needs.
- **Ports clash.** Two dev servers on port 3000 will fail. Give each worktree its own port.
- **Split the work by area.** Tasks that touch the same files cause conflicts. Give agents separate parts of the codebase where you can.
- **Small, frequent commits.** Ask each agent to commit after every self-contained change. Small commits are easier to merge and easier to undo.
- **Do not delete worktree folders by hand.** Use `git worktree remove`. If you already did, run `git worktree prune`.

## Let your agent do the git work

You do not have to type any of this. Ask your agent: "Create three worktrees for these three tasks, one branch each." Then, when the work is done: "Merge all three branches into main, resolve conflicts and run the tests."

## Want more like this?

The full Git and GitHub lesson and the rest of the course are inside my Skool community, **Agent Architects**: https://www.skool.com/agent-architects
