# Fable prompt: 10 changes to test with Claude Fable 5.2

Your Fable 5.2 agent keeps stopping, asks for permission on routine work, or burns through tokens. Start with the tip that matches the problem.

The first six tips follow the video in order. Every prompt below is an original example you can adapt. Test each change on your own tasks. Anthropic's reported tests describe its setups, not guaranteed results for yours.

| In the video | Find it here |
|---|---|
| Ownership sentence | [Tip 1](#1-decide-whether-you-want-ownership) |
| Finishing work | [Tip 2](#2-define-what-finished-means) |
| Lower effort | [Tip 3](#3-turn-down-effort-in-the-settings) |
| Cost-aware subagents | [Tip 4](#4-give-delegation-a-cost-test) |
| Stale never-rules | [Tip 5](#5-audit-old-never-rules) |
| Precise approval rules | [Tip 6](#6-name-the-actions-that-need-approval) |

Apply system-prompt or tool-description changes in a fresh conversation. For an ongoing run, put new instructions in the newest turn. See [preserved thinking](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking).

## 1. Decide whether you want ownership

Ownership framing encourages structural changes. Omit it for minimal edits; a separate scope rule doesn't cancel it. Review the diff. [Source: code ownership](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2).

Example for a repo where you want ongoing maintenance:

```text
You own maintenance of this shopping-cart service. Consolidate repeated price validation as you add the requested discount feature. Preserve existing checkout behavior.
```

For a small patch, request the patch directly and leave ownership framing out.

## 2. Define what finished means

Distinguish routine obstacles from deliberate barriers. Anthropic's medium-effort session replay roughly halved unfinished sessions with doable work, using about 30% more output tokens. [Source: finishing work](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2).

```text
Deliver the requested CSV importer and verify it against the sample file. Diagnose ordinary tool errors and continue when safe. Report missing access or protected files as blockers. Keep required confirmation for destructive actions.
```

## 3. Turn down effort in the settings

A think-less instruction didn't suppress thinking at medium or above in Anthropic's tests. [Source: effort calibration](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2). Effort is the main thinking-depth control; `high` is Fable 5.2's API default. Compare quality, latency and tokens at lower levels. [Effort docs](https://platform.claude.com/docs/en/build-with-claude/effort).

Concrete Messages API request fragment for a trial at medium effort:

```json
{"output_config": {"effort": "medium"}}
```

Run the same task and acceptance check at `high` and `medium` before picking one. Ask for shorter replies separately.

## 4. Give delegation a cost test

Audit standing delegation instructions first. If needed, put actual subagent cost, delegation criteria and briefing requirements in the tool description. [Source: subagents](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2).

```text
Subagents consume additional tokens. Check the configured child model before delegating. Delegate an independent task only when the expected benefit justifies that cost. Give it the inputs, boundaries and expected output.
```

The video calls this usage-limit awareness. Make it concrete in your harness: record child usage and review whether that delegation helped. Don't guess what each child costs.

## 5. Audit old never-rules

Stale cautions can suppress routine work. Put valid exceptions inside the rule; only allow retries safe to repeat. [Source: accumulated caution](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2).

Example replacement for an old blanket retry ban:

```text
Retry a read-only status lookup after a temporary timeout. Before repeating a write, check whether it already succeeded. Ask before any retry that could duplicate a payment or message.
```

## 6. Name the actions that need approval

Approval rules need exact actions and boundaries. [Source: approvals](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2).

Example for a local documentation task:

```text
You may read project files, edit the requested documentation and check its links. Ask before publishing the page, sending messages to other people or deleting user files.
```

## 7. Make each approval specific

Name the approved action and target. [Source: approvals](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2).

```text
Yes, run the reviewed migration on staging-db only. Production changes still need separate approval.
```

This is the reply you give the agent after reviewing its proposed migration.

## 8. Test removing in-prompt token counters

Anthropic found lower cost with equivalent performance after removing large prompt budgets in coding tests at high and xhigh. [Source: migration instructions](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2).

Concrete harness change to test:

```text
Omit the prompt line that reports the task's remaining token allowance.
```

Keep your actual runtime limits and cost monitoring. API task budgets are a separate beta control; this finding doesn't evaluate them. [Task-budget docs](https://platform.claude.com/docs/en/build-with-claude/task-budgets).

## 9. Keep conversation history append-only

Preserved thinking depends on the earlier conversation prefix. Changing system text, tools or an earlier message can invalidate later thinking and cause a default Messages API rejection. Keep returned thinking blocks unchanged. Use supported context editing or compaction when shortening history. [Preserved-thinking docs](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking).

Original harness sketch:

```python
# Keep this session's original system and tool definitions.
# Add new requirements at the end, rather than rewriting a prior turn.
messages.append({"role": "user", "content": "Also report rows rejected by the importer."})
```

If you need different system instructions, start a fresh conversation.

## 10. Check the client before fixing a silent agent

Progress updates arrive in thinking blocks. At the default `omitted` display they have no readable text. The beta `updates` display exposes progress summaries; render the non-empty thinking blocks. Updates can still be skipped. [Thinking docs](https://platform.claude.com/docs/en/build-with-claude/thinking).

Concrete Claude API request settings:

```text
anthropic-beta: thinking-display-updates-2026-08-18
```

```json
{"thinking": {"type": "adaptive", "display": "updates"}}
```

These are request fragments, not a complete API call. Preserve the returned blocks when continuing the conversation.

Try one change on a task you can score. Record whether it finished correctly, what changed in the diff, how long it took and how many tokens it used. Keep the change only when that tradeoff works for you.

Checked against Anthropic's official docs on November 11, 2026. For the full model-specific guidance, read [Prompting Claude Fable 5.2](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2).
