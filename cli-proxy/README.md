# One proxy for all your AI subscriptions

You commented "proxy", so here's the full breakdown.

I run several Claude subscriptions, a Codex subscription and more behind one small server on my Mac mini. Every agent on every computer I own talks to that one server. I log into each account once, the server rotates requests between them, and I never open a terminal to re-login when one account runs out.

This covers what the tool is, how to set it up, how to share it across machines safely, how I watch every account's resets, and how I hand out one-off private tokens to cloud test sandboxes.

## Read this first: terms of service

Using several consumer subscriptions this way may not be allowed by the companies that sell them. In the video I say it plainly: it "may or may not be allowed, do this at your own risk." I have not asked the providers for permission. They could change their rules, throttle the accounts, or ban them.

- Only use accounts you own and pay for.
- Never share a login with other people or sell access.
- Read your provider's current terms before you build this.
- If you want a setup that is clearly allowed, use the official API with your own API key.

Everything below is how the tool works. Whether you should use it is your call.

## What CLIProxyAPI is

[CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI) is an open source server. You log in to your AI subscriptions through it, and it exposes them as a normal API endpoint on your machine. Clients that speak the Claude, OpenAI or Gemini API formats connect to it instead of connecting straight to the provider. It does the login, token refresh and request forwarding.

It supports Claude, Codex, Gemini and several other providers. Check the repo for the current list.

There is also a desktop app, [EasyCLIProxyAPI](https://github.com/router-for-me/EasyCLIProxyAPI). It adds a graphical settings screen, a tray icon and start/stop buttons for the same server. Use it if you would rather not edit a config file.

## Set it up

### 1. Install

On macOS with Homebrew:

```bash
brew install cliproxyapi
```

Other platforms and Docker are covered in the [repo README](https://github.com/router-for-me/CLIProxyAPI). Run `cliproxyapi --help` to see every login flag.

### 2. Lock down the config

Open the config file. The Homebrew install puts it at `/opt/homebrew/etc/cliproxyapi.conf`. Set three things:

```yaml
server:
  host: "127.0.0.1"   # this machine only, never the whole network
  port: 8317

access:
  api-keys:
    - "<make-up-a-long-random-key>"   # clients must send this
```

Generate the key with something like `openssl rand -hex 24`. This is the key your clients use to talk to the proxy. It is not your Claude password and not a provider key. Treat it like a password anyway.

Leave the management API's remote access off (`allow-remote: false`).

### 3. Log in to each account once

Each login opens a browser OAuth flow:

```bash
cliproxyapi --claude-login      # run once per Claude account
cliproxyapi --codex-login       # run once per Codex account
```

To add a second Claude account, log out of Claude in the browser (or use a private window) so the login screen lets you pick the other account, then run the login again. Every login saves one credential file in the proxy's auth folder. The folder holds live tokens, so keep it private and never commit it. Use `--no-browser` if the machine has no browser and you want to finish the login from another one.

### 4. Start it and check it

```bash
brew services start cliproxyapi
lsof -iTCP:8317 -sTCP:LISTEN -nP
```

You should see it listening on `127.0.0.1:8317` and nothing else. If you see `*:8317`, it is open to your network. Fix the `host` setting first.

## Point your tools at it

On the same machine, tell Claude Code to use the proxy instead of Anthropic. In your Claude Code settings file, add an `env` block:

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:8317",
    "ANTHROPIC_AUTH_TOKEN": "<the-proxy-api-key-from-step-2>"
  }
}
```

Start Claude Code and send one message. If it answers, requests are going through the proxy. The same idea works for any client that lets you set a base URL and a key, including Codex-style and OpenAI-compatible tools.

## Serve it to your other computers

The proxy listens on localhost, so other machines cannot see it. That is on purpose. You bring them to it with a private tunnel. Pick one.

### Option A: SSH tunnel

From the other computer, forward its own local port to the proxy machine:

```bash
ssh -N -L 8317:127.0.0.1:8317 you@your-proxy-machine
```

Now `http://127.0.0.1:8317` on the other computer reaches the proxy. Set the same `ANTHROPIC_BASE_URL` there. Run the tunnel under `autossh` or a launch service so it comes back after a reboot. The reverse form (`ssh -R`, started from the proxy machine) does the same job if only the proxy machine can open connections.

