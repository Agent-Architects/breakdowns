# Pick a model using your own work

Choose the least expensive model that reliably completes the task at the quality and speed you need. A product tier or parameter count can narrow the shortlist. Your examples decide the winner.

## Run the same test twice

1. Pick one recurring job. For example, an agent reads support tickets, assigns a team, and returns JSON that your ticket system can accept.
2. Save a small set of representative inputs. Include easy cases, ambiguous cases, and past failures. Keep private customer data out of any service that has not been approved to handle it.
3. Write the pass criteria before you run either model. For the ticket example, the output must parse, select an allowed team, and ask for human review when the text leaves ownership unclear.
4. Give two candidates the same instructions, inputs, tools, and limits. Record their exact model versions and settings. Repeat the tricky cases to catch inconsistent answers.
5. Grade each output against the criteria. Compare cost per successful job, including retries, and the time your user actually waits. A cheap first attempt can be expensive if it regularly needs another pass.

| Candidate | Cases passed / tried | Must-pass failures | Total cost incl. retries | Cost per successful job | Typical / slow-case latency |
|---|---|---|---|---|---|
| Lower-cost option |  |  |  |  |  |
| More capable option |  |  |  |  |  |

**Decision rule.** Set your minimum pass rate, maximum acceptable wait, and must-pass cases in advance. Among the candidates that qualify, choose the lowest cost per successful job. If neither qualifies, inspect the failures. Missing context, a broken tool, or vague instructions can affect both. If only one type of case needs the stronger model, route that case to it and rerun the test.

**Worked example.** Suppose model A passes 18 of 20 cases for $0.10 total. Model B passes 20 of 20 for $0.30. Their costs per successful case are approximately $0.006 and $0.015. If both misses were critical routing mistakes, A alone misses the quality bar. Test whether sending just the ambiguous tickets to B closes the gap.

## Why this test matters

Teams choose training data, architecture, and post-training methods. In one similarly trained family, a larger model can improve difficult-task performance. Across families, the result can reverse. DeepMind’s 70B Chinchilla outperformed its 280B Gopher on many benchmarks, and mixture-of-experts designs can activate only part of the network for each token. Check actual quality, latency, and price on your workload. [DeepMind research](https://arxiv.org/abs/2203.15556) · [Mistral model architecture](https://docs.mistral.ai/models/mixtral-8x7b-0-1)

The full AI Models lesson is in [Agent Architects](https://www.skool.com/agent-architects).
