# Give your agent the right tools

Your agent can write the perfect plan and still get stuck at the login screen. It needs a way to interact with the apps where the work happens.

This is the full breakdown behind the browser automation, MCP vs CLI, and CLI tools videos. You'll learn five ways to connect an agent to your work, when each makes sense, and how to turn a successful browser workflow into something you can run again.

## What a tool actually does

The model decides what to do. The harness is the app running the model, and its tools let the agent act: read a file, run a command, search a website, or interact with another app. Which tools are available depends on that harness and your settings.

An API is an interface software can call directly. A lot of agent tools wrap an API. Others work with local files, browser pages, or the desktop. You don't need an API for every task, but an existing supported interface can save you from rebuilding the same interaction yourself.

## Pick a starting point

| Your task | Start with | What to check |
|---|---|---|
| A custom local task with no existing tool | Script | Inputs, dependencies, and how you'll check the result |
| A service with a useful command-line tool | CLI | Commands, account, output controls, and access |
| A service already connected through your agent app | MCP | Available operations, permissions, and result size |
| A website workflow with no suitable direct tool | Browser automation | Correct login, page state, and evidence the action worked |
| A desktop app or workflow across app windows | Computer use | Window focus, OS permissions, and visible results |

These can overlap. A CLI is a command surface. Browser automation is an interaction method. A command can drive a browser, and an MCP tool can call an API or run code behind the scenes.

## 1. Scripts: build the custom step

A script is a piece of code your agent can write and execute. It might convert a folder of CSVs, check filenames, or call an API that doesn't have a useful existing integration.

Scripts are a good fit when the task is specific enough that an existing tool doesn't cover it. Start small: one input, one output, and a clear way to tell whether it worked. You can keep the script and reuse it once the behavior is proven.

Try this:

```text
Write a script that reads the CSV files in this sample folder and reports which files are missing the invoice_id column. Print filenames and missing columns. Leave the source files unchanged. Run it on the sample and show the result.
```

The tradeoff is maintenance. Someone has to handle dependencies, error cases, and changes to the service or file format. Your agent can help with that, but a script still needs a checked result.

## 2. CLI tools: work through commands

A command-line interface lets your agent operate a tool by running commands. GitHub's `gh` CLI is one example. Instead of clicking through a repository, an agent can ask for a specific list of issues.

Here's a read-only example for a machine where GitHub CLI is already installed and has the required access:

```bash
gh issue list --repo cli/cli --state open --limit 5 \
  --json number,title,url \
  --jq '.[] | "#\(.number) \(.title) \(.url)"'
```

This requests up to five open issues and prints their numbers, titles, and links. It doesn't create or edit issues. The flags and fields are documented in the [GitHub CLI issue-list manual](https://cli.github.com/manual/gh_issue_list).

Commands are composable: you can filter a result, transform it, and pass it to another step. That can keep a workflow compact. Check that each step receives the format it expects.

Installing a CLI doesn't automatically give every agent access. The executable must be reachable in that process's `PATH`, under the right OS user, with the required credentials and network access. A sandbox can restrict it too. If it works in your terminal but fails in the agent, compare those environments.

Help your agent discover the tool with a short instruction or skill: what the command is for, where its help lives, and which account or project to use. Start with `gh issue list --help` before guessing flags.

## 3. MCP: connect tools through the agent app

Model Context Protocol gives an agent client a standard way to discover and call tools. A server exposes named tools with input schemas. The client controls how those tools are presented to the model. [MCP tool specification](https://modelcontextprotocol.io/specification/latest/server/tools).

This is useful when your harness already has a good integration for a service. You can work with the available operations without designing a new command wrapper.

Check the scope in your harness settings. A connection may be available to your user, one project, or another configured scope. The settings file's location alone doesn't define access across all agent apps. Login and service permissions still apply.

### MCP vs CLI and tokens

Compare the actual workflow. A CLI that returns only three fields can save context compared with a tool returning a full record. A noisy CLI can waste context too.

MCP discovery and result handling depend on the client and server. Some clients load tools on demand; some servers support compact results. Neither interface guarantees lower token use. MCP calls can also be chained by the harness or agent. Choose based on the available operations, output size, and steps needed to finish your task.

## 4. Browser automation: work with the website

Browser automation lets your agent navigate pages, inspect their structure, fill fields, and click controls. It's useful for the niche website your industry depends on, especially when no suitable API, CLI, or integration exists.

First prove the workflow interactively. Have the agent read the page, perform a small task, and check the result. A click succeeding doesn't prove that the website saved the change or returned the right records.

Try this first task on a website you have permission to automate:

```text
Open the supplier portal in the approved browser session. Find the five most recent orders and return each order's reference, date, and status. Check those values against the visible order list. Leave orders unchanged.
```

### Turn a successful run into a reusable command

Once the workflow works, use that successful run as the starting point for an adapter. [OpenCLI](https://github.com/jackwener/OpenCLI) supports reusable website adapters exposed as commands. Its [extension guide](https://opencli.info/docs/guide/extending-opencli.html) explains the supported ways to keep and install custom adapters.

1. Identify the successful steps, required login, inputs, and expected output.
2. Ask the agent to build an adapter for that specific operation using the current OpenCLI authoring guidance.
3. Give it explicit inputs, such as an order limit, and return only the fields you need.
4. Run it again and compare its output with the website. Include an empty-result case and a logged-out case.
5. Document how to invoke it and what a failure looks like before scheduling it.

Original follow-up prompt:

```text
Use the successful order lookup above to build a reusable OpenCLI adapter. Accept a limit argument and return reference, date, and status. Follow the current OpenCLI adapter-author guidance. Check the output against the page. Report login failures as errors, not as an empty list. Include usage instructions.
```

OpenCLI's browser setup uses a Browser Bridge extension and local daemon with your browser login. Follow the [Browser Bridge setup guide](https://opencli.info/docs/guide/browser-bridge.html) for current requirements. Reusable commands still need maintenance when a site changes. A successful interactive run gives you a tested starting point, not a guarantee that every website can become a reliable command automatically.

## 5. Computer use: work across the desktop

Computer use lets an agent interact with app windows through the mouse, keyboard, and screen. It's useful when the task lives in a desktop app or needs several apps in sequence.

Availability depends on the harness, operating system, and permissions you've granted. Check which app or desktop surface the agent can control. A visible window doesn't mean the agent has permission to operate everything on the machine.

For example, an agent could enter sample data into a desktop app that has no useful direct interface. Have it check the saved record afterward. Window focus, dialogs, and screen layout can all affect the result.

## Connect one workflow and prove it

Pick one repetitive task. Describe its inputs, the account it should use, and the result you expect. Choose the tool that covers the operation, then run a small version you can check yourself.

Give it enough access for that task. Separate reading from actions like sending, deleting, or publishing when you configure permissions. Website text, emails, and tool results are external data; they can contain instructions your agent shouldn't follow as your own request. Keep credentials out of prompts and reusable examples.

When the result is correct, save the command, script, adapter, or skill with its usage instructions. That's how a one-time success becomes a workflow you can repeat.

For the full lesson and more agent workflows, join the [Agent Architects community](https://www.skool.com/agent-architects).

Primary tool documentation checked November 11, 2026. Follow the linked docs for current setup details.
