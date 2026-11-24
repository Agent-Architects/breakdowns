# Turn a skill into a scheduled automation

You commented AUTOMATE, so here's the full breakdown.

**The short version.** Pick a task you do every day. Record your screen while you say out loud what you're doing and why. Hand the recording and the transcript to your agent and have it interview you until it can write the workflow down as a skill: inputs, steps, outputs, completion criteria, gotchas, and the scripts and tool connections it needs. Run the skill by hand until it works, then put it on a schedule so it runs without you. Everything below was checked against the official docs on Nov 24, 2026.

## The three steps

| Step | What you make | Where it lives |
|---|---|---|
| 1. Capture | A screen recording with narration, plus a text transcript | Any folder, for example `~/Projects/automations/weekly-report/capture/` |
| 2. Skill | A `SKILL.md` with Inputs, Steps, Outputs, Done when, Gotchas, Scripts and tools | `~/.claude/skills/<name>/` or a repo's `.claude/skills/<name>/` ([skills](https://code.claude.com/docs/en/skills)) |
| 3. Schedule | A scheduled run of that skill, with permissions set for nobody watching | Desktop, cloud, GitHub Actions, or cron/launchd plus `claude -p` |

In the lesson I say you can "dictate and describe and record an entire workflow that you do every day," and the agent turns it into "structured inputs, steps, outputs, completion criteria, gotchas, and any scripts or tool connections that it might need." That's the whole method. The rest of this page is how to do each part well.

## Step 1: Record the workflow

On a Mac you need nothing extra.

