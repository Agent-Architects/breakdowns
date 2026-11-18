# Search every conversation your coding agents ever had

You commented "cass", so here's the full breakdown.

cass (coding_agent_session_search) is an open source tool by Jeffrey Emanuel. It indexes the session transcripts of your coding agents and gives you one search box. Repo: github.com/Dicklesworthstone/coding_agent_session_search

## What it is
Claude Code, Codex, Cursor, Grok, Gemini CLI, OpenCode, Hermes, Aider and 20+ more each store sessions in their own folder or database. cass reads them, copies the message text into one local SQLite database, and builds a search index on top. A search never opens the agent. It queries the copy.

## Why
- Find the conversation where something got fixed, across every agent, with a few words.
- See which agent, which project and which day.
- Your agents can search it too (JSON output), so one agent can reuse what another already solved.
- It is transcript search, not a memory layer. It does not decide what agents should remember.

## Install and first search
```bash
brew install dicklesworthstone/tap/cass     # Apple Silicon Mac and Linux
cass                                         # opens the terminal UI, first launch builds the index
```
The README also offers an install script (`install.sh`). The first index can take a while on a big history.

Never run bare `cass` inside an agent, it opens the interactive UI. Agents and scripts use:
```bash
cass search "ffmpeg crop" --mode lexical --no-maintenance --robot --fields minimal --limit 5
```
`--no-maintenance` stops the search from starting an index in the background. Semantic search is optional: `cass models install` downloads a small model (about 90 MB).

## Cross-computer: one search across all your machines (what I show in the video)

The way I make this cross-computer: pick one computer as the home computer (in my setup that is the one running my ADE, Cortext), install cass on every computer, and have the home computer pull every other computer's agent sessions into its own index over Tailscale. Then one search on the home computer covers every machine.

cass has this built in ("Remote Sources"). It connects over plain SSH and copies the session files with rsync, keeping track of which machine each one came from.

```bash
# on the home computer: find your other machines (SSH config + online Tailscale peers)
cass sources discover --tailscale --json

# guided setup: pick hosts, optionally install cass on them, index, write sources.toml, then sync
cass sources setup --tailscale

# later, pull new sessions from every remote into the home index
cass sources sync
```

- Tailscale here is only the network. cass uses ordinary SSH to each machine's Tailscale IP, so your SSH keys, host-key checks and Tailscale ACLs still apply. It does not log in to Tailscale or change your SSH config.
- Remote machines are listed in `sources.toml`, next to cass's config file.
- `cass sources setup --dry-run` shows what it would do without changing anything.

## Safety
- Local: the index lives on your machine (on macOS, under ~/Library/Application Support). The indexer uploads nothing.
- Redaction: secrets in message text are redacted before they reach the database and index. On by default.
- Not covered: your original session files stay as they are, and cass also keeps a raw mirror (an unredacted copy of the source files) by default. Set `CASS_RAW_MIRROR=0` to turn it off.
- The database is a second copy of everything pasted into a session. Treat that folder like the transcripts themselves.
- Status: the README calls it alpha. Check `cass --version` before relying on the output format.
- License: MIT with an OpenAI/Anthropic rider. The rider denies rights to OpenAI, Anthropic and anyone acting for them. If that could apply to you or your employer, read the LICENSE file first. Not legal advice.

Checked against the cass source (commit f94ea2d) and GitHub on 2026-11-14 (release v0.11.0). Cross-computer section checked against the cass README on 2026-11-18 (commit cd5301a).

## Sources

- cass repo: https://github.com/Dicklesworthstone/coding_agent_session_search
