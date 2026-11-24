# Prune your skills every time a new model drops

You commented PRUNE, so here's the full breakdown.

**The short version.** Skills are written for the model you had when you wrote them. When a smarter model comes out, a lot of those instructions turn into dead weight: things the new model already does on its own, or loud rules that now make it overreact. So every time you switch to a new frontier model, go through your skill folders and cut back as far as you can while the output stays just as good. Measure first, cut one piece at a time, and keep what still changes the result.

## Why skills go stale

In the lesson I say: "Oftentimes your skills can be over prescriptive for new models and because new models are so much smarter. They've actually absorbed some of those instructions that you needed to give a stupider model before and you can get rid of a lot of that skill altogether."

Anthropic's own docs back this up in three ways.

**1. Old instructions can now do harm, not just nothing.** The prompting guide for Claude Fable 5.2 has a whole section called "Review prompts and harnesses designed for earlier models." It says that in Anthropic's testing, "some instructions and interventions designed for earlier models raised cost, caused side effects, or no longer had an effect" ([Prompting Claude Fable 5.2](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2)). Its checklist for switching models tells you to read "the system prompts, skills, agent files, memory files, notes, and harness text you carry over, and remove or test" what that section describes.

Some examples from that list:

- **Standing instructions to delegate** "can sit in system prompts, skills, and agent files." Remove the ones you no longer need if the model delegates too much.
- **Instructions to think less** like "answer directly without deliberating" don't stop Fable 5.2 thinking at `medium` and above. Remove them and lower effort instead.
- **Style rules for writing.** The model "follows them closely," so a hard limit like "one instruction per sentence, in 20 words or fewer" can make its prose choppy.
- **Cautions that piled up.** "Delete cautions whose reason no longer holds, and rewrite absolute rules with their scope and reason." The model treats an instruction with "never" in it as absolute.

**2. Shouting at the model backfires.** The general prompting guide says Claude Opus 4.5 and 4.6 are "more responsive to the system prompt than previous models. If your prompts were designed to reduce undertriggering on tools or skills, these models might now overtrigger. The fix is to soften any aggressive language." Instead of "CRITICAL: You MUST use this tool when...", write "Use this tool when..." It also says lines like "If in doubt, use [tool]" cause overtriggering ([Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)). That guidance names specific models, and the same page says to re-check model-specific advice against your own evals before applying it to another model. Which is exactly the point: re-check.

**3. Every line costs context.** Anthropic's skill authoring guide opens with "Concise is key" and "The context window is a public good." Its default assumption: "Claude is already very smart. Only add context Claude doesn't already have." Then it asks you to challenge every paragraph: "Does this paragraph justify its token cost?" ([Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)).

