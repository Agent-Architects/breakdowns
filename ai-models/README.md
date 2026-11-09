# AI models are really a mirror of you

You commented, so here's the full breakdown.

The claim from the video: an AI model meets you at the level you show up at. That isn't a vibe, it falls straight out of how these models work. Here's the technical version, then what to do with it.

## 1. What the model actually computes

A large language model is a function that takes a sequence of tokens and returns a probability distribution over the next token.

1. **Tokenize.** Your text is split into tokens (word pieces, roughly 3 to 4 characters of English each) and each token becomes an integer id.
2. **Embed.** Each id is looked up in an embedding table and becomes a vector of a few thousand numbers.
3. **Transformer layers.** The vectors pass through dozens of layers. Each layer has:
   - **self-attention**: every token builds a weighted mix of the tokens before it, so its vector picks up context from the whole input
   - a **feed-forward block**: the same small neural network applied to each position
4. **Output.** The last vector is multiplied by a matrix the size of the vocabulary, giving a score per possible next token. A softmax turns the scores into probabilities.
5. **Sample.** One token is picked (greedy, or sampled with temperature / top-p), appended to the input, and the whole thing repeats.

The "model" is just the weights: billions of numbers in those matrices. Your words become numbers, get multiplied by those numbers, and come back out as words.

## 2. How it learned

- **Pretraining.** The weights start random. The model reads a huge text corpus and, at every position, is penalized for how little probability it gave the real next token (cross-entropy loss). Gradient descent nudges the weights to do better. To predict text well, it has to internalize grammar, facts, reasoning patterns and styles, so those end up encoded in the weights.
- **Post-training.** The raw predictor is then tuned on instruction and chat examples, and further shaped with human or AI preference feedback (RLHF and similar). This is what makes it answer like an assistant. The data and feedback each company chooses are why different models behave differently.

What it does not have: no memory between calls, no access to your files or the live world, and no knowledge after its training cutoff. Everything it knows about you has to be in the input.

## 3. Why it is a mirror

The model learned the distribution of text written by everyone: experts and beginners, careful and sloppy. At inference time it doesn't pick "smart mode". It continues the text it was given in the way that is most probable **given that text**.

So the output is conditioned on the input:

- A vague, low-effort prompt looks like the start of a low-effort exchange, so the most likely continuation is generic.
- A precise prompt with domain vocabulary, constraints and examples looks like an expert exchange, so the likely continuation is expert-level.

Mechanically, your tokens change the activations in every layer, which shifts which features and patterns the network uses. Different words, different internal state, different answer. That's the mirror.

## 4. Context is the entire input

Everything the model conditions on in one call is the context:

- the provider's **system prompt** (hidden instructions)
- your **prompt**
- **files and tool results** the harness reads into the chat
- the **conversation so far**, both sides

It all has to fit in the **context window**, a fixed token budget per call. The model re-reads the whole window to produce every new token, so:

- **Hard limit.** Past the window, the harness must summarize or drop earlier content.
- **Cost and speed.** More tokens means more compute per token generated.
- **Quality degrades with length.** Attention is spread over more tokens, and models are measurably worse at using information buried in the middle of long inputs. Irrelevant context also competes with the parts that matter.

Practical consequences:

- One chat per job. Start fresh when it drifts.
- Put durable knowledge (goals, specs, conventions, examples) in **files** the agent loads when relevant. Files are the long-term memory the model doesn't have.
- Load only what the task needs. More context is not always better.

**In-context learning** is the upside: examples in the prompt steer the output distribution with no retraining. Two or three good examples of the output you want are often worth more than a paragraph of instructions.

## 5. The test that shows the limit

1. Ask: "What is the best-selling product in my industry?" It answers from patterns in its training data.
2. Ask: "What is MY best-selling product?" It can't. Your sales data was never in its training set or its context.

It isn't a reasoning failure. It's missing input. Give it your docs and numbers (in context or through tools) and it can do real work on your business.

## 6. Why it makes things up, and the fix

The model outputs the most probable continuation, not a verified fact. When the right answer isn't strongly represented in its weights or its context, a fluent but wrong continuation can still be the most probable one. That's a hallucination.

The fix is **grounding**: let the model call tools and condition on real results.

- The harness describes available tools to the model.
- The model emits a structured tool call (search the web, read a file, run code).
- The harness executes it and inserts the result into the context.
- The model continues, now conditioned on real data.

Example: an old model asked "who is the president?" gives whoever held office in its training data. The same model with a web search tool looks it up and answers correctly.

The single biggest quality lever for an agent is making it **verify its own output in the real world**:

- **Code:** run the tests and read the errors.
- **Images and video:** render, screenshot, and inspect the result with vision.
- **Facts:** search, then cite the source.

## 7. Make the mirror work for you

- State the goal, the audience and what "good" looks like, not just the task.
- Use the vocabulary of the domain. It pulls the model toward expert text.
- Give constraints and 2 to 3 examples of the output you want.
- Supply the context it cannot know: your data, your rules, your past decisions.
- Keep lasting context in files and load only what the task needs.
- Keep chats short and focused. Restart when quality drops.
- Require verification with tools before it hands work back.
- When an answer is weak, debug the input first.

## Starter prompts

```
Before you start, ask me up to 5 questions about the goal, the audience, constraints and what a great result looks like. Then do the task.
```

```
Context for this whole chat: <goals, constraints, data, 2-3 examples of good output>. Use only this plus tool results. If something you need is missing, say what it is instead of guessing.
```

```
When you finish, verify the result with a tool (run it, search it, or look at it), then tell me exactly what you checked and what you could not check.
```

## Want the full lesson?

This is the short version. The full video lesson on AI models goes deeper: training, why models from different companies behave differently, the model sizes and when to use each, and how all of this sets up context engineering.

It's all inside my Skool community, **Agent Architects**: https://www.skool.com/agent-architects
