# Claude connectors now ship skills (MCP)

You commented MCP, so here's the full breakdown.

**The short version.** MCP turned two this week, and Anthropic shipped the biggest set of upgrades since launch. An MCP server can now hand Claude three new things on top of its tools: **skills** (the playbook for using those tools), **tasks** (long jobs that run on the server while Claude keeps working) and **elicitation** (the server stops and asks you before something risky). Skills over MCP is a **public beta**. Tasks and Elicitation are **GA** on Pro, Max and Ultra. File uploads to MCP servers are **rolling out soon** ([Anthropic launch](https://claude.com/resources/articles/skills-over-mcp-tasks-and-more)). Everything below was checked against Anthropic's and the MCP project's own docs on Nov 25, 2026.

## MCP turns two

| | |
|---|---|
| Open-sourced | Nov 25, 2024 ([MCP blog](https://blog.modelcontextprotocol.io/posts/mcp-turns-two/)) |
| Monthly SDK downloads | "over 700 million" ([Anthropic](https://claude.com/resources/articles/skills-over-mcp-tasks-and-more)), up from "more than 90 million" a year earlier ([MCP blog](https://blog.modelcontextprotocol.io/posts/mcp-turns-two/)) |
| Connectors for Claude | "over 10,000 MCP connectors for Claude" ([Anthropic](https://claude.com/resources/articles/skills-over-mcp-tasks-and-more)) |
| Contributors | "more than 2,500 unique contributors" ([MCP blog](https://blog.modelcontextprotocol.io/posts/mcp-turns-two/)) |
| Governance | Moved to the Agentic AI Foundation (Linux Foundation) in Dec 2025 ([MCP blog](https://blog.modelcontextprotocol.io/posts/mcp-turns-two/)) |

Anthropic's framing: Claude should treat a server "more like another agent: learning from it, delegating to it, and exchanging input and files along the way."

## What shipped

| Feature | What it does | Status |
|---|---|---|
| **Skills over MCP** | The server ships playbooks next to its tools. Claude loads one only when it needs it | **Public beta** in Claude and Claude Code. Pro, Max, Ultra on by default. Team: an org Owner turns it on. Enterprise: coming soon |
| **Tasks** | The server takes a long job, hands back a task ID and keeps working. Claude carries on and picks up the result later | **GA** on Pro, Max, Ultra. Rolling out to Team and Enterprise |
| **Elicitation** | The server pauses and asks you for input through a form or a link, then continues | **GA** on Pro, Max, Ultra. Rolling out to Team and Enterprise |
| **File uploads** | Send files to an MCP server without passing them through the context window | **Rolling out soon**. Not usable yet |

Source: [Anthropic launch](https://claude.com/resources/articles/skills-over-mcp-tasks-and-more).

## 1. Skills over MCP (public beta)

Tool names and descriptions tell Claude *what* a server can do, not *how* to handle a real job. Skills fill that gap: "best practices, step-by-step workflows, or playbooks customized to a user's account or organization" ([Anthropic](https://claude.com/resources/articles/skills-over-mcp-tasks-and-more)).

**Who ships them** (as Anthropic describes them):

- **Shopify:** designs and updates a merchant's online store end to end.
- **HubSpot:** onboards customers and sets them up in Claude.
- **Atlassian:** brings organizational context for insights and work analysis.
- **Carta (coming soon):** drafts and issues equity from an uploaded document.

**How it works under the hood** ([MCP Skills overview](https://modelcontextprotocol.io/extensions/skills/overview), [spec](https://github.com/modelcontextprotocol/ext-skills/blob/main/specification/beta/skills.mdx)):

- A skill is the same thing you already know: a folder with a `SKILL.md` (name + description in the frontmatter) plus optional files.
- The server lists its skills with `skills/list`. Each entry carries the full file list with a size and a SHA-256 digest per file.
- **Loaded on demand.** Before a skill loads, Claude only sees its name, description and which server it came from. The files are fetched when the skill is actually used. Anthropic: Claude "loads a skill only when it's needed, keeping context use low."
- **Updates come from the server.** "Skills update together with the server", so there's nothing extra to install. The server can also serve different skills per account or org.
- **The digest is not a safety stamp.** It proves the bytes match what the server listed, not that the content is safe.

**Where you see them in Claude Code** ([Claude Code docs](https://code.claude.com/docs/en/mcp)):

- Type `/` or run `/skills`. They show as `<server>:<skill>`, for example `/docs:pdf report.pdf`.
- claude.ai connectors get a prefix, for example `claude_ai_Docs:pdf` for a connector named Docs.
- Use one by asking Claude, or type its name as a command yourself.

## 2. Tasks (GA)

Before, a tool call had to finish before Claude could move on. On claude.ai and Desktop a tool call times out at 240 seconds ([connector docs](https://claude.com/docs/connectors/building/index.md)). With Tasks, a server can run slow jobs "or even full agent loops" while Claude keeps working ([Anthropic](https://claude.com/resources/articles/skills-over-mcp-tasks-and-more)).

**Who ships them:** **ZoomInfo** uses Tasks for deeper account and contact research that used to take several prompts.

**How it works** ([MCP Tasks overview](https://modelcontextprotocol.io/extensions/tasks/overview)): Claude calls the tool, the server answers right away with a task ID, and Claude checks back with `tasks/get` until it's `completed` or `failed`. If the server needs something from you mid-job, the status becomes `input_required`. Cancelling is a request: the server may still finish.

**What you see in Claude Code** ([Claude Code docs](https://code.claude.com/docs/en/mcp)):

- The footer shows a count like `1 MCP task`, and the transcript later says `MCP task ... completed.` The result goes to Claude, so ask Claude for it.
- Stop one from `/tasks` (select it, press `x`) or ask Claude. `Esc` does not stop a background task.
- **Remote server:** the task keeps running after you quit. Come back to the **same session** (`claude -c`, `claude -r` or `/resume`) and Claude picks up the result if the server still has it.
- **Local (stdio) server:** it stops when Claude Code exits, even if `/tasks` says the task is still running.

## 3. Elicitation (GA)

A server can stop mid-request and ask you, through a **form** or a **link**, then carry on. Anthropic frames it for things like spending money or deleting data ([Anthropic](https://claude.com/resources/articles/skills-over-mcp-tasks-and-more)).

**Who ships it:**

- **Supabase:** confirms costs before creating a paid project and before running destructive SQL.
- **Railway:** asks before destructive changes like removing a service.
- **GitHub:** makes you type the repository name before an agent deletes it.

**Two modes** ([Elicitation spec](https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation)):

- **Form:** simple fields (text, numbers, yes/no, pick lists). Never for passwords, API keys or payment details.
- **Link:** opens a page in your browser. What you type there never passes through Claude. This is the one for sensitive input, sign-ins and payments.

In Claude Code there's nothing to set up: a dialog appears when a server asks ([Claude Code docs](https://code.claude.com/docs/en/mcp)).

## Checklist: get MCP skills working in Claude Code

From the [Claude Code MCP docs](https://code.claude.com/docs/en/mcp) and the [changelog](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md):

- [ ] **Claude Code 2.1.332 or later.** The docs say 2.1.331, the changelog lists "Added skills from MCP servers (beta)" under 2.1.332. Run `claude --version`.
- [ ] **Model:** a Fable model, or Opus 4.8, Sonnet 5, Haiku 5.5 or later.
- [ ] **Login:** a Pro, Max or Ultra subscription login. claude.ai connectors only load on a claude.ai subscription login. API key and Console logins are still rolling out.
- [ ] **Direct connection to Anthropic** with feature-flag fetching on. If `/status` shows a Features row naming a variable (for example `DISABLE_TELEMETRY`), unset it and restart.
- [ ] **Server on MCP revision 2026-07-28 or later.** Open `/mcp`, pick the server and look for a **Protocol** row. No Protocol row, no skills.
- [ ] **Team:** an org Owner turns on **Skills over MCP** in Organization settings > Connectors, and the org **Skills** setting must be on too.
- [ ] **Run `/skills`** and confirm the server's skills are listed before you rely on them. During the beta Anthropic keeps skills off for some connectors, and no setting changes that.

**Not supported for skills:** `claude -p`, the Agent SDK, GitHub Actions, cloud sessions, `claude remote-control` server mode, Bedrock/Vertex and other cloud providers, a custom `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN` or `apiKeyHelper`, connectors and Desktop extensions inside the Desktop app, and HIPAA or zero-data-retention orgs.

**Tasks:** need Claude Code 2.1.304 or later (just update to the latest), a server that supports tasks on revision 2026-07-28, and an interactive session. A one-shot `claude -p` gets no MCP tasks.

## Trust before you use one

Skills can tell Claude to run code, so treat them like any other code you didn't write ([Claude Code docs](https://code.claude.com/docs/en/mcp)):

- **Default (auto) mode:** no prompt. A classifier decides whether a skill loads, without reading it.
- **Manual mode:** you get a prompt. **Allow this version** approves that exact version. If the server changes any file, it asks again. Remove approvals in `/permissions`.
- **Block a server's skills:** deny `Skill(mcp__<server>__*)` in `/permissions`. Deny `Skill(<server>:<skill>)` blocks one skill.
- **Scanning:** Anthropic scans skills only from claude.ai Directory connectors (and Enterprise custom connectors with scanning on). Servers you add with `claude mcp add` are not scanned.
- The docs, verbatim: "Skills can direct Claude to run code. Servers can change skills at any time. Add only servers you trust."

## Catches

- **Skills over MCP is a beta.** Tasks and Elicitation are GA. File uploads aren't out yet.
- **Enterprise doesn't have Skills over MCP yet.** Anthropic says "coming soon."
- **The vendor writes the playbook.** It can be tailored to your account or org only if the vendor builds it that way. And they can change it any time.
- **No speed or token numbers** were published for Skills over MCP. The "more than 85%" context saving in the launch post is for Tool search, a different feature.
- **Name your own test server something unique.** Skills show as `<server>:<skill>`, so a server named like an installed plugin can show the same names.
- **It's an open standard, not Claude-only.** VS Code (GitHub Copilot) supports MCP skills too ([implementations list](https://github.com/modelcontextprotocol/ext-skills/blob/main/docs/implementations.md)).

## My take

If you built your own skills around an MCP server, check whether the vendor now ships one. Theirs updates with the server, yours doesn't. And together with [Claude Code code mode](../claude-code-code-mode/), MCP has mostly caught up with CLI tools on cost and speed. There are still pros and cons both ways, but it's worth a rethink.

## Sources

- [MCP servers can now ship skills, run tasks, and more with Claude](https://claude.com/resources/articles/skills-over-mcp-tasks-and-more), Anthropic, Nov 24, 2026
- [Two Years of MCP Builders](https://blog.modelcontextprotocol.io/posts/mcp-turns-two/), MCP blog, Nov 24, 2026
- [Connect Claude Code to tools via MCP](https://code.claude.com/docs/en/mcp), Claude Code docs (skills, tasks, elicitation)
- [Skills extension overview](https://modelcontextprotocol.io/extensions/skills/overview) and [spec (beta)](https://github.com/modelcontextprotocol/ext-skills/blob/main/specification/beta/skills.mdx), Model Context Protocol
- [Tasks extension overview](https://modelcontextprotocol.io/extensions/tasks/overview), Model Context Protocol
- [Elicitation spec, revision 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation), Model Context Protocol
- [Claude Code changelog](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)
- [Building connectors](https://claude.com/docs/connectors/building/index.md), Claude docs
- [Skills over MCP implementations](https://github.com/modelcontextprotocol/ext-skills/blob/main/docs/implementations.md), community-maintained list
