# Agent Architects: free breakdowns

One-page breakdowns of my short videos on building with AI agents. Each folder is one video.

Want the full video lessons and the rest of the course? They are inside my Skool community, Agent Architects.

## Breakdowns

| Breakdown | Video |
|---|---|
| [Every AI agent is made of 3 parts](f11-three-parts-of-an-agent/) | model, harness, context |
| [Build your own software factory](software-factory/) | 97 PRs in 24 hours, the 7 layers of verification, intake, orchestration |
| [How an AI agent edits video with no mistakes](ai-video-editing-workflow/) | Drive inbox, VM, Whisper cuts, review link, motion graphics, funnel, posting |
| [Teach your agent to climb the context tree](context-tree/) | trunk, branches, INDEX.md routing, progressive disclosure, skills |
| [AI models are really a mirror of you](ai-models/) | tokens, attention, training, context window, grounding, verification |
| [Pick a model using your own work](model-selection-field-test/) | task scorecard, cost per successful run, latency, and when to try a more capable model |
| [The context playbook: how to engineer your agent's context](context-engineering/) | budget, accuracy, skills, instruction files, routing, compaction, subagents, load-order map, templates |
| [Fable prompt: 10 changes to test with Claude Fable 5.2](fable-5-2-prompting/) | ownership, finishing work, effort, subagent cost, never-rules, approvals, token counters, append-only history, silent clients |
| [Give your agent the right tools](agent-tools/) | scripts, CLI, MCP, MCP vs CLI tokens, browser automation, reusable browser commands, computer use |
| [Edit your reel like any reel you love](edit-like-any-reel/) | rough cut, reference study, HTML scenes, head matte, captions, self-check, Opus 5.5 vs Fable 5.2 |
| [An AI edited another AI's weights](ai-brain-surgery/) | MIT CSAIL study, 0.016% of weights edited, MATH-500 7.9% to 48.1%, the repetition-loop catch, the Gemma failure, what it means for agent builders |
| [Make any CLI tool discoverable to your agent](cli-skill-discovery/) | tool vs skill, skill descriptions in context, step-by-step guide, copy-paste SKILL.md template for a CLI |
| [One proxy for all your AI subscriptions](cli-proxy/) | CLIProxyAPI setup, serving across machines, rotation, usage dashboard, one-off sandbox token gate, security checklist |
| [Search every conversation your coding agents ever had](cass/) | cass by Jeffrey Emanuel, 30+ agents, one local SQLite index, install, agent-safe search flags, redaction and raw mirror, license rider |
| [Claude Code /advisor: when to ask a smarter model](claude-code-advisor/) | how it works, setup, pairings, cost, when a weaker model should consult (dev, knowledge work, automations), drop-in skill |
| [Claude Code code mode: the full guide](claude-code-code-mode/) | mental model, setup, 12 workflows with prompts, when not to use it, permissions per mode, 5 hook recipes, long-running code, troubleshooting, limits |
| [Gemini 4 Neon: Opus 5.5 level for about half the price](gemini-4-neon/) | every number with its source, Opus 5.5 comparison, cost per coding-agent task, the speed catch, which model to pick for what |
| [Run 10 agents on one project: git worktrees](git-worktrees/) | what a worktree is, 6 steps with exact commands, merging and conflicts, cleanup, 7 pitfalls, prompts to let your agent do the git work |
| [A2UI 1.0: let your agent answer with UI, not text](a2ui/) | what it is, why it beats text, surfaces, components and data model, real JSON messages, quickstart and skill, model vs builder decisions, catalog safety, who uses it |
| [Claude Ship: from open PR to ready to merge](claude-ship/) | /ship and /steward on any plan, the watch and what it blocks, hosted Code Review, PR Steward and Claude Approvals, starter approvals.yml, auto-merge warning, costs and spend limits |
| [How always-on AI agents work: the 7 parts](always-on-agents/) | agent loop, ways to act, app connections and tool search, channels, memory and dreaming, cron and webhook triggers, permission layers, where to start |
| [GitHub is your agent database: version and share your skills](github-agent-database/) | what goes in, repo layout, project skills, plugin marketplace, symlinks and submodules, dated commits and diff review, private repo and collaborators, secrets and large files, starter files and setup prompt |
| [Context rot: how one stale fact spreads, and the state file that stops it](context-rot/) | stale facts in context and instruction files, the study where agents followed the file over the code, dated STATE.md template, safe /compact and /clear |
| [The subagent test: do you need the history, or just the answer?](subagent-test/) | the one question, how subagents work, read-only helpers, handoff files, copy-paste researcher subagent, when not to use one |
| [Give your reviewer agent fresh context (and maybe a different model)](fresh-context-reviewer/) | self-preference and self-correction research, fresh session vs different model, four setups, reviewer subagent and prompt |
| [Turn a skill into a scheduled automation](skill-to-automation/) | record the workflow, SKILL.md template, interview prompt, Desktop and cloud scheduled tasks, GitHub Actions, claude -p with cron or launchd, unattended permissions |
| [Prune your skills every time a new model drops](prune-skills/) | why old skills get over-prescriptive, what the docs say to cut, baseline evals, keep vs cut table, audit prompt |
| [My agents rent their own computers: the scripts and rules I give them](agents-rent-vms/) | why, what it costs, hcloud.py rent/list/delete, bootstrap with egress guard, idle cost guard, agent rules block, setup prompt, security checklist |
| [Instagram buried half my trial reels: the uniquify skill](uniquify-trial-reels/) | what trial reels are, our suppression numbers, each uniquify transform and why, the full v2 script, posting rules, setup prompt, what we don't know yet |
| [Tailscale: your own private cloud for you and your agents](tailscale-private-cloud/) | what a tailnet is, setup, Serve, Taildrop, node sharing, Tailscale SSH, agent-hosted app rules, 5 starter prompts, security |
| [How AI models stay grounded: the model is a snapshot, the harness checks reality](model-grounding/) | training data and cutoffs, the president test, harness tools that check the real world, verify-before-you-claim rules block, research prompt |
| [My agents built my own Calendly. Here's yours.](slotwise-booking/) | Slotwise, why build your own, features, Cloudflare and Node hosting, Google Calendar sync, the /setup runbook, what your agent does vs what you click, setup prompt, costs |