- **Screen recording.** Press Shift-Command-5 to open Screenshot, pick Record Entire Screen or Record Selected Portion, then under **Options** choose a microphone so your voice is recorded with the video. Turn on Show Mouse Clicks so your clicks show up. Click Record to start, and the stop button in the menu bar to finish. Recordings save as `.mov` files ([Apple: record the screen](https://support.apple.com/en-us/102618), [Apple: screenshots and recordings](https://support.apple.com/guide/mac-help/take-a-screenshot-or-screen-recording-mh26782/mac)).
- **Dictation for the transcript.** Turn it on in System Settings, Keyboard, Dictation. Open a blank note, then start dictating with the Microphone key, the Dictation shortcut, or Edit, Start Dictation. You can dictate "text of any length without a timeout," but it "stops automatically when no speech is detected for 30 seconds," so keep talking or restart it after a pause ([Apple: dictation](https://support.apple.com/guide/mac-help/use-dictation-mh40584/mac)).

**What to say out loud.** The agent only knows what you tell it. Narrate:

1. What starts the task, and when you normally do it.
2. Where every input comes from: which app, which file, which inbox, which filter.
3. Every click and every decision, and the rule behind the decision ("I skip anything under $50 because...").
4. What the finished result looks like and where it goes.
5. The weird cases: what you do when the export is empty, the login expired, or a number looks wrong.

**Make the video readable.** Claude Code's Read tool takes text, images (PNG, JPEG, GIF, WebP), PDFs and notebooks. Video isn't on that list ([tools reference](https://code.claude.com/docs/en/tools-reference)). So snap a screenshot (Shift-Command-3) at each key screen while you record, or ask your agent to pull a still every few seconds from the `.mov` with ffmpeg's `fps` filter ([ffmpeg filters](https://ffmpeg.org/ffmpeg-filters.html)). Save the stills next to the transcript.

## Step 2: Turn it into a skill

A skill is a folder with a `SKILL.md` file. The file has YAML frontmatter between `---` markers and Markdown instructions after it ([skills](https://code.claude.com/docs/en/skills)). What matters for an automation:

- **`description` is the trigger.** Claude matches your request against it, so it "must say both what the Skill does and when to use it" ([Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)). Write it in third person ([best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)).
- **`name` rules.** Lowercase letters, numbers and hyphens, 64 characters max, and not the words `anthropic` or `claude`. The description caps at 1,024 characters ([best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)). In Claude Code, `name` defaults to the folder name ([skills](https://code.claude.com/docs/en/skills)).
- **Keep the body short.** Under 500 lines. Put long reference material in separate files the skill links to ([skills](https://code.claude.com/docs/en/skills)).
- **Scripts do the exact work.** Bundled scripts run through bash, and "only their output enters context" ([Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)). Use them for anything that must be done the same way every time.
- **Pre-approve the script.** `${CLAUDE_SKILL_DIR}` expands to the skill's folder in both the body and the `allowed-tools` rule, so a skill can run its own script without a permission prompt ([skills](https://code.claude.com/docs/en/skills)).
- **Block questions in background runs.** `disallowed-tools` removes tools while the skill is active. The docs' own example is `AskUserQuestion` "for a background loop" ([skills](https://code.claude.com/docs/en/skills)).

**Where to save it:** `~/.claude/skills/<name>/` works in all your projects on this machine, but not in cloud sessions. For a cloud run, commit it to the repo's `.claude/skills/<name>/` or turn it on in your claude.ai account ([skills](https://code.claude.com/docs/en/skills)).

### Copy-paste SKILL.md template

```markdown
---
name: weekly-report
description: Builds the Monday sales report from the CRM export and posts a short summary to Slack. Use when asked for the weekly report, or when a scheduled run says to run weekly-report.
allowed-tools: Read Write Bash(${CLAUDE_SKILL_DIR}/scripts/fetch.sh *)
disallowed-tools: AskUserQuestion
---

# Weekly report

## Inputs
- CRM export: run `${CLAUDE_SKILL_DIR}/scripts/fetch.sh last-7-days`. Output is a CSV in ./data/.
- Targets: ./data/targets.csv (one row per rep).
- If an input is missing or empty: stop, write the reason to the run log, do not guess.

## Steps
1. Fetch the export (script above). Check it has more than 0 rows.
2. Join it to targets by rep email.
3. Work out revenue vs target per rep and for the team.
4. Write the report using the layout in [layout.md](layout.md).
5. Post the 5-line summary to #sales.

## Outputs
- File: ./reports/YYYY-MM-DD.md
- Message: one Slack post in #sales with the team total and the top 3 reps.

## Done when
- [ ] The report file exists and has a row for every rep in targets.csv.
- [ ] Totals in the report match the CSV totals.
- [ ] Exactly one Slack post was sent.
- [ ] One line was added to the run log.

## Gotchas
- The export uses UTC dates. Reports use local dates.
- Refunds show as negative rows. Keep them in the total.
- If the script prints "session expired", stop. Don't try to log in.

## Scripts and tools
- scripts/fetch.sh: pulls the CRM export. Reads the API key from the CRM_API_KEY environment variable. Never write keys into this folder.
- Slack: through the Slack MCP server or connector. Post only to #sales.

## Run log
Append one line to ./logs/weekly-report.log: date, status (done, stopped or failed), files written, anything skipped and why.
```

The "Done when" list is the part people skip, and it's what makes an unattended run safe. Anthropic's guide recommends a checklist Claude copies and ticks off, plus a "run validator, fix errors, repeat" loop for anything that can be checked ([best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)).

### The interview prompt

In the video I use my own builder skill for this interview. Here's the same step done by hand. Put the transcript and stills in one folder and give your agent this:

> I recorded myself doing a task I want to automate. The transcript is in `capture/transcript.txt` and the screenshots are in `capture/frames/`. Read all of them first.
>
> 1. Summarize the workflow back to me in numbered steps, and tell me which step each screenshot shows.
> 2. Interview me, one question at a time, until you know: what triggers the task, every input and where it comes from, every decision rule, the exact outputs and where they go, what "done" looks like in checks you can verify, and what goes wrong. Ask about edge cases I didn't mention.
> 3. Mark each step as either judgment (Claude does it) or exact (a script should do it). Draft each script, keep it small, and read secrets from environment variables only.
> 4. List every app this needs. For each one, tell me the connection to use (an MCP server, a connector, a CLI or an API) and walk me through connecting it. Don't continue until each connection works.
> 5. Write `~/.claude/skills/<name>/SKILL.md` with these sections: Inputs, Steps, Outputs, Done when, Gotchas, Scripts and tools, Run log. Third-person description that says what it does and when to use it. Under 500 lines.
> 6. List the exact tools the skill needs as permission rules, so I can pre-approve only those.
> 7. Run it once with me watching. Fix what breaks. Then ask me how often and at what time I want it to run, and which scheduler fits. Don't schedule anything until I say yes.

Run it by hand a few times with `/weekly-report` before you schedule it. If it can't finish with you watching, it won't finish alone.

## Step 3: Put it on a schedule

| Option | Runs on | Machine must be on | Local files | Shortest interval | Use it for |
|---|---|---|---|---|---|
| [Desktop scheduled task](https://code.claude.com/docs/en/desktop-scheduled-tasks) | Your machine | Yes, app open and awake | Yes | 1 hour in the forms | Anything that touches your own files and apps |
| [Cloud scheduled task](https://code.claude.com/docs/en/routines) | Anthropic's cloud | No | No, fresh repo clone | 1 hour | Repo and connector work that must run with the laptop shut |
| [`/loop`](https://code.claude.com/docs/en/scheduled-tasks) | Your open session | Yes, session open | Yes | 1 minute | Polling while you work. Not for daily jobs |
| [GitHub Actions](https://code.claude.com/docs/en/github-actions) | GitHub runner | No | No, the checked-out repo | Set by your cron line | Repo jobs you want in CI |
| cron or launchd plus [`claude -p`](https://code.claude.com/docs/en/headless) | Your machine | Yes | Yes | 1 minute | Full control from a script |

The interval and machine columns come from the [compare table](https://code.claude.com/docs/en/scheduled-tasks) in the docs, except the last two rows.

**Desktop scheduled task.** Needs Claude Desktop 1.1.5368 or later. In the Code tab, click **Scheduled**, then **New task**. Name it, write the instructions (for example "Use the weekly-report skill and finish every item in its Done when list"), turn on **Only on this computer**, pick the folder, pick Hourly, Daily, Weekdays or Weekly, then set the permission mode. Each run is a fresh session. If the computer sleeps through a run, it's skipped, and on wake Desktop runs one catch-up for the most recent miss in the last seven days. So a 9am task can run at 11pm. Click **Run now** after creating it and pick "always allow" on each prompt, so later runs don't stall. The task's prompt lives at `~/.claude/scheduled-tasks/<task-name>/SKILL.md` ([Desktop scheduled tasks](https://code.claude.com/docs/en/desktop-scheduled-tasks)).

**Cloud scheduled task.** Formerly called routines, in research preview, on Pro, Max, Ultra, Team and Enterprise plans. Run `/schedule` in the CLI, for example `/schedule daily PR review at 9am`, or use claude.ai/code/routines. Each run clones your repos, loads the skills committed there, and can use the connectors you include. All your connectors are included by default, so remove the ones the task doesn't need. Runs start in auto mode when it's available. A custom cron expression is read in UTC, and a run set exactly on the hour can start late, so pick a time like 9:07 ([cloud scheduled tasks](https://code.claude.com/docs/en/routines)).

**`/loop`.** `/loop 20m /weekly-report` re-runs a skill inside your open session. Tasks stop when the session exits, recurring ones expire after 7 days, and a fire skips skills marked `disable-model-invocation: true` ([scheduled tasks](https://code.claude.com/docs/en/scheduled-tasks)).

**GitHub Actions.** Check out the repo so `.claude/skills/` is on the runner, then pass the skill as the prompt. A skill prompt can use the tools its `allowed-tools` grants. GitHub only runs schedules from the default branch, and turns them off in public repos after 60 days with no activity ([GitHub Actions](https://code.claude.com/docs/en/github-actions)). The cron here is in UTC:

```yaml
name: Weekly report
on:
  schedule:
    - cron: "7 9 * * 1"
jobs:
  report:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v6
      - uses: anthropics/claude-code-action@v1
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          prompt: "/weekly-report"
          claude_args: "--max-turns 30"
```

**cron or launchd plus `claude -p`.** `-p` runs Claude Code non-interactively, and a `/skill-name` in the prompt string is expanded before it runs. It exits 0 on success and non-zero on failure ([headless](https://code.claude.com/docs/en/headless)). Wrap it in a script:

```bash
#!/bin/zsh
# weekly-report.sh: use full paths, schedulers don't load your shell PATH
cd /Users/YOU/Projects/reports || exit 1
/full/path/to/claude -p "/weekly-report" \
  --permission-mode dontAsk \
  --allowedTools "Read,Write,Bash(/Users/YOU/.claude/skills/weekly-report/scripts/fetch.sh *),mcp__slack__*" \
  --max-turns 30 \
  --max-budget-usd 3 \
  --output-format json >> logs/weekly-report.jsonl 2>&1
```

Run `which claude` to get the real path. `mcp__slack__*` allows every tool from a server named `slack`. Use your server's real name, or name single tools ([permissions](https://code.claude.com/docs/en/permissions)). Don't add `--bare` here: bare mode skips skill discovery and doesn't read your subscription login ([headless](https://code.claude.com/docs/en/headless)). If the job can't find your login, run `claude setup-token` and set the printed token as `CLAUDE_CODE_OAUTH_TOKEN` in the job's environment. It's a one-year token meant "for CI pipelines and scripts" ([authentication](https://code.claude.com/docs/en/authentication)). Treat it like a password.

On a Mac, Apple calls launchd "the preferred way" to add a timed job, and cron is deprecated in its favor. A launchd job with `StartCalendarInterval` that was due while the Mac slept runs on wake. Cron just skips it ([Apple: scheduling timed jobs](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html)). Save this as `~/Library/LaunchAgents/com.you.weekly-report.plist`. Per-user agents in that folder load at login ([Apple: launchd jobs](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.you.weekly-report</string>
  <key>ProgramArguments</key>
  <array><string>/Users/YOU/Projects/reports/weekly-report.sh</string></array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Weekday</key><integer>1</integer>
    <key>Hour</key><integer>9</integer>
    <key>Minute</key><integer>7</integer>
  </dict>
</dict>
</plist>
```

On Linux, `crontab -e` and a line like `7 9 * * 1 /home/you/reports/weekly-report.sh` does the same. The five fields are minute, hour, day of month, month and day of week ([crontab(5)](https://man7.org/linux/man-pages/man5/crontab.5.html)).

## Permissions when nobody is watching

- **`claude -p` starts in Manual mode** (v2.1.302 or later) when nothing sets a mode. Calls that need approval are denied, so a run with no rules can do almost nothing ([permission modes](https://code.claude.com/docs/en/permission-modes)).
- **`--allowedTools`** lists what runs without asking, in permission rule syntax. `Bash(git diff *)` matches `git diff` with or without arguments ([headless](https://code.claude.com/docs/en/headless)).
- **`dontAsk`** denies anything that would prompt and runs only reads and pre-approved tools. The docs suggest it for "locked-down CI and scripts" ([permission modes](https://code.claude.com/docs/en/permission-modes)). Start here.
- **`auto`** has a classifier review each action instead of you. Add `--permission-prompts none` so anything that would still prompt is denied and the run moves on ([headless](https://code.claude.com/docs/en/headless)).
- **`bypassPermissions`** is for "isolated containers and VMs only" ([permission modes](https://code.claude.com/docs/en/permission-modes)). Not your laptop.
- **Deny rules win.** Rules are checked deny, then ask, then allow. A `"deny": ["Bash(git push *)"]` in settings blocks it even if something else allows it ([permissions](https://code.claude.com/docs/en/permissions)).
- **Cap the run.** `--max-turns` and `--max-budget-usd` work in print mode. The budget is a client-side estimate and spend can pass it, so leave headroom ([CLI reference](https://code.claude.com/docs/en/cli-reference)).

## What goes wrong

- **The skill asks a question and nobody answers.** Put `AskUserQuestion` in `disallowed-tools` and tell the skill to stop and log instead of asking.
- **It runs but does nothing.** A cloud run can show Succeeded even when the work didn't happen. The status says how the session ended, not whether the job got done, so read the transcript ([cloud scheduled tasks](https://code.claude.com/docs/en/routines)). Your Done when list and run log are how you find out.
- **Desktop runs stall on a prompt.** Do a **Run now** first and approve each tool for that task ([Desktop scheduled tasks](https://code.claude.com/docs/en/desktop-scheduled-tasks)).
- **The skill isn't there.** Cloud sessions don't load `~/.claude/skills/`, and `--bare` skips skills ([skills](https://code.claude.com/docs/en/skills), [headless](https://code.claude.com/docs/en/headless)).
- **Wrong time.** Cloud custom cron and GitHub cron are UTC. Desktop and `/loop` use local time, and both add a small delay ([routines](https://code.claude.com/docs/en/routines), [scheduled tasks](https://code.claude.com/docs/en/scheduled-tasks)).
- **Late catch-up runs.** A Desktop task can fire hours late after sleep. Add a guard like "only process today's data" ([Desktop scheduled tasks](https://code.claude.com/docs/en/desktop-scheduled-tasks)).
- **Too many tools.** A cloud run can use every connector you include, writes too ([cloud scheduled tasks](https://code.claude.com/docs/en/routines)). Give it only what this one job needs.
- **Secrets in the skill folder.** Keys go in environment variables or a secret store, never in `SKILL.md` or scripts.
- **The recording was vague.** If you didn't say the rule out loud, the agent guesses it. Record again rather than patch the guess.

## Sources

| Claim | Source |
|---|---|
| Skill folder and `SKILL.md` structure, frontmatter fields, `allowed-tools`, `disallowed-tools`, `${CLAUDE_SKILL_DIR}`, 500-line tip, skill locations, cloud sessions skip personal skills | https://code.claude.com/docs/en/skills |
| Description must say what and when, three loading levels, scripts' output only enters context | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview |
| `name` and `description` limits, third-person descriptions, checklists and feedback loops | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices |
| Read tool file types: text, images, PDFs, notebooks | https://code.claude.com/docs/en/tools-reference |
| Compare table of Cloud, Desktop and `/loop`; 7-day expiry; jitter; `disable-model-invocation` skills skipped by fires | https://code.claude.com/docs/en/scheduled-tasks |
| Desktop tasks: version, steps, sleep and catch-up runs, Run now and always allow, prompt stored as `SKILL.md` | https://code.claude.com/docs/en/desktop-scheduled-tasks |
| Cloud tasks: research preview, plans, `/schedule`, connectors, auto mode, UTC cron, run status meaning | https://code.claude.com/docs/en/routines |
| `claude -p`, `/skill-name` in `-p`, exit codes, `--bare`, `--allowedTools`, `dontAsk`, `auto`, `--permission-prompts none` | https://code.claude.com/docs/en/headless |
| `-p` starts in Manual mode, mode table, `bypassPermissions` for isolated containers and VMs | https://code.claude.com/docs/en/permission-modes |
| Rule order deny, ask, allow; settings rule example | https://code.claude.com/docs/en/permissions |
| `--max-turns`, `--max-budget-usd` | https://code.claude.com/docs/en/cli-reference |
| `claude setup-token`, `CLAUDE_CODE_OAUTH_TOKEN` for scripts, bare mode doesn't read it | https://code.claude.com/docs/en/authentication |
| GitHub Actions schedule, checkout then `/skill-name` prompt, default branch and 60-day rule | https://code.claude.com/docs/en/github-actions |
| Mac screen recording with Shift-Command-5 and a microphone | https://support.apple.com/en-us/102618 |
| Screenshot options, `.mov` files, Shift-Command-3 | https://support.apple.com/guide/mac-help/take-a-screenshot-or-screen-recording-mh26782/mac |
| Mac Dictation: turning it on, no timeout, stops after 30 seconds of silence | https://support.apple.com/guide/mac-help/use-dictation-mh40584/mac |
| launchd preferred over cron, sleep behavior, `StartCalendarInterval` | https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html |
| Per-user agents load from `~/Library/LaunchAgents` at login; `Label` and `ProgramArguments` required | https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html |
| ffmpeg `fps` filter | https://ffmpeg.org/ffmpeg-filters.html |
| crontab time fields | https://man7.org/linux/man-pages/man5/crontab.5.html |

## Want more like this?

More agent breakdowns and the full lessons are inside my Skool community, **Agent Architects**: https://www.skool.com/agent-architects
