# Schedule the weekly audit

The audit has two halves:

1. **Read-only half (schedule it):** pick the most-used skills, run self-improve, draft eval sets. This is `weekly-audit-prompt.md` version B. Safe to run unattended, it changes nothing.
2. **Review half (you, 10 to 20 minutes):** review the eval sets, run the skill-creator description loop, apply, re-test. Not scheduled, on purpose.

Pick the section for your tool. Every claim below was checked against the vendor docs on 2026-11-26. Things I could not confirm are marked **not verified**.

First, for all options:

```bash
mkdir -p ~/skill-audits
```

Save the text inside prompt B's code block in `weekly-audit-prompt.md` as `~/skill-audits/weekly-audit-prompt-b.txt` (the scripts below read it from there). Make sure self-improve is installed (README step 1) and you have run the prompt once by hand, so you know what the output looks like and which permission prompts it triggers.

## Claude Code

### Option 1 (recommended): Desktop app scheduled task

Needs the Claude Desktop app (Claude Desktop 1.1.5368 or later for local tasks). It runs on your machine with access to your files and `~/.claude/skills`.

1. Open the **Code** tab, click **Scheduled** in the sidebar (or the sidebar's **More** menu). If your build shows **Routines** instead, click **Routines**, then **New routine**.
2. Click **New task**. If a menu offers **Create with Claude** or **Set up manually**, choose **Set up manually**. If a menu offers **Local** and **Cloud**, choose **Local**. If **Only on this computer** is on top of the dialog or under **Advanced settings**, turn it on. The menu wording varies by app version.
3. Name: `weekly-skill-audit` (it becomes a lowercase kebab-case folder name, must be unique).
4. Instructions: paste prompt **B** from `weekly-audit-prompt.md`.
5. Folder: `~/skill-audits`.
6. Schedule: **Weekly**, pick the day and time (for example Monday 9:00). For a cron expression use **Custom** from the task's Edit form, for example `0 9 * * 1` (days of the week as numbers, Sunday is `0`).
7. Permission mode: pick **Accept edits** (it only needs to write reports in the folder), plus the model you normally use.
8. Click **Create**, then **Run now** once. Watch for permission prompts (it will want to run `python3` and read your transcripts) and choose **always allow** for each, so later runs don't stall. Review them on the task's detail page under **Always allowed**.

Things to know (from the Claude Code docs):

- Local tasks only fire **while the app is open and your computer is awake**. If the computer sleeps through the time, the run is skipped. When the app starts or the computer wakes, Desktop runs **one** catch-up run for the most recently missed time (it looks back 7 days). Turn on **Keep computer awake** in Settings if you want it to fire on time. Closing the laptop lid still sleeps it.
- Each run starts a fresh session a few minutes after the scheduled time (a small deterministic delay).
- Allow rules from `~/.claude/settings.json` also apply to scheduled tasks.
- The task's prompt is stored in `~/.claude/scheduled-tasks/<task-name>/SKILL.md`; edit it there or in the Edit form. Schedule and folder are not in that file.
- Open a run's session from the task's **History** list to see what it did.

Docs: https://code.claude.com/docs/en/desktop-scheduled-tasks

### Option 2: `claude -p` from cron or launchd

`claude -p` runs Claude Code non-interactively. Facts from the docs (https://code.claude.com/docs/en/headless):

- Do **not** add `--bare`: bare mode skips skill discovery ("it doesn't get the list of available skills"). Without it, `claude -p` loads your skills like an interactive session.
- Include `/skill-name` in the prompt to run a skill by name: "User-invoked skills and custom commands work. Include `/skill-name` in the prompt string and Claude Code expands it before running."
- In `-p`, a call that needs approval is denied unless something approves it, so pre-approve with `--allowedTools`. `--permission-prompts none` (v2.1.259 or later) denies anything that would still prompt, instead of hanging.

Create `~/skill-audits/run-weekly-audit.sh`:

```bash
#!/bin/bash
set -euo pipefail
cd "$HOME/skill-audits"
# Prompt B from weekly-audit-prompt.md, saved as this file:
PROMPT="$(cat "$HOME/skill-audits/weekly-audit-prompt-b.txt")"
# Use the full path to claude (run `which claude`); cron has a minimal PATH.
"$HOME/.local/bin/claude" -p "$PROMPT" \
  --permission-mode acceptEdits \
  --permission-prompts none \
  --allowedTools "Bash(python3 *)" "Bash(python3.11 *)" Read Write \
  --output-format text > "$HOME/skill-audits/last-run.log" 2>&1
```

Replace `$HOME/.local/bin/claude` with the output of `which claude`. Make it executable (`chmod +x ~/skill-audits/run-weekly-audit.sh`) and run it once by hand first. If the log says a call was denied, add the matching `--allowedTools` entry. Syntax for tool patterns is the permission rule syntax: `Bash(python3 *)` matches `python3` with any arguments.

Then schedule it:

- **macOS cron** (`crontab -e`): `0 9 * * 1 /bin/bash $HOME/skill-audits/run-weekly-audit.sh` (Mondays 9:00, local time).
- **launchd** (macOS): create `~/Library/LaunchAgents/com.example.weekly-skill-audit.plist` with `ProgramArguments` = `/bin/bash`, `$HOME` expanded to your full home path, `/skill-audits/run-weekly-audit.sh`, and `StartCalendarInterval` with `Weekday` 1, `Hour` 9, `Minute` 0. Load with `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.example.weekly-skill-audit.plist`.
- **Linux systemd timer or cron:** the same script, scheduled with `OnCalendar=Mon 09:00` or a crontab line.

**Not verified:** the Claude Code docs describe `claude -p` in scripts and CI, but they do not describe cron or launchd specifically. Whether a headless job started by cron or launchd can use your subscription login (on macOS the login lives in the keychain, which a background job may not reach) is **not verified**. Test it: run the script once from the scheduler (for example with a cron line a couple of minutes from now) and read `last-run.log`. If it fails to authenticate, use the Desktop option above, or an API key (see the headless docs on `ANTHROPIC_API_KEY`).

### What not to use for this

- **`/loop` and session cron tools (CronCreate):** session-scoped. "Tasks only fire while Claude Code is running and idle", and recurring tasks expire 30 days after you create them (7 days on versions before 2.1.330). Fine for a quick reminder, not for a standing weekly job.
- **Cloud scheduled tasks (routines) and GitHub Actions schedules:** they run in Anthropic's cloud or in CI on a fresh clone with no access to your local files. self-improve reads your transcripts under `~/.claude/projects`, so they have nothing to read.

## Codex

### Option 1: Scheduled tasks (Codex or ChatGPT desktop app)

Codex calls these Scheduled tasks (they used to be called Automations). From the Codex docs (https://learn.chatgpt.com/docs/automations):

1. Create it from a chat: "You can create and update scheduled tasks from a ChatGPT or Codex chat." Tell it what the task should do, when it should run, and whether it returns to the current chat or starts a new one. (The Codex CLI and IDE extension don't include the Scheduled management interface, use the desktop app or ChatGPT web.) The docs don't give click-by-click steps, so open the chat in the project folder you want and ask, for example:

   > Create a scheduled task named weekly skill audit that runs every Monday at 9am in a new chat. Task instructions: (paste prompt B from `weekly-audit-prompt.md`, but start it with "Use $self-improve.")

2. The docs say you can trigger a skill in the task prompt with `$skill-name` in the desktop app, so start the prompt with `Use $self-improve`.
3. For a custom schedule the docs show an RRULE, for example `RRULE:FREQ=WEEKLY;BYDAY=MO;BYHOUR=9;BYMINUTE=0` (adapted from the docs' monthly example `RRULE:FREQ=MONTHLY;BYMONTHDAY=1;BYHOUR=9;BYMINUTE=0`; the weekly form is my adaptation, check it in the app).
4. Test the prompt in a regular chat first, then review the first few runs ("Test the prompt in a regular chat first, then review the first few runs").
5. Results show up in the **Scheduled** view, which "acts as your inbox".

Things to know:

- "Keep the computer on and the app running when a scheduled task needs local files." This one does (your transcripts).
- Tasks "run unattended with your default sandbox settings". In read-only or workspace-write mode a tool call that needs network access or writes outside the sandbox fails. The audit writes reports to `~/skill-audits`, so put that folder inside the project or allow it. The docs suggest workspace-write plus command rules over full access.
- Standalone tasks start a new chat for each run, which suits an audit.

### Option 2: `codex exec` from cron or launchd

```bash
#!/bin/bash
set -euo pipefail
cd "$HOME/skill-audits"
PROMPT="$(cat "$HOME/skill-audits/weekly-audit-prompt-b.txt")"
codex exec --sandbox workspace-write --skip-git-repo-check \
  -o "$HOME/skill-audits/last-run.md" "$PROMPT"
```

From the Codex docs (https://learn.chatgpt.com/docs/non-interactive-mode): `codex exec` "runs in a read-only sandbox" by default, `--sandbox workspace-write` allows edits, `--skip-git-repo-check` is for folders that aren't git repos, `-o <path>` writes the final message to a file, and scheduled jobs are listed among its uses. Don't add `--ephemeral` to the sessions you want audited, it skips writing session files. Schedule the script with a cron line (`0 9 * * 1 /bin/bash $HOME/skill-audits/run-weekly-audit.sh`) or a launchd plist as above.

**Not verified:** the docs page does not say whether `$skill-name` works inside a `codex exec` prompt, so prompt B names the skill in plain words ("Run the self-improve skill"). Codex's own instructions treat a plain-text skill name as a mention ("If the user names a skill (with `$SkillName` or plain text) ... you must use that skill"), from the open-source Codex repo, but I haven't run this exact job end to end. Also **not verified:** that the `workspace-write` sandbox lets the script read transcripts under `~/.claude` and `~/.codex`. Run it once by hand and read `last-run.md`. If it can't read them, widen the sandbox for that one job only after reading the Codex docs on sandbox modes.

The skill-creator description loop is Claude Code only (it runs `claude -p`). For Codex-only skills, the review half is the manual check in README step 6.

## Agent frameworks with their own cron (example)

If your agents run under a framework that has its own persistent cron, use that instead of the app scheduler, and don't use the harness's built-in loop tools inside it. Generic shape:

```bash
<framework-cli> add-cron <agent-name> weekly-skill-audit "0 9 * * 1" "<prompt B from weekly-audit-prompt.md>"
```

Example with the cortextOS CLI (Monday 9:00 local, five-field cron; the CLI also accepts intervals like `6h` or `1d`):

```bash
cortextos bus add-cron <agent-name> weekly-skill-audit "0 9 * * 1" "<prompt B>"
```

(Syntax checked with `cortextos bus add-cron --help`; replace `<agent-name>` with your agent's name.)

## After each scheduled run: the 15-minute review

1. Open `~/skill-audits/<date>/SUMMARY.md`.
2. For each skill with an eval set: edit `trigger-evals.json` (README step 3), run the loop (step 4), apply the diff you approve and re-test (step 5).
3. Note in the next report what you changed, so next week's run shows whether it held.