### Option B: Tailscale

Put both machines on the same [Tailscale](https://tailscale.com) network. Then reach the proxy through the proxy machine's tailnet address. The proxy itself still binds to localhost, so put a small forwarder in front that binds only to the tailnet address (the gate below is exactly that). Do not bind the proxy to `0.0.0.0`.

### Never do this

Do not expose the proxy to the public internet, a port forward on your router, or a public tunnel URL. Anyone who finds the address and the key spends your subscriptions, and you cannot tell it from you.

## Rotation: what happens as accounts fill up

Your config has a routing strategy. Mine is `round-robin`:

```yaml
routing:
  strategy: "round-robin"
```

With round-robin, each new request goes to the next account in the list. Other options in the config are `weighted-round-robin` (give bigger plans more traffic) and `fill-first` (use one account until it is spent, then the next).

Two details that matter in practice:

- **Session stickiness.** You can bind a conversation to one account for a while. This keeps prompt caching working, because a cache built on one account does not help a request that lands on another. I keep it on.
- **Failover.** When an account hits its usage limit and the provider rejects a request, the proxy retries the request on another account. Your agent does not see the error. It only sees a failure when every account is out at once.

Limits do not go away. You have the combined headroom of all the accounts, so the day the last one is empty, everything stops until a window resets. That is why I built the dashboard below.

## The dashboard: see every account's resets

This is a small page I built so I can see at a glance which account has room and when the next one frees up. You can build the same thing in a weekend.

### What it shows

- **One row per account.** Name or label, provider (Claude or Codex), plan tier.
- **Two gauges per account.** Percent used in the 5-hour window and in the 7-day window.
- **The next reset time.** Exact date, time and a countdown for each window.
- **A timeline.** One bar per account across the week. Each bar runs from seven days before the account's reported reset to the reset itself, with a line for "now". At a glance you see which accounts reset soon and which just reset.
- **Freshness.** When each number was last checked. Stale data is labeled stale, and a missing reset time shows as "unknown" instead of a guess.
- **Every account stays visible,** even if its usage check fails.

### Where the data comes from

The proxy only forwards requests. It does not tell you how much of each plan is left. The page asks each provider directly, using the same login token the proxy already saved for that account:

1. A small server-side script reads the credential files from the proxy's auth folder.
2. For each Claude account, it calls the provider's usage endpoint with that account's token. The response includes percent used and a reset timestamp for the 5-hour window and the 7-day window.
3. For each Codex account, it calls the equivalent usage endpoint for that provider. It returns the same two windows.
4. It writes only the safe fields (label, plan, percent, reset time, checked-at) into a snapshot file.
5. The page reads the snapshot. The browser never sees a token.

These usage endpoints are not documented public APIs. They are the ones the official apps use, so they can change or disappear without notice. Treat that part as fragile.

Rules that kept mine stable:

- **Cache hard.** Refresh each account at most every two minutes. Hidden browser tabs do not poll.
- **Respect rate limits.** If a usage call returns 429, read `Retry-After`, stop calling for that long, and show the cached values with a banner.
- **One refresh at a time.** Use a lock file so two tabs do not both refresh.
- **Keep secrets server-side.** The script holds the tokens. The page gets the snapshot only.

### Build it

Give your agent this prompt and the proxy's auth folder location:

```text
Build a small local dashboard that shows my AI subscription usage.

Data: a server-side script reads each credential file in my proxy auth folder,
calls each provider's usage endpoint with that account's token, and writes a
snapshot of: label, provider, plan, percent used and reset time for the 5-hour
and 7-day windows, and checked-at. Never send tokens to the browser, logs or files
outside the folder. Cache for 2 minutes, honor Retry-After on 429, and use a lock
file so only one refresh runs at a time.

Page: one row per account with two gauges (5-hour and 7-day), the next reset
time with a countdown, and a week timeline with one bar per account and a "now"
line. Label stale data. Show an unknown reset as unknown. Keep every account
visible even if its check fails.
```

I also run a second small script from the same data. It watches the burn rate across all accounts and, if the pooled plans are projected to run out within about ten minutes, messages my running agents to save their work first. It never stops them. It is a few dozen lines: poll every two minutes, keep twenty minutes of history, compute percent per minute per account, ignore samples from before a reset, and warn once per episode.

## One-off private tokens for cloud sandboxes

I test my agent products in disposable cloud boxes, and those agents need real model replies. I do not want my real credentials on a box I will delete in a few hours. So the boxes never get them.

The pattern is a gate: a small second proxy that sits in front of the real one.

```
sandbox  --token-->  gate  --real proxy key-->  proxy  -->  provider
```

How it works:

1. **The gate is its own tiny server.** It binds only to the private network address (a tailnet), never to a public one.
2. **Each sandbox gets its own random token.** Generate it fresh with `openssl rand -hex 24`. Never reuse one token across two boxes. The gate stores only the token's hash and a box name, so the config file does not hold usable secrets.
3. **A request passes only if all of these match.** The source address is that box's address, the token matches that box's hash, the path is on a short allow list (messages, token counting, model list), the method fits the path, the body is under a size cap, and the model is on an allow list.
4. **The gate swaps the credential.** It forwards the request to the real proxy with the proxy's own key, which only the gate knows. The sandbox's token is never sent upstream, and the real key is refused if a sandbox ever presents it.
5. **It caps concurrency per box,** for example four requests at once, so one runaway agent cannot drain everything.
6. **It logs metadata only.** Time, box name, route, model, status, bytes, milliseconds. Never bodies, headers or keys.

On the sandbox, two environment variables are all you set: the base URL points at the gate, and the key is that box's token. The agent works like normal. The real accounts and the real key never leave the main machine.

### Time-box and revoke

My gate has no built-in expiry. Add one or enforce it by process:

- **Name an end time** when you create the token. A few hours is enough for a test run.
- **Add a backstop job** that removes the box from the gate at the deadline, even if you forget.
- **Revoke by deleting the entry.** Remove the box from the gate config and restart the gate. The token is dead everywhere, even if it is still sitting on the sandbox.
- **Clean the box.** Remove the token from its environment files and shell history, and confirm no process still holds it.
- **One token in one place.** Put it in a single environment file for a single user, not in a repo, a log or a chat.

A better version adds an expiry timestamp to each entry, so the gate refuses the token on its own after the deadline. Ask your agent to add that.

## Security checklist

- [ ] Proxy binds to `127.0.0.1` only. Verify with `lsof -iTCP:8317 -sTCP:LISTEN -nP`.
- [ ] Proxy has a long random client key. Treat it like a password.
- [ ] Management API stays local. Remote management is off.
- [ ] The auth folder and config file are never committed, pasted into chat, or shown on screen.
- [ ] Other machines connect over an SSH tunnel or Tailscale. Never a public port or public URL.
- [ ] Each machine or sandbox has its own token, so you can revoke one without touching the rest.
- [ ] Sandbox tokens have an end time and a removal job. Revocation means deleting the gate entry.
- [ ] Gate allows only the routes, models, body size and concurrency your tests need.
- [ ] Logs never include request bodies, headers or keys.
- [ ] You have a plan for the day an account is banned or a provider changes its rules.
- [ ] You have read your providers' terms.

## What to do next

1. Install it and log in one account. Check that Claude Code answers through `127.0.0.1`.
2. Add a second account and watch requests spread.
3. Ask your agent to build the usage dashboard from the prompt above.
4. Only if you have sandboxes that need real model replies, build the gate.

For the full lesson and more agent workflows, join the [Agent Architects community](https://www.skool.com/agent-architects).

---

## Sources

- CLIProxyAPI: https://github.com/router-for-me/CLIProxyAPI
- EasyCLIProxyAPI desktop client: https://github.com/router-for-me/EasyCLIProxyAPI
- Claude Code settings and environment variables: https://code.claude.com/docs/en/settings
