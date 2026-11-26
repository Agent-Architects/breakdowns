# Judging hooks

## What the script sees

Claude Code records hook runs as `attachment` entries (`hook_success`, `hook_cancelled`,
`hook_permission_decision`, and others) and hook blocks as tool results containing `<Event>:<Tool> hook error:`.
`retro.py hooks` classifies each run:

| Outcome | Meaning |
|---|---|
| silent | ran, printed nothing |
| rewrite | changed the tool input (`updatedInput`), e.g. a command proxy |
| context | added context for the model |
| block | denied or blocked the call |
| deny | a PermissionRequest hook denied |
| timeout / cancelled | did not finish in time |
| nonzero | exited non-zero without a decision |

Codex rollouts do not record hook runs in the same way; for Codex, judge from tool errors and the human's reaction.

## Rating a firing

For each block, error or timeout, read the blocked call (`on:` line) and the next actions:

- **Right:** the call was risky and the agent took the safe path, or the human agreed.
- **Wrong:** the call did not do what the hook guards against (false positive), or the agent had to work around
  it to do approved work. Note the workaround: a hook that teaches agents to rephrase commands is worse than none.
- **Slow:** timeouts on Stop or PreToolUse hooks delay every turn. Count them.

## Missing hooks

Candidates come from three places:

1. `hooks.md` "risky calls with no hook decision" (push, force, reset --hard, rm -rf outside /tmp, .env, POST or
   DELETE requests, publish, repo create, pm2 delete). Many are fine. Look for ones the human objected to, or that
   had no approval in the turn before.
2. "Never" and "always" corrections in `signals.md` that were repeated. A rule broken twice is a hook candidate.
3. Skill rules that kept being "not reached" over two cycles. A script check the skill runs can enforce them more
   cheaply than a global hook.

Propose the hook as: event, matcher, condition, decision (block, ask, or add context), message, and the false
positives you expect. Hook changes are live-system changes: they need the owner's explicit approval.
