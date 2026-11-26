# Context budget: the yardsticks

Quoted from Anthropic docs, fetched 2026-11-10. Re-fetch when a cycle runs more than a few months later, and
update this file if a number changed. Use only these numbers; do not invent thresholds.

Sources:
- [BP] https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- [SK] https://code.claude.com/docs/en/skills
- [MEM] https://code.claude.com/docs/en/memory

## Skills

| Check | Yardstick | Source |
|---|---|---|
| SKILL.md body length | "Keep the `SKILL.md` body under 500 lines for optimal performance." | BP |
| Splitting | "Split content into separate files when approaching this limit." | BP |
| Reference depth | "Keep references one level deep from `SKILL.md`." Nested references get partial reads such as `head -100`. | BP |
| Long reference files | "For reference files longer than 100 lines, include a table of contents at the top." | BP |
| name | "Maximum 64 characters", lowercase letters, numbers and hyphens | BP |
| description | "Maximum 1,024 characters", "Should describe what the Skill does and when to use it", "Always write in third person" | BP |
| Listing truncation | "the combined `description` and `when_to_use` text is truncated at 1,536 characters in the skill listing". "Put the key use case first" | SK |
| Recurring cost | "Once a skill loads, its content stays in context across turns, so every line is a recurring token cost." | SK |
| After compaction | Re-attached skills keep "the first 5,000 tokens of each" within "a combined budget of 25,000 tokens" | SK |
| Old content | "Don't include information that will become outdated"; keep superseded material in an "old patterns" section | BP |
| Repeated reads | "If Claude repeatedly reads the same file, consider whether that content should be in the main `SKILL.md` instead." | BP |
| Ignored files | "If Claude never accesses a bundled file, it might be unnecessary or poorly signaled" | BP |
| Scripts | Scripts run "without loading their full contents into context. Only the script's output consumes tokens." | BP |

## Rules and memory files

| Check | Yardstick | Source |
|---|---|---|
| CLAUDE.md size | "target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence." | MEM |
| Imports | `@path` imports "help you organize a long file but don't reduce its context cost"; max depth "four hops" | MEM |
| Auto memory index | "The first 200 lines of `MEMORY.md`, or the first 25KB, whichever comes first, are loaded at the start of every conversation. Content beyond that threshold is not loaded" | MEM |
| Index hygiene | "keep one line per entry, move detail into topic files, and merge or drop stale entries" | MEM |
| Enforcement | CLAUDE.md is context, "not enforced configuration. To block an action regardless of what Claude decides, use a PreToolUse hook" | MEM |

The 200-line / 25KB truncation applies to the Claude Code auto-memory `MEMORY.md`. A framework index that the
agent reads itself (for example an agent-root `MEMORY.md` listed as a startup file) is not truncated, but it
costs its full size every session; apply the same hygiene yardstick and say which case it is.

## What to look for in transcripts

- A skill file read in several `sed -n` chunks, or re-read 3+ times in a session: too long to hold, or the
  needed part is buried. Pair with lint's line count.
- One reference file read in most triggers: move its core into SKILL.md. One never read: cut or signal it.
- The same rule in two skills: keep one copy, point to it from the other.
- Large tool outputs (`tokens.md`): prefer `| head`, `--json` plus a field filter, or a script that prints a summary.
- Runs of no-op turns from polls and ticks: give the cron an exit condition or a quiet mode where the script prints
  nothing and the agent ends the turn without narration.
