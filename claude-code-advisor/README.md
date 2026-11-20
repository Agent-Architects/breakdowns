# Claude Code /advisor: when your agent should ask a smarter model

You commented "advisor", so here's the full breakdown, plus a skill you can drop in so your agent knows exactly when to use it.

Most people think you have to pick one model: run the big one all day and burn through your limits, or run a cheaper one and watch it get stuck. The advisor tool lets you do both. Your main model does the routine work and, at the moments that matter, consults a second, stronger model for guidance.

*Checked against the official Claude Code docs on November 20, 2026. Links at the bottom. The advisor is experimental, so details may change.*

---

## How it works

- The advisor is a tool that runs on Anthropic's side. Your main model can call it mid-task.
- When called, the advisor reads the **full conversation**, including every tool call and result, and sends back guidance. Claude then continues with that guidance.
- **Claude decides when to call it**, usually before committing to an approach, when an error keeps coming back, and before declaring a task done. There is no setting to cap or force calls, but you can ask for it in your prompt: "consult the advisor before you continue".
- If the advice contradicts what Claude can see (a failing step, the actual file contents), Claude raises the conflict instead of following the advice blindly.

## Setup

```text
/advisor opus          # set the advisor (saved as advisorModel in your user settings)
/advisor               # open the picker, or print the current advisor outside the terminal UI
/advisor off           # turn it off
```

Other ways to set it:

```json
// settings file
{ "advisorModel": "opus" }
```

```bash
claude --advisor opus   # this session only, doesn't change your saved setting
```

**The advisor must be at least as strong as your main model.** Sonnet with an Opus advisor works. Opus with a Sonnet advisor does not; Claude Code won't attach a weaker advisor. Haiku 4.5 can call an advisor but can't be one. Subagents inherit your advisor and apply the same check against their own model.

**Where it works:** the Anthropic API, Claude Platform on AWS and Claude Models on Google Cloud (Anthropic managed). Not on Amazon Bedrock, Google Cloud's Agent Platform or Microsoft Foundry. Through an LLM gateway it only works if the gateway forwards the request intact.

**What you'll see:** an `Advising` line while it runs, then whether it reviewed, declined or was unavailable. Press `Ctrl+O` to read the guidance.

**Cost:** each call reads the whole conversation at the advisor model's rates (on a subscription, it counts toward your plan's limits). Turning the advisor on or off does not break your main prompt cache, but the advisor's own read is not cached, so every call re-reads the transcript. That's why *when* it gets called matters.

**Common pairings:** Sonnet main + Opus advisor (routine work cheap, planning and hard failures to Opus), Haiku main + Opus advisor (lowest cost with strong planning), Opus main + Opus advisor (a second opinion on high-stakes work).

---

## When should a weaker model consult its advisor?

**Default: don't.** Every call re-reads the whole conversation at the stronger model's rates. The advisor pays off at a few expensive moments, not as a habit. On long or high-stakes work, call it at these four moments only:

1. **Once before committing to the plan** on a long task (after you've read enough to have a real plan).
2. **Before an irreversible or outward-facing action** with real blast radius: delete, migrate, deploy, send, publish, pay, switch on a schedule.
3. **After the same problem has beaten you twice.** One failure is normal; two means you're missing something.
4. **Once before declaring a long task done.**

**Budget:** 0 calls on short tasks, about 1 to 3 on a long one. If you hit 3 on one task, the plan or the request is the problem: ask the user.

**Never for:** routine edits, lookups, anything you can verify by running it once, a single failure you haven't debugged yet, or reassurance.

**Examples:**

- **Software development:** before committing to an architecture on a new feature, before a migration, when a bug survived two fixes.
- **Knowledge work:** before a recommendation when your key sources disagree, before sending a final public or client document.
- **Automation building:** before switching on a workflow that sends, posts, pays or deletes on its own, when a live workflow keeps failing after two fixes.

---

## The skill: teach your agent when to use it

Copy [`skills/when-to-consult-advisor/SKILL.md`](skills/when-to-consult-advisor/SKILL.md) into your project's `.claude/skills/when-to-consult-advisor/` folder (or `~/.claude/skills/` for every project). Its description lists the trigger moments, so the model loads it right when it's about to make one of these calls.

Or just paste this into your `CLAUDE.md`:

```markdown
## Advisor
Default: don't call it. Only on long or high-stakes work: once before committing to the plan,
before an irreversible or outward-facing action, after the same problem beat you twice, and once
before declaring done. About 1 to 3 calls per long task, 0 on short ones.
```

### Paste-in prompt for your agent

```text
Install the "when-to-consult-advisor" skill from
https://github.com/Agent-Architects/breakdowns/tree/main/claude-code-advisor/skills/when-to-consult-advisor
into .claude/skills/, add the short Advisor section from that page to my CLAUDE.md,
then tell me to type /advisor opus to switch the advisor on.
```

---

## Sources

- Claude Code docs, advisor tool: https://code.claude.com/docs/en/advisor
- Claude API docs, advisor tool: https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool
- Claude Code docs, model configuration: https://code.claude.com/docs/en/model-config

Want the full video lessons? They're inside my Skool community, Agent Architects: https://www.skool.com/agent-architects
