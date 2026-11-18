# Claude Code code mode: what it is and how to turn it on

You commented "code mode", so here's the full breakdown.

Normally Claude Code calls one tool at a time: it asks for a Bash command or a file read, waits for the result, reads it, then decides the next step. Code mode flips that. Claude writes a short piece of JavaScript that makes the tool calls, and Claude Code runs that code in your session. One script can run commands in parallel, feed one result into the next call, and hand back only the part of the output Claude needs to read.

It is experimental and off by default.

## Turn it on

Either start Claude Code with the environment variable:

```bash
CLAUDE_CODE_EXPERIMENTAL_CODE_MODE=1 claude
```

or add it to the `env` block of your user settings, `~/.claude/settings.json`:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_CODE_MODE": "1"
  }
}
```

Claude Code asks you to confirm the first time. Project settings files cannot turn it on. To turn it off, remove the variable or set it to `0`.

## What it lets Claude do

1. **Edit many files in one step.** A change that repeats across many files runs as one loop instead of one call per file.
2. **Filter a search before Claude reads it.** Search the repo and return only the lines that matter, not the whole output.
3. **Run independent commands at the same time.** Lint, typecheck and tests in parallel.
4. **Chain results.** Find a file with one call, edit it with the next, in the same script.
5. **Run the tests and look only at what failed.** The script returns the failing part, not the full log.
6. **Treat a failing command as data.** A failing test comes back with its output instead of stopping the run.
7. **Agent teammates use it too.** In agent teams, teammates run in code mode (in-process display mode).

Long builds can also run in the background for up to two hours while you keep talking to Claude (start the session in auto or `bypassPermissions` mode for that).

## Safety: your rules still apply

- Every tool call inside the code still goes through your `deny` and `ask` permission rules and your `PreToolUse` hooks, under the tool's usual name (for example `Bash`).
- In auto mode, the classifier reviews each piece of code before it runs, not each call. It cannot see values computed while the code runs (like a path taken from search output), so keep rules or hooks for calls you must control.
- In other modes, the code starts without a review and you are prompted for each call that would normally prompt.

## Requirements and limits

- Claude Code v2.1.323 or later (agent teams need v2.1.326 or later), native build, a Claude subscription or Console account.
- Models: Claude Opus 5.5, Sonnet 5.5, Haiku 5.5 or Fable 5.2.
- Interactive terminal only: not `claude -p`, the Agent SDK, the VS Code panel, the Desktop app or cloud sessions.
- Not available through a gateway, Bedrock, Google Cloud, Microsoft Foundry, or on HIPAA or zero-data-retention organizations.
- While it is on: no Remote Control, Claude in Chrome or computer use. Code you wait on stops after ten minutes.
- There are no official speed or token numbers for code mode yet.

## Sources

- Claude Code docs, Code Mode: https://code.claude.com/docs/en/code-mode
- Claude Code changelog (2.1.323 "Added Code Mode", 2.1.326, 2.1.327): https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md
- Permission modes: https://code.claude.com/docs/en/permission-modes
- Hooks: https://code.claude.com/docs/en/hooks
- Agent teams: https://code.claude.com/docs/en/agent-teams

Checked 2026-11-18 against Claude Code 2.1.327.
