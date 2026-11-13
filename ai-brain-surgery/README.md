# An AI edited another AI's weights. Here's what MIT showed (and didn't)

You commented, so here's the full breakdown.

Researchers at MIT CSAIL had a frontier model, OpenAI's GPT-6 Astra, edit the weights of a small open-source model directly. No training run. The edited model scored much higher on math. The result is real, and it's also narrower than the headline. This page covers both.

## What the study is

- Title: "Sparks of Weight-Space Programming: LLMs can natively read & write neural network weights"
- Authors: Rikiya Takehi, Jayden Teoh, Alex Zhang, Omar Khattab, all listed under MIT CSAIL
- Published: November 2, 2026, on the first author's site: https://rikiyat.github.io/blog/weight-space-programming/
- Logs of every experiment: https://github.com/RikiyaT/lm_understand-logs

It's a research blog post, not a peer-reviewed paper. I found no arXiv listing. The authors released full logs, which is why people could check it.

## What they did

The authors call the idea Weight-Space Programming: "treating the weights as a program to be read and written." Instead of training a model, you let an LLM read its raw numbers and change them, the way a programmer edits code.

The math experiment, step by step:

1. The target was Qwen3.5-0.8B, a small open model (Apache 2.0 license).
2. Astra got a Python session with the model's weights loaded. "No training or gradient information is allowed."
3. It could pick practice problems from the GSM8K and MATH training sets and run a limited number of forward passes (10, 25 or 50).
4. It noticed the model loops: it repeats the same text and never reaches an answer. 85 of its first 96 practice answers ran to the 32,768-token limit.
5. It traced the looping to one direction written by the MLPs of layers 15 and 19.
6. It subtracted that direction from 64 output columns in each of those layers. That is 131,072 weights, or 0.016% of the model.

## Key results

Qwen3.5-0.8B, same sampling settings for both models:

| | MATH-500 | GSM8K | IFEval | Answers that hit the token limit |
|---|---|---|---|---|
| Base | 7.9% | 13.8% | 21.0% | 93.0% |
| Edited, 10 forward passes | 12.3% | 25.7% | 49.0% | 87.2% |
| Edited, 25 forward passes | 14.1% | 25.1% | 39.9% | 86.4% |
| Edited, 50 forward passes | 48.1% | 67.1% | 62.3% | 33.1% |

The strongest run took 158 conversational turns, 80 Python runs and 20.3 hours, including 4.7 hours waiting through a service outage (VentureBeat's reading of the logs).

Other experiments in the same post:

- Given 17,253 raw weights and no tools, Astra named the game a network was trained on (Breakout, 99% confident). VentureBeat reports it identified Breakout, Pong, Pac-Man and Freeway across four networks with matching architectures.
- With no tools, Astra wrote game-playing networks from scratch. In Breakout its network scored 517.4. The PPO baselines scored 15.8 (100M training steps) and 25.3 (500M steps). Against the 500M-step baselines it came close in Asterix and reached 60% of the score in Seaquest. These are the authors' own PPO runs.

## The catch: it fixed a loop, and it failed on Gemma

Put this part on top of anything you repeat.

**The gain is mostly a repetition-loop fix.** The authors say it themselves: "Fixing loops, however, is not the same as making a model better at math: it lets the model finish answers it could already work out." The share of answers that ran out of tokens fell from 93% to 33%. Looping is a known Qwen behavior in thinking mode. The authors also note that turning thinking off raises the base score, but "it does not fix the weights. It avoids the loops by not using the mode that has them."

**It did not work on Gemma 3 270M.** Gemma rarely loops (8.5% of answers hit the limit, against 93% for Qwen). The blog: "Here, Astra could not improve it." MATH-500 stayed between 6.8% and 7.7% across all budgets. In their words: "Editing weights could remove an obstacle that hid an ability, but it could not add an ability the model lacked." The authors published this failure. A critic pointed out the announcement thread on X left it out.

Other limits:

- One frontier model, one small target model, mostly single runs per setting. The authors: "Weight-Space Programming is not a method. It is the name of an emerging concept." They also say "We have not compared Astra with interpretability researchers".
- On the sycophancy experiment, "from the weights alone, Astra was unable to tell." It only picked out the sycophantic model after being allowed to look at attention patterns on texts it wrote.
- Cost and speed are not measured. VentureBeat: "The study did not establish a sixfold reduction in spending alongside its sixfold mathematical accuracy gain."
- It did not edit itself. The target was a different, much smaller model. Self-improvement is the authors' speculation, not a result: VentureBeat notes "the researchers did not demonstrate such a cycle or establish that gains would compound."
- The comparisons in the games experiment are against the authors' own PPO runs, not against an established engine or the same heuristic written as ordinary code (A. Maier's critique, linked below).

## Why it matters

What the authors argue it could lead to (their claims, not results):

- Auditing a model from its weights, without running benchmarks, for example to find backdoors.
- Cheaper changes: editing a few weights instead of curating data and running a training loop.
- Adding or removing a capability by editing a small number of weights, which "can leave the rest of the model intact and avoid the catastrophic forgetting that fine-tuning often causes."
- Grafting a circuit from one model into a different architecture.
- Recursive self-improvement: "An LLM that can inspect, debug, and improve its own weights, or those of a newer model, offers a richer, more native path to it."

How people reacted:

- The authors say it has been replicated or extended by "more than a hundred we know of," including Hugging Face, who rebuilt the edited model from the logs. That count is the authors' own.
- Maxime Fournes, CEO of PauseAI, called it "a terribly reckless research direction" because it could "massively accelerate progress".
- A skeptic put the result as: "if there's a clear flaw in the LLM's reasoning, LLMs can help edit it out", and questioned whether it shows stronger reasoning.

## What it means if you build with agents

These are my takeaways, not claims from the study.

1. **Weight edits need the weights.** This applies to open models you run yourself. With a hosted API, your provider would have to do it. VentureBeat: "Customers relying solely on a hosted API would need their provider to enable or perform the intervention."
2. **The shape that worked is narrow.** One specific, reproducible failure (the model loops), a harness where the agent can run the model and measure, and a clear metric. Giving an agent that setup is a testable idea. "Make it better" isn't.
3. **Check the simple fix first.** Here, turning thinking off raises the base model's score, as the authors note, though it doesn't fix the weights. Compare any weight patch against the cheapest alternative before you adopt it.
4. **Treat a patch like a new model version.** Compare it against the original on tasks you care about, look for unintended changes, and keep a rollback path.
5. **Measure the whole cost.** Finding the patch took a 20-hour agent session in the strongest run. Saved compute is a hypothesis in this study, not a number.

The enterprise uses in the news coverage are hypotheses. No deployments were reported.

## Sources

Checked November 13, 2026.

- Primary: https://rikiyat.github.io/blog/weight-space-programming/ (Sparks of Weight-Space Programming, November 2, 2026, with an authors' update on November 12)
- Author page confirming MIT CSAIL: https://rikiyat.github.io/
- Experiment logs and artifacts: https://github.com/RikiyaT/lm_understand-logs
- VentureBeat, Carl Franzen, November 2, 2026: https://venturebeat.com/technology/like-gene-editing-for-neural-networks-mit-researchers-used-gpt-6-astra-to-edit-qwens-open-weights-directly-boosting-math-performance
- Independent critical read (A. Maier): https://akmaier.substack.com/p/weight-space-programming-what-is

## Want the full lesson?

This is the short version. The full lessons on building with agents are inside my Skool community, **Agent Architects**: https://www.skool.com/agent-architects
