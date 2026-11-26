# Scheduling the cycle

The skill never creates its own schedule. You set one up, or ask your agent to, through your tool's normal
scheduler. Suggested cadence:

| Scope | Cadence | Window |
|---|---|---|
| Each daily skill | Weekly, rotate one or two skills per run | `--since 7` |
| All daily skills, summary only | Monthly | `--since 30`, `--max 20` |
| One skill, ad hoc | After a correction like "add this to the skill" or "you have a skill for this" | `--since 3` |

The scheduled prompt should say: run the self-improve skill for <skill>, write the report to <folder>, give me
the top 3 findings, apply nothing.

Exact setup steps for Claude Code Desktop, `claude -p` with the OS scheduler, Codex and other agent
schedulers are in the pack's `schedule.md`.

Keep reports in one folder and name them by date, so each cycle can diff against the last one: a finding that
appears twice is a candidate for a script check or a hook.
