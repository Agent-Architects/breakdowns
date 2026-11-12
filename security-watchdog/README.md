# security-watchdog

An agent skill that watches the security news for the things YOU actually use, and has a fix ready when
something hits.

## What it does
1. **Maps your stack.** Every dependency in your projects' lockfiles, your machine, CLIs, AI tools and MCP servers,
   editor extensions, and the services you host on or pay for (and which keys each one holds).
2. **Picks its own sources.** Base feeds (GitHub malware and security advisories, OSV, CISA Known Exploited
   Vulnerabilities, supply-chain research blogs, oss-security) plus security feeds for your specific vendors, each
   one fetched and verified before it is added.
3. **Checks every 30 minutes**, cheapest step first:
   - a script fetches the feeds and keeps only what is new (no model, no tokens);
   - a small, cheap model reads the new items and decides which ones touch your stack, by meaning, not keywords;
   - only when something is relevant, your strongest model checks the real exposure (installed versions, whether a
     bad package ever ran, which keys a breached service holds) and prepares the fix: a branch or draft PR with the
     upgrade, an ordered key-rotation list, or a written plan.
4. **Asks you first.** You get one message per finding on the channel you choose (Slack, Telegram, email, ...).
   Nothing is merged, deployed or rotated until you say yes.
5. **Gets better.** It logs how fast each alert came, adds faster sources when it was late, and rescans your stack
   weekly.

## Install
Copy the `security-watchdog` folder into your agent's skills folder (for example `~/.claude/skills/` for Claude
Code, or wherever your harness loads skills), then tell your agent:

> Install the security-watchdog skill and set it up.

The agent asks a few questions (project folders, servers, services, where to send alerts), builds the map, picks
sources, runs a test alert end to end, and installs a 30-minute schedule with your OS scheduler (launchd, cron or
Task Scheduler). It works with Claude Code, Codex, Gemini CLI, OpenCode, Cursor CLI and other agents that can run a
prompt from the command line. Needs Python 3.9+ and nothing else (no packages to install).

## What it costs
It is not free to run. The scheduled job wakes every 30 minutes (up to 48 times a day) and uses model calls
whenever there is something new to read.

- **The fetch step costs no tokens.** A plain script pulls the feeds and keeps only new items. If nothing is new, the
  run ends here.
- **The cheap-model check runs on new items, and busy feeds (OSV, GitHub advisories) have new items most of the
  day.** Expect it on many of the 48 daily ticks. Rough estimate, not measured: 5k to 20k input tokens per run on a
  Haiku, mini or flash class model, which is roughly 0.2M to 1M tokens a day. Mostly input; the output is short.
- **The strongest model runs only when the cheap check flags something that touches your stack.** It reads your
  files, installed versions and keys, then prepares the fix, so a single finding is roughly 30k to 150k tokens
  (estimate). Many days have none; a busy supply-chain week can have several.
- Your numbers depend on how large your stack is and which models you pick. Check `~/.security-watchdog/run.log`
  and your provider's usage page after a few days, and set a timeout or cheaper model in `config.json` if it is more
  than you want to spend.
- Optional: a GitHub token raises the GitHub API limit; it is not required.

## What it will not do
- Apply, merge, deploy, rotate or delete anything without your yes.
- Print or send your secret values. It names keys and where they live, never their contents.
- Call a failed check "safe". If a source could not be read, it says so.

## Pause or remove
Remove the schedule (the agent shows you the exact command at setup), then delete `~/.security-watchdog`.
