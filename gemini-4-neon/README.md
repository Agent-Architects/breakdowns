# Gemini 4 Neon: Opus 5.5 level for about half the price

You commented NEON, so here's the full breakdown.

**The short version.** Gemini 4 Neon scores a little above Claude Opus 5.5 and costs about half as much per coding-agent task. It's slow, and it's not the cheapest model you can run. Every number below was checked on Nov 22, 2026.

## Every number in the carousel

| What the slide says | The number | Source |
|---|---|---|
| It outscores Opus 5.5 | 61 vs 59 | [Artificial Analysis Intelligence Index v5.0.1](https://artificialanalysis.ai/leaderboards/models) |
| #1 for coding agents | Neon 59, Claude Fable 5.2 58, Claude Opus 5.5 58 | [Artificial Analysis Coding Agent Index v2.1](https://artificialanalysis.ai/articles/gemini-4-neon-intelligence-gain) and [their post](https://x.com/ArtificialAnlys/status/2123170648772288540) |
| About half the price | $6.86 vs $12.61 per coding-agent task | [Artificial Analysis, Nov 18](https://artificialanalysis.ai/articles/gemini-4-neon-intelligence-gain) |
| It's slow | 22.3 minutes per task, median model 12.7 | [Artificial Analysis, Gemini 4 Neon page](https://artificialanalysis.ai/models/gemini-4-neon) |
| "They're so far ahead here it's insane." | Theo, Nov 19 | [His post](https://x.com/theo/status/2123619214061977920) |
| "We will work on more efficiency." | Melvin Johnson, Gemini post-training lead at Google, Nov 21 | [His reply](https://x.com/melvinjohnsonp/status/2124314155884974558) |

## The honest version

**Opus 5.5 level.** Neon is ahead on both Artificial Analysis indexes: two points overall, one point for coding agents. That's close, not a blowout. In [Google's own benchmark table](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-neon/), Opus 5.5 still wins Terminal-bench 4.1 (65.8 vs 65.2) and FrontierCode 2.0 (47.3 vs 46.2).

**About half the price.** $6.86 against $12.61 is 46% less. That's per coding-agent task, with each model running in its maker's own CLI (Antigravity CLI and Claude Code). On general Intelligence Index tasks the gap is smaller: $6.44 against $10.04, which is 36% less. The API price is $3 in and $15 out per 1M tokens ([Google](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-neon/)).

**Slow.** 22.3 minutes per task against a 12.7 minute median. About 60 seconds before the first answer token at its top setting. It ranks #92 of 94 on verbosity, so it writes a lot of tokens ([Artificial Analysis](https://artificialanalysis.ai/models/gemini-4-neon)).

**Not the cheapest, not the smartest.** On the Intelligence Index, GPT-6.2 Astra scores 62 for $4.00 a task and GPT-6.2 Sol scores 57 for $1.01. Claude Fable 5.2 leads at 65. Neon's price win is against Claude.

## The leaderboard it sits in

| Model | Intelligence Index | Cost per task |
|---|---|---|
| Claude Fable 5.2 | 65 | $26.54 |
| GPT-6.2 Astra | 62 | $4.00 |
| **Gemini 4 Neon** | **61** | **$6.44** |
| Gemini 4 Carbon | 60 | $7.76 |
| Claude Opus 5.5 | 59 | $10.04 |
| GPT-6.2 Sol | 57 | $1.01 |
| Claude Sonnet 5.5 | 55 | $10.02 |
| Gemini 4 Hydrogen | 54 | $3.16 |

Source: [Artificial Analysis leaderboard](https://artificialanalysis.ai/leaderboards/models), top setting per model. Cost here is per Intelligence Index task. That's why Neon shows $6.44 in this table and $6.86 in the coding-agent test.

## Which model to pick for what

This is my read of the numbers above. It isn't a benchmark result.

| If you need | Pick | Why |
|---|---|---|
| A daily coding agent, and you can wait | Gemini 4 Neon | #1 on the Coding Agent Index, $6.86 a task |
| The highest score, whatever it costs | Claude Fable 5.2 | 65 on the Intelligence Index, $26.54 a task |
| Strong general work for less | GPT-6.2 Astra | 62 for $4.00 a task. For coding agents it scores 53 |
| Cheap bulk work | GPT-6.2 Sol | 57 for $1.01 a task. For coding agents it scores 50 |
| Fast everyday tasks | Gemini 4 Hydrogen | 54 for $3.16 a task. Google's Logan Kilpatrick calls it the ["quick and efficient model"](https://x.com/OfficialLoganK/status/2124169455576154400) |
| An answer right now | Not Neon at its top setting | 22.3 minutes a task |

The coding-agent scores for Astra and Sol come from the chart in [Artificial Analysis's post](https://x.com/ArtificialAnlys/status/2123170648772288540), where both ran in Codex.

**One setting worth knowing.** Neon on high effort scores 60 for $3.74 a task. On its top setting (xhigh) it scores 61 for $6.44. You pay $2.70 more per task for one point ([Artificial Analysis](https://artificialanalysis.ai/models/gemini-4-neon)).

**Then test it on your own work.** A leaderboard narrows the shortlist. Your own tasks pick the winner: [Pick a model using your own work](../model-selection-field-test/).

## Fine print

- Scores are each model's top setting. For the Coding Agent Index, each model ran in its maker's own CLI.
- Gemini 4 Carbon's cost per task is at its standard price. It's on a $2 in / $10 out promo through Nov 30, 2026.
- Post dates are US Eastern, the way X shows them.
- These numbers move fast. Open the links before you commit to a model.

## Want more like this?

More model breakdowns and the full lessons are inside my Skool community, **Agent Architects**: https://www.skool.com/agent-architects
