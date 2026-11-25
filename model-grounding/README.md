# How AI models stay grounded: the model is a snapshot, the harness checks reality

You commented GROUND, so here's the full breakdown.

**The short version.** An AI model's understanding of the world is not reality. It's a predictive model trained on a huge pile of internet data, frozen at a cutoff date. Ask it about anything that changed after that date and it gives you its best guess from old data, with full confidence. What fixes that is the harness around the model: the tools that let it check the real world before it answers, like web search, fetching a page, reading your actual files or running a command. That's grounding. The model predicts, the tools check, and the answer is based on what's true now.

## The model is a snapshot of its training data

In the lesson I say: "The AI model's understanding of the world is not reality. It's a model that has been created by training off of data from the internet. It's a predictive model. That means it's predicting what it thinks the world is like. It doesn't mean it knows what the world is like."

That's literally how these models are built. Anthropic's glossary describes pretraining as "the initial process of training language models on a large unlabeled corpus of text," where the model is "pretrained to predict the next word" ([Glossary](https://platform.claude.com/docs/en/about-claude/glossary)). Everything it "knows" is patterns from that text.

And that text stops at a date. Every model on Anthropic's models page lists two dates: a **training data cutoff** and a **reliable knowledge cutoff**. For the current lineup (Claude Fable 5.2, Opus 5.5, Sonnet 5.5, Haiku 5.5) both say June 2026 ([Models overview](https://platform.claude.com/docs/en/about-claude/models/overview)). Anything that happened after that isn't in the model at all. And the world keeps moving every day after the cutoff, while the model stays exactly the same.

Three things follow from that:

1. **The model doesn't know what it doesn't know.** It has no clock and no feed. Nothing inside it says "this fact is 8 months old."
2. **It will still answer.** It's a predictor, so it predicts. The output sounds just as confident when it's wrong.
3. **Older models are further behind.** A model trained two years ago is two years out of date on everything, and you might still be running it in a cheap subagent somewhere.

## The president test

My favorite way to see this: ask a model who the president is.

"Its answer will actually be the most recent president that was present in its data that it was trained on. So if you ask a really old model who the president is, it won't know the answer. It will give you the wrong answer."

The model isn't lying. It's doing exactly what it was trained to do: predict the most likely answer from its data. Its data just ends before the present.

Swap "president" for anything your agent touches and you see the problem:

- the latest version of a library or a CLI flag that changed last month
- a price, a plan limit, a free tier
- an API endpoint that moved
- which model is newest (models are notoriously out of date about themselves)
- the state of your own project: which branch you're on, whether the tests pass, whether that PR merged

All of these feel like facts to the model. All of them can be stale.

## The harness lets the model check reality

"Because we have harnesses that wrap around that model, the harness actually lets the model use tools to check the real world to validate its predictions."

The harness is everything around the raw model: the loop that runs it, the tools it can call, the files it can read, the permissions. Claude Code, Codex, the Claude app, your own agent built on the API: all harnesses.

Give the same model a web search tool and the president question changes completely. "Now when you ask it who the president is, it doesn't matter when that model was trained. It can use its web search tool to actually search the live internet and get a response back. That's grounding its predictions in reality."

The providers describe their search tools in exactly these terms:

- Anthropic: "The web search tool gives Claude direct access to real-time web content, allowing it to answer questions with up-to-date information beyond its knowledge cutoff. The response includes citations for sources drawn from search results." ([Web search tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool))
- Google literally calls the feature grounding: "Grounding with Google Search connects the Gemini model to real-time web content," which lets it "provide more accurate answers and cite verifiable sources beyond its knowledge cutoff" and "reduce model hallucinations by basing responses on real-world information." ([Grounding with Google Search](https://ai.google.dev/gemini-api/docs/google-search))

Web search is the obvious one, but every tool that reads the real world grounds the model:

| Tool | What it grounds |
|---|---|
| Web search | News, prices, versions, anything public that changes |
| Fetch a URL | The exact docs page, changelog or spec, instead of a memory of it |
| Read a file | Your real code and config, instead of what it assumes is there |
| Run a command | `git status`, the test suite, `--help`, the live version of a tool |
| Query an API or database | Real data instead of a plausible-looking guess |
| An MCP server or connected app | Your calendar, your inbox, your tickets, right now |

Claude Code ships `WebSearch` ("Performs web searches") and `WebFetch` ("Fetches content from a specified URL") alongside its file and shell tools ([Claude Code tools reference](https://code.claude.com/docs/en/tools-reference)). Having the tools isn't the whole job, though. The model has to actually use them instead of answering from memory, and that's where your instructions come in.

## How to keep your agent grounded

The rule I give my agents is short: **verify before you claim.** If you didn't check it with a tool in this session, you don't know it.

### 1. Turn on the tools that check reality

- In Claude Code, keep web search and web fetch available (allow them in your permissions so they don't stall on a prompt), plus the normal file and shell tools.
- On the API, add the web search tool to the request when the task touches anything time-sensitive.
- For your own systems, give the agent read access through a CLI, an MCP server or a script, so it can look instead of guess.

### 2. Tell it when to use them

Paste this into your `CLAUDE.md` or `AGENTS.md`:

```markdown
## Grounding: verify before you claim

Your training data has a cutoff, so anything that changes over time may be stale in your memory.
Check it with a tool in this session before you state it or act on it.

- Versions, flags, APIs, prices, limits, release dates, "the latest X": look it up
  (official docs or the tool's own --help / --version), then answer. Cite the source.
- Anything about this project (files, branches, test results, config, deploy state):
  read the file or run the command first. Never describe code you haven't opened.
- Today's date and anything "recent": get the date from the system (`date`), not from memory.
- If you can't check something, say "I haven't verified this" instead of guessing.
- When a tool result and your memory disagree, the tool result wins.
```

### 3. Make it show its source

Anthropic's own guide to reducing hallucinations gives the same three moves: allow uncertainty ("Explicitly give Claude permission to admit uncertainty. This technique can drastically reduce false information."), ground responses in direct quotes, and verify with citations, where Claude backs each claim with a quote or source and retracts claims it can't support ([Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations)). A link or a quoted line is something you can check in two seconds. "I believe" is not.

### 4. Copy-paste prompt: ground a research question

```text
Answer this using live sources, not your memory: <question>

1. Get today's date first.
2. Search the web and open the most authoritative sources you find
   (official docs, the vendor's own page, the primary paper or announcement).
3. Quote the exact lines that answer the question, with the URL and the date
   the page shows, if it shows one.
4. If sources disagree, say so and say which one is more authoritative and why.
5. Then give your answer in two or three sentences, and flag anything you
   could not verify.
```

## What goes wrong

- **Trusting the confident answer.** The tone tells you nothing. A stale answer and a correct one sound the same.
- **Tools available, never called.** The agent has web search but answers from memory because nobody told it to look. Put the rule in the instructions file.
- **Grounding the question but not the project.** It looked up the docs, then assumed your code matches what it expected. Read the file too.
- **Old models in cheap seats.** Your main agent is current, but the small model in a subagent or a script is a year older. It needs the same tools and the same rule.
- **Searching, then summarizing from memory anyway.** Ask for quotes and links so you can see the answer came from the source.
- **Low-quality sources.** Web search finds forum posts and SEO pages too. Tell it to prefer official docs and primary sources.
- **Stale facts saved into memory files.** A fact the agent looked up once and wrote into `CLAUDE.md` goes stale too. Date it, or tell the agent to re-check it.
- **Thinking grounding means zero mistakes.** Anthropic says these techniques "significantly reduce hallucinations" but "don't eliminate them entirely," so check anything high-stakes yourself.

## Sources

| Claim | Source |
|---|---|
| Pretraining on a large unlabeled corpus; models are "pretrained to predict the next word" | [Anthropic glossary](https://platform.claude.com/docs/en/about-claude/glossary) |
| Each model lists a training data cutoff and a reliable knowledge cutoff; June 2026 for the current lineup | [Models overview](https://platform.claude.com/docs/en/about-claude/models/overview) |
| Web search gives "direct access to real-time web content" and "up-to-date information beyond its knowledge cutoff," with citations | [Web search tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool) |
| Grounding with Google Search connects the model to real-time web content, cites verifiable sources beyond its knowledge cutoff, reduces hallucinations | [Grounding with Google Search](https://ai.google.dev/gemini-api/docs/google-search) |
| Claude Code's WebSearch and WebFetch tools | [Claude Code tools reference](https://code.claude.com/docs/en/tools-reference) |
| Allow uncertainty, ground in direct quotes, verify with citations; techniques reduce but don't eliminate hallucinations | [Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations) |

Docs checked on Nov 25, 2026. Model cutoffs and tool names change with every release, so check the links before you rely on a detail. Which is the whole point of this page.

## Want more like this?

More agent breakdowns and the full lessons are inside my Skool community, **Agent Architects**: https://www.skool.com/agent-architects
