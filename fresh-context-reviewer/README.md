# Give your reviewer agent fresh context (and maybe a different model)

You commented REVIEWER, so here's the full breakdown.

**The short version.** The agent that wrote the code is the worst one to review it. It's anchored on its own decisions, and the research on models grading their own work backs that up. So every review runs in an empty context window: a subagent, `/code-review`, or a brand new session. If you can, put a different model (or a different model and harness pair) behind the reviewer too, because a different model brings different blind spots.

In the lesson I say: "The implementer will be biased towards its own decisions and won't have a clear mind to review things objectively."

## Why the implementer can't review its own work

Two separate problems stack up here.

**1. Models favor their own output.** This is called self-preference bias, and it's been measured:

- Panickssery et al. found LLM evaluators score their own outputs higher than others' even when human annotators rate them as equal quality. Models like GPT-4 and Llama 2 can tell their own text apart from other models' and humans' with non-trivial accuracy, and when they fine-tuned for that skill, the bias got stronger in a linear relationship.
- Wataoka et al. measured a significant self-preference bias in GPT-4 and traced it to familiarity: models rate low-perplexity text (text that looks like what they'd write) higher than humans do, whoever wrote it.
- The MT-Bench paper (Zheng et al.) saw GPT-4 favor itself with a 10% higher win rate and Claude-v1 with 25%, but is careful to say its data was too limited to prove a self-enhancement bias. I'm including it for honesty: the effect is real in the later controlled studies, the early numbers were noisy.

**2. Self-correction without outside feedback is weak.**

- Huang et al. (ICLR 2024): models "struggle to self-correct their responses without external feedback," and sometimes get worse after trying.
- Stechly, Valmeekam and Kambhampati tested GPT-4 on planning and puzzle tasks: "significant performance collapse with self-critique and significant performance gains with sound external verification."
- Kamoi et al.'s survey (TACL 2024) concludes self-correction "works well in tasks that can use reliable external feedback."

Now add the context problem. Inside one session, the implementer's context window is full of its own plan, its own reasoning and every "this is fine because..." it told itself along the way. Ask it to review and it reads the diff through all of that. Anthropic's own best-practices page says it plainly: `/code-review` reviews the diff "in a fresh subagent that never saw your conversation. It isn't swayed by the reasoning that produced the code." And: "Handing the same task to a subagent doesn't make the answer any better. A fresh reviewer does help, because it hasn't seen your reasoning."

One caveat on all of this: those papers study judging answers, chat and reasoning tasks, not code review specifically. The lesson I take for code is the same, and it matches what I see every day.

## Why a different model can help

Two papers point the same way:

- **Verga et al., "Replacing Judges with Juries."** A panel of smaller judges from disjoint model families beat a single large judge, showed less intra-model bias, and cost over seven times less.
- **Goel et al., "Great Models Think Alike."** LLM judges favor models similar to themselves, and model mistakes are getting more similar as capabilities increase, which the authors flag as a risk of correlated failures.

That's the research version of what I say in the lesson: different companies train on different data, so different models have different biases. A reviewer from another model family is more likely to trip over the thing your implementer was blind to.

The part that's my experience, not a study: this holds for code. Same-family pairs (say, Sonnet implements, Opus reviews) help, but a different company's model in its own harness catches a different class of misses again. Treat the model swap as a bonus. The fresh context is the part you never skip.

| Setup | What it sees | Bias toward the code | Cost | When I use it |
|---|---|---|---|---|
| Same session ("now review what you wrote") | Everything, including its own reasoning | Highest, it's grading itself with its notes open | Lowest | Never for a real review. Fine for "did you run the tests?" |
| Fresh session or subagent, same model | Only what you hand it | Lower, no reasoning to anchor on, but the same model's blind spots | Extra tokens, and it has to re-read the code | Every change |
| Fresh session + different model | Only what you hand it | Lowest, different context and different training | Highest, plus a second tool to run | Risky changes: auth, money, data, migrations |

## How to set it up in Claude Code

**Option 1: `/code-review`.** It's built in and works on any plan. In a terminal session it runs as a background subagent with its own context window, so it starts clean. With no target it reviews your branch's changes. You can point it at a PR number, branch, path or commit range, add `--fix` to apply findings, or `--comment` to post them on the PR. `/review` is an alias. An effort level trades coverage for confidence: `low` reports only what it's most confident in, `medium` through `max` widen the net.

**Option 2: your own reviewer subagent.** Every non-fork subagent "starts with a fresh, isolated context window. It doesn't see your conversation history, the skills you've already invoked, or the files Claude has already read." The `model` field takes `sonnet`, `opus`, `haiku`, `fable`, a full model ID, or `inherit`. Leave it out and the subagent runs on the same model as your conversation. So set it to a model your implementer isn't using. The file is below.

**Option 3: a separate session.** The best-practices page calls a second session "the easiest independent reviewer you can get": one session writes, another reviews without having watched it being written, and you paste the findings back. Start it on a different model with `claude --model opus` (or `sonnet`, or a full model name), or pipe the diff straight in:

```bash
git diff main...HEAD | claude -p --model opus "Review this diff against SPEC.md. Report only correctness gaps, with file and line. Skip style."
```

**Option 4: a different company's model.** Open that vendor's coding agent in a separate terminal on the same repo, give it the same diff, spec and reviewer prompt, and paste its findings back into your Claude Code session. That's the "different model and harness pair" from the lesson.

**On a team: Code Review on GitHub.** A managed service an Owner turns on for Team and Enterprise plans. Several agents read each PR, a verification step checks findings against the code, and the results land as inline comments ranked by severity.

### Gotchas that make a "fresh" reviewer not fresh

- **Forks inherit everything.** A fork "inherits the entire conversation so far instead of starting fresh," with the same model. `/subtask` starts a fork. Great for side work, wrong for review.
- **The delegation message can leak reasoning.** When Claude hands off to a subagent, it "composes a delegation message that summarizes the task." My read: if that summary says "I used a mutex here because X," you've smuggled the implementer's reasoning back in. Tell it what to pass.
- **Same-family aliases follow your session.** If your session runs on an Opus model and the subagent says `model: opus`, it runs on that same version. Use a full model ID to pick another version.
- **Forcing one model overrides yours.** While `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` is on, Claude Code ignores the `model` field in subagent definitions.
- **CLAUDE.md still loads.** Non-fork subagents get your CLAUDE.md files, which is usually what you want: your rules apply to the review. Set `omitClaudeMd: true` if you want the reviewer to work only from what you hand it.

## What to give the reviewer (and what not to)

| Give it | Don't give it |
|---|---|
| The diff, or the branch to compare against | The implementer's plan or chain of reasoning |
| The spec, ticket or acceptance criteria | "I chose X because..." explanations |
| The test command, so it can run it | The implementer's own summary of what it did |
| Your rules (CLAUDE.md does this) | A list of things that are "already fine" |

The research above says outside feedback beats self-critique, so let the reviewer run real checks. Tests and typechecks are the external feedback. The reviewer's opinion is one more signal on top.

And ask for less than you think. From the best-practices page: "A reviewer that's asked to find problems will always find *something*. If you fix every finding, you end up with extra abstraction layers and tests for cases that can't happen." Keep "skip style" in the prompt, and let the reviewer say "nothing found."

## Copy-paste: the reviewer subagent

Save as `.claude/agents/reviewer.md` in your project (or `~/.claude/agents/reviewer.md` for every project). Change `model` to whatever your implementer is not.

```markdown
---
name: reviewer
description: Independent code reviewer. Reviews a diff against its spec in a fresh context. Use after implementing a change, before opening the PR.
tools: Read, Grep, Glob, Bash
model: opus
---

You are reviewing code you did not write. You have not seen how it was built,
and that is the point. Judge the code only by the diff, the spec and the tests.

1. Read the diff you are given (or run git diff against the base branch you are told).
2. Read the spec or acceptance criteria. List every requirement.
3. For each requirement: is it implemented, and is there a test that would fail without it?
4. Run the test command you are given. Report the command and the result.
5. Look for correctness problems: wrong logic, unhandled errors on real paths,
   broken edge cases, security issues, data loss, changes outside the stated scope.

Report:
- Verdict: PASS, or FAIL with the blocking findings.
- Each finding: severity (blocking or minor), file:line, what is wrong,
  and the input or step that shows it.
- Requirements with no test.

Rules: do not edit files. Skip style and naming. If you find nothing that
affects correctness, say "No blocking findings." Do not invent problems to fill the report.
```

`tools` limits what it can call. With Bash it can still change files, so the "do not edit" line matters. If you don't need it to run tests, drop Bash and it's read-only by construction.

## Copy-paste: what to tell your implementer

Paste this when the implementer says it's done:

> Spin up the reviewer subagent on this change. Pass it only: the base branch, the path to the spec, and the test command. Do not pass your plan, your reasoning or your summary of what you did. When it reports back, show me the findings as-is, then fix only the blocking ones and tell me which you skipped and why.

## Copy-paste: reviewer checklist

For a separate session or another vendor's agent, use this as the prompt:

```text
You are an independent reviewer. You did not write this code.
Inputs: the diff (git diff <base>...HEAD), the spec at <path>, the test command <cmd>.

1. Every requirement in the spec: implemented? tested?
2. Run the tests. Paste the command and the last lines of output.
3. Correctness only: logic, error paths, edge cases, security, data loss, scope creep.
4. For each finding: blocking or minor, file:line, why, how to reproduce.
5. Verdict: PASS or FAIL. "No blocking findings" is a valid answer.
Skip style. Do not edit files.
```

## What goes wrong

- **Reviewing in the same session.** The most common one. It reads its own reasoning back and agrees with itself.
- **Forking instead of spawning fresh.** A fork has the whole conversation, so it's the same reviewer with a new name.
- **Handing over the implementer's summary.** Now the reviewer checks the story, not the code.
- **No tests in the loop.** Self-critique is the weak part in the research. Make the reviewer run something real.
- **Fixing every finding.** You end up with code built to please the reviewer. Fix the blocking ones, skip the rest on purpose.
- **Same model everywhere by default.** Leave `model` unset and the reviewer runs on your conversation's model. Fine for most changes, but don't call it a second opinion.

## Sources

| Claim | Source |
|---|---|
| LLM evaluators score their own outputs higher than humans do; self-recognition correlates linearly with self-preference | Panickssery, Bowman, Feng, LLM Evaluators Recognize and Favor Their Own Generations: https://arxiv.org/abs/2404.13076 |
| GPT-4 shows significant self-preference bias; LLMs rate low-perplexity text higher than humans do | Wataoka, Takahashi, Ri, Self-Preference Bias in LLM-as-a-Judge: https://arxiv.org/abs/2410.21819 |
| GPT-4 favors itself by a 10% win rate, Claude-v1 by 25%, but data too limited to determine a self-enhancement bias | Zheng et al., Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena: https://arxiv.org/abs/2306.05685 |
| LLMs struggle to self-correct reasoning without external feedback, sometimes degrade | Huang et al., Large Language Models Cannot Self-Correct Reasoning Yet (ICLR 2024): https://arxiv.org/abs/2310.01798 |
| Performance collapse with self-critique, gains with sound external verification | Stechly, Valmeekam, Kambhampati, On the Self-Verification Limitations of LLMs on Reasoning and Planning Tasks: https://arxiv.org/abs/2402.08115 |
| Self-correction works well with reliable external feedback | Kamoi et al., When Can LLMs Actually Correct Their Own Mistakes? (TACL 2024): https://arxiv.org/abs/2406.01297 |
| A panel of judges from disjoint model families shows less intra-model bias than one large judge, at over 7x lower cost | Verga et al., Replacing Judges with Juries: https://arxiv.org/abs/2404.18796 |
| Judges favor models similar to themselves; model mistakes grow more similar with capability | Goel et al., Great Models Think Alike and this Undermines AI Oversight: https://arxiv.org/abs/2502.04313 |
| Non-fork subagents start with a fresh, isolated context; delegation message; CLAUDE.md loads unless `omitClaudeMd`; `model` field values and default; alias version rule; `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`; forks inherit the conversation; `/subtask`; `tools` field; Bash can still change files | Claude Code subagents: https://code.claude.com/docs/en/sub-agents |
| Fresh reviewer "isn't swayed by the reasoning"; second session as reviewer; reviewer always finds something, keep "skip style"; same model by default | Claude Code best practices: https://code.claude.com/docs/en/best-practices |
| `/code-review` runs as a background subagent with its own context; targets, `--fix`, `--comment`, effort levels, `/review` alias | Review locally with /code-review: https://code.claude.com/docs/en/code-review-local |
| Managed Code Review for Team and Enterprise: several agents, verification step, inline comments by severity | Claude Code Code Review: https://code.claude.com/docs/en/code-review |
| `--model` flag, `claude -p`, piping content into `claude -p` | Claude Code CLI reference: https://code.claude.com/docs/en/cli-reference |

Docs checked on 2026-11-24.

## Want more like this?

More agent breakdowns and the full lessons are inside my Skool community, **Agent Architects**: https://www.skool.com/agent-architects
