# Model vs harness: why the same model scores differently

You commented, so here's the full breakdown.

When you see a score for an AI model, you're not only seeing the model. You're seeing the model inside a harness: the app that wraps it with a system prompt, tools, and a loop that decides what happens next. Change the harness and the same model can score differently.

This is the full breakdown behind the harness short. You'll get the numbers, what they do and don't prove, and how to test a model in more than one harness before you pick one.

## What a harness is

The model produces the next step. The harness is everything around it: the system prompt, which tools it can call, and how results are fed back in. Claude Code, Codex CLI, and Gemini CLI are harnesses. So are generic ones like Terminus 2, which benchmark teams use as a common baseline.

A benchmark score is a score for the model and its harness together. Leaderboards often don't make clear which harness ran the model, so compare with care.

## Same model, different harness, different score

On Terminal-Bench 2.1, here's how the same model scored in a vendor harness versus the generic Terminus 2 harness ([Snorkel leaderboard](https://snorkel.ai/leaderboard/terminal-bench-2-1/)):

| Model | Vendor harness | Terminus 2 | Gap |
|---|---|---|---|
| Claude Opus 4.6 | Claude Code 70.1% | 63.8% | 6.3 points |
| Claude Sonnet 4.6 | Claude Code 58.5% | 51.5% | 7.0 points |
| Claude Fable 5 | Claude Code 83.8% | 80.5% | 3.3 points |
| GPT-5.5 | Codex CLI 83.2% | 78% | 5.2 points |
| Gemini 3 Pro | Gemini CLI 65.8% | 73.9% | Terminus 2 higher by 8.1 points |

The direction isn't constant. Most rows favor the vendor harness, but Gemini 3 Pro scores higher in Terminus 2.

A few more examples:

- **LangChain** kept the model fixed (gpt-5.2-codex) and only changed the harness. Terminal-Bench 2.0 went from 52.8% to 66.5%, a 13.7 point gain. They tuned the harness on that benchmark's own tasks, and their tuned harness didn't carry over to Opus 4.6 (59.6%). [Source](https://www.langchain.com/blog/improving-deep-agents-with-harness-engineering), 17 Feb 2026.
- **An audit of 254 public SWE-bench submissions** found a median score range of 15.6 points for the same model across scaffolds, and up to 29.8 points. Those are mostly 2024 to 2025 era models, and the authors call the result observational. [Source](https://arxiv.org/abs/2609.17394), 15 Sep 2026.
- **Epoch AI** found that switching only the scaffold made up to an 11% difference for GPT-5 and up to 15% for Kimi K2 Thinking on SWE-bench Verified. [Source](https://epoch.ai/gradient-updates/why-benchmarking-is-hard), 23 Dec 2025.
- **Anthropic** found that infrastructure setup alone moved Terminal-Bench 2.0 by 6 points, and says leaderboard gaps under 3 points deserve skepticism until the setup is documented and matched. [Source](https://www.anthropic.com/engineering/infrastructure-noise), 5 Feb 2026.

## What this does and doesn't say

The harness effect is large enough to be in the same ballpark as the gap between the top few models. That's the safe claim.

It does not say the harness matters more than the model. In the same audit, the fitted model range was 47.9 points against 37.6 points for scaffolds: "the fitted ranges are of the same order". Under one fixed harness, model gaps are still huge, and the gap between older and newer model generations is much bigger than most harness gaps.

The numbers are also noisy:

- Some harness gaps sit inside the noise. Several of the Terminal-Bench rows above are within a few points, and Anthropic notes that confidence intervals alone span 1 to 2 points.
- Evaluators disagree. Claude Opus 4.8 in Claude Code scores 78.9% on the Snorkel board and 69.66% on the Vals board. Same model, same named harness.
- Benchmark revisions can flip a result. On Terminal-Bench 2.0, Opus 4.6 in Terminus 2 was ahead of Claude Code (62.9% vs 58%). After 28 tasks were fixed in 2.1, Claude Code was ahead.

Treat any single harness gap as specific to the site and run that produced it.

## Models are trained on their own harnesses

This is the part the short is about. Companies build a model and a harness together: Claude in Claude Code, ChatGPT in Codex. The idea is that a model trained around its own harness is more at home in it. I haven't found a primary source that measures that training effect directly.

The leaderboard above fits that pattern, since most vendor rows beat the generic harness. But it doesn't prove the cause. The Gemini 3 Pro row goes the other way, and a score gap alone can't tell you why it exists. Treat "trained on their own harness" as a reason to test, not as a result.

## Why you test a model in several harnesses

A leaderboard tells you how a model did in someone else's harness, on someone else's tasks, with someone else's settings. Your work is different.

Try this:

1. Pick three to five real tasks from your own work, small enough to check by hand.
2. Run the same model in two or three harnesses, such as its own vendor harness and a generic or open one.
3. Keep the task, the instructions, and the success check identical.
4. Compare results you can verify yourself, plus time and cost. Run each more than once, since one run is noisy.
5. Then swap the model and repeat, so you can see how much came from the model and how much from the harness.

A model that looks weaker in one harness may be fine in another. And a harness that looks great on a benchmark may not be the one that suits your tasks.

## Safe takeaways

- The same model can score differently depending on the harness around it.
- The harness is a large, under-reported variable. It's not proven to matter more than the model.
- When two top models are a few points apart, ask which harness ran each one.
- Test the model in more than one harness on your own tasks.

Sources checked November 13, 2026. Leaderboards and posts change, so follow the links for current numbers.