In Claude Code the cost is concrete. Once a skill loads, "its content stays in context across turns, so every line is a recurring token cost" ([skills](https://code.claude.com/docs/en/skills)). After auto-compaction, Claude Code re-attaches only the first 5,000 tokens of each invoked skill, with a combined budget of 25,000 tokens, so older skills can be dropped entirely if you've used a lot of them. And the always-loaded skill listing has a budget of 1% of the context window. When it overflows, descriptions get dropped, starting with the skills you use least ([skills](https://code.claude.com/docs/en/skills)).

A bloated skill isn't just slower. It crowds out the stuff that matters.

## Why "every new model" is the right moment

The skill authoring guide says "Skills act as additions to models, so effectiveness depends on the underlying model." It even gives the question to ask for the strongest tier: "Claude Opus (powerful reasoning): Does the Skill avoid over-explaining?" ([Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)).

So a skill isn't "done." It's tuned to one model. When the model changes, the tuning is out of date.

As of today the current lineup on Anthropic's models page is Claude Fable 5.2, Claude Opus 5.5, Claude Sonnet 5.5 and Claude Haiku 5.5 ([Models overview](https://platform.claude.com/docs/en/models/overview)). The Fable 5.2 guide points straight at this: if "your system prompt, skills, or harness was written for Claude Fable 5.1 or Claude Opus 5.5," go review it ([Prompting Claude Fable 5.2](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2)).

One catch. If the same skill also runs on a smaller model, don't prune it down to what only the biggest model can handle. The same guide says "What works perfectly for Opus might need more detail for Haiku," so test on every model you actually use it with.

## How to prune safely

The rule I follow: **same quality, fewer words.** If you can't show the quality held, you didn't prune, you just deleted.

1. **Pick 3 to 5 real tasks for the skill.** Real prompts you'd actually give it, with the input files. Anthropic's guide suggests building "three scenarios" and says evaluations "are your source of truth for measuring Skill effectiveness" ([Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)).
2. **Write down what "good" looks like for each.** A short list of expected behaviors, like the `expected_behavior` list in Anthropic's example eval.
3. **Run three baselines on the new model, each in a fresh session:** no skill, old skill, and later the pruned skill. Claude Code's docs say a fresh session matters "because leftover context from authoring the skill will mask gaps in the written instructions." For a personal or project skill, turn it off for the no-skill run by setting it to `"off"` in `skillOverrides` ([skills](https://code.claude.com/docs/en/skills)).
4. **Look at the no-skill run first.** If the new model already passes without the skill, that's the "get rid of a lot of that skill altogether" case. Maybe the whole skill goes, or only the hard facts stay.
5. **Cut one section at a time.** Delete or shorten one block, rerun the same tasks, compare. If the output holds, the cut stays. If it slips, put it back. One at a time is the only way to know which line was doing the work. The Fable 5.2 guide says the same about new additions: change one thing at a time and measure its effect and its token cost on your own tasks.
6. **Soften before you delete loud rules.** Turn "CRITICAL: You MUST..." into a plain "Do X when Y." If the behavior holds, keep the calm version.
7. **A/B the old and pruned versions on the same tasks.** Same prompts, same files, fresh sessions. Compare pass rate and tokens.
8. **Keep the old version in git.** If you track skills in a repo, the diff is your changelog and you can roll back in one command.

If you'd rather not run this loop by hand, Claude Code has two tools for it. The `skill-creator` plugin (`/plugin install skill-creator@claude-plugins-official`) stores test cases in `evals/evals.json`, runs each case in a clean subagent, benchmarks with-skill versus without-skill on pass rate, time and tokens, and has a "Version comparison" mode that "runs a blind A/B between two versions of the skill." For skills shipped in a plugin, `claude plugin eval` runs each prompt with and without the plugin and can gate CI ([skills](https://code.claude.com/docs/en/skills)).

There's also a quick first pass: `/doctor prompt-audit` looks for "instructions written for older models, references to files or commands that don't exist, and files that contradict each other." It reports findings with proposed edits and changes nothing until you say so. Point it at one skill with `/doctor prompt-audit .claude/skills/deploy` (needs Claude Code v2.1.283 or later) ([memory](https://code.claude.com/docs/en/memory)). Treat its proposals as candidates for your A/B, not as the answer.

## Keep vs cut

| Keep | Cut (or test hard) |
|---|---|
| Scripts the skill runs. Anthropic says pre-made scripts are "more reliable than generated code," save tokens and keep results consistent | Explanations of things the model already knows ("Claude already knows that," in Anthropic's own example) |
| Hard facts: your table schemas, IDs, paths, naming rules, API quirks, the "filter out test accounts" kind of rule | Generic best-practice advice any good engineer would follow anyway |
| Exact sequences for fragile steps, the "narrow bridge with cliffs on both sides" case, like migrations that must run in order | Step-by-step hand-holding for open-field tasks where "many paths lead to success" |
| Your taste and preferences the model can't guess: voice, format, what "done" means for you | ALL-CAPS, "CRITICAL", "MUST", "If in doubt, use X" written to fight undertriggering |
| Rules that still change the output in your A/B | Workarounds for old model failures you can't reproduce on the new model |
| A clear `name` and `description`, since that's what Claude uses to decide whether to trigger the skill | Old cautions and "never" rules whose reason no longer holds, standing "delegate this" lines, "don't think, just answer" lines |
| Reference files that Claude actually opens | Bundled files Claude never opens. Anthropic says an ignored file "might be unnecessary or poorly signaled" |

The left column is sourced from the [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices). The right column mixes that page with the two prompting guides linked above. Everything in the right column is a candidate, not a verdict. Your A/B decides.

## Pruning checklist

Copy this into the skill's folder or your notes when a new model ships.

```markdown
## Prune pass: <skill name>, new model: <model>

- [ ] Committed the current version so I can diff and roll back
- [ ] 3 to 5 real tasks picked, with input files
- [ ] Expected behaviors written down for each task
- [ ] Baseline run on the new model, fresh sessions: NO skill
- [ ] Baseline run on the new model, fresh sessions: OLD skill
- [ ] Noted where no-skill already matches old-skill (cut candidates)
- [ ] Softened ALL-CAPS / CRITICAL / MUST lines, reran
- [ ] Cut one section at a time, reran after each cut
- [ ] Put back any cut that made a task fail
- [ ] Scripts, schemas, IDs, paths and exact sequences kept
- [ ] Reference files Claude never opens: removed or relinked
- [ ] Final A/B: old vs pruned on the same tasks, pass rate + tokens
- [ ] Tested on every model this skill runs on, not only the newest
- [ ] SKILL.md still under 500 lines, description still says when to use it
- [ ] Committed with a message saying what was cut and why
```

## Copy-paste prompt: audit a skill folder against a new model

Run this in a fresh session on the new model, from the repo that holds the skill.

```text
You are auditing one skill folder so it fits the model you are running on now.
Skill folder: <path, e.g. .claude/skills/deploy>
The skill was last tuned on: <old model>. You are: <new model>.

Do not edit any file yet. Produce a written audit and a test plan.

1. Read every file in the folder: SKILL.md, reference files, scripts.
   Report the SKILL.md line count and list each file with one line on its job.

2. Go through SKILL.md section by section. For each section, label it:
   - KEEP-FACT: facts I can't derive myself (schemas, IDs, paths, naming
     rules, API quirks, the owner's preferences)
   - KEEP-SCRIPT: a script or exact command sequence for a fragile step
   - CUT-KNOWN: explanation or generic advice I would follow without being told
   - SOFTEN: ALL-CAPS, CRITICAL, MUST, "if in doubt, use X", or "never" rules
     without a stated scope and reason
   - CUT-STALE: workarounds for old model behavior, standing "delegate" lines,
     "don't think" lines, rigid style limits, cautions whose reason is gone
   - UNSURE: can't tell without testing
   Quote the first line of each section so I can find it.

3. List bundled files the skill never points to, or points to so vaguely
   you would not open them.

4. Propose the pruned SKILL.md as a diff. Keep every KEEP item word for word.
   Rewrite SOFTEN items as plain "Do X when Y" with the reason.

5. Write a before/after test plan:
   - 3 to 5 realistic prompts this skill should handle, with any input files
   - expected behaviors for each, as a short checklist
   - three arms, each prompt in a fresh session: no skill, old skill,
     pruned skill
   - the cut order: which section to remove first, second, third,
     so each cut can be tested on its own
   - what result would make us put a cut back

6. End with: estimated lines removed, the 3 riskiest cuts, and which other
   models this skill also runs on that the pruned version must still pass.
```

The point of step 5 is that the agent's opinion isn't the proof. The test run is.

## What goes wrong

- **Pruning by vibes.** You cut half the skill, it "feels fine," and three weeks later a rare case breaks. No baseline, no proof.
- **Testing in the session where you edited the skill.** The leftover context hides the gap. Claude Code's docs say to use a fresh session for exactly this reason ([skills](https://code.claude.com/docs/en/skills)).
- **Deleting the facts with the fluff.** The model got smarter, not psychic. It still doesn't know your schema or your deploy order.
- **Deleting scripts because "the model can write that now."** It can, but the script is more reliable, cheaper and the same every time ([Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)).
- **Pruning for the top model only.** The skill also runs on your fast, cheap model in a subagent, and now it fails there.
- **Swapping one loud rule for another.** If a calm rule doesn't hold, fix the wording or the description. Don't go back to CAPS by reflex.
- **Cutting many sections at once.** Something slips and you don't know which cut did it.
- **Pruning once and forgetting.** Next model, same job. Put it on your list for every release.

## Sources

| Claim | Source |
|---|---|
| Instructions designed for earlier models "raised cost, caused side effects, or no longer had an effect"; review system prompts, skills, agent files, memory and notes when switching; delegation, think-less, style-rule and piled-up-caution examples; "never" read as absolute; change one thing at a time and measure on your own tasks; review skills written for Fable 5.1 or Opus 5.5 | [Prompting Claude Fable 5.2](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2) |
| Opus 4.5 and 4.6 more responsive to the system prompt, may overtrigger; soften "CRITICAL: You MUST"; "If in doubt, use [tool]" causes overtriggering; re-check model-specific advice with your own evals | [Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| "Concise is key"; "Claude is already very smart"; "Only add context Claude doesn't already have"; "Does this paragraph justify its token cost?"; degrees of freedom (narrow bridge vs open field); test with all models, "Does the Skill avoid over-explaining?"; build evaluations first, three scenarios, baseline without the skill; utility scripts more reliable than generated code; ignored files may be unnecessary; SKILL.md under 500 lines | [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) |
| Loaded skill content stays in context, "every line is a recurring token cost"; compaction re-attaches the first 5,000 tokens per skill, 25,000 combined; listing budget 1% of the context window; baseline in a fresh session with and without the skill; `skillOverrides` `"off"`; skill-creator plugin with blind A/B version comparison; `claude plugin eval` | [Claude Code skills](https://code.claude.com/docs/en/skills) |
| `/doctor prompt-audit` finds instructions written for older models, missing files or commands, contradictions; takes a path; v2.1.283 or later | [Claude Code memory](https://code.claude.com/docs/en/memory) |
| Current models: Claude Fable 5.2, Claude Opus 5.5, Claude Sonnet 5.5, Claude Haiku 5.5 | [Models overview](https://platform.claude.com/docs/en/models/overview) |

Docs checked on Nov 24, 2026. Model names and Claude Code features change, so check the links before you rely on a detail.

## Want more like this?

More agent breakdowns and the full lessons are inside my Skool community, **Agent Architects**: https://www.skool.com/agent-architects
