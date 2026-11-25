<!-- BLOCKED: replace SLOTWISE_REPO_URL once the Slotwise repo is public. Do not merge before. -->
# My agents built my own Calendly. Here's yours.

You commented CALENDAR, so here's the full breakdown.

**The short version.** Slotwise is the booking app my agents built for me, cleaned up and open-sourced under MIT. You publish booking pages, people pick a free time, and the booking lands on your Google Calendar. It runs on Cloudflare's free plan or on any server with Node. The repo ships a setup runbook, so you clone it, open it in Claude Code (or Codex, or any agent), type `/setup`, and your agent does the build, deploy, domain, Google setup and a real test booking. You only do the logins, the consent screens and any payment. At the end it offers to brand it as yours.

Repo: **SLOTWISE_REPO_URL**

## Why I built my own

In the short I say: "I literally just asked the agent to one-shot a clone of Calendly." It went and looked at the website, used my verification skill, hosted it on Cloudflare, and "it actually set up the full Google OAuth client itself, literally just using computer use." I came back to it, it was working, and my first client call was booked through it a couple of hours later.

The moral of the story: if you're building software for yourself, not for a bunch of other users, "you can pretty much do anything that you want and host it on your own machine or on your own Cloudflare account."

Slotwise is that app, with everything personal stripped out and a setup runbook added, so your agent can do the same setup for you with your own accounts and your own branding.

## What it does

Everything here is in the repo's README and docs today:

- **Booking pages** per owner (`/<username>`) and per event type (`/<username>/<slug>`), shown in the guest's time zone.
- **Event types** with one or more durations, slot interval, buffers, minimum notice, booking window, daily limit, custom questions, location (Google Meet, Zoom, phone, in person, custom) and color.
- **Availability**: weekly hours, date overrides, and several named schedules.
- **Google Calendar sync**: busy times on the calendars you pick hide slots. Bookings are written to the calendar you pick (with a Meet link if you want one) and moved or removed when someone reschedules or cancels.
- **Manage links**: guests cancel or reschedule from a private link. You can cancel, reschedule or ask them to reschedule.
- **No double booking**, even when two people hit Book at the same moment.
- **Email** through Resend, or a log outbox when you haven't set one up.
- **Agent friendly**: one versioned JSON API (`/api/v1`) that the web UI and a CLI both use, owner API tokens with read or write scopes, CSV export. Every CLI command prints JSON, so your agent can do anything the UI can.
- **Your brand**: name, colors, logo, theme and font from one command.

## How it works

Plain words, no code needed.

**One app, thin hosting adapters.** All the logic lives in one place (`src/core/`) and every route in one hosting-neutral file. Then there are two small entry files: one for Cloudflare Workers, one for Node. Two adapters ship and are tested:

| Where it runs | Database | Status in the repo |
|---|---|---|
| Cloudflare Workers | D1 (Cloudflare's SQLite) | Reference path. Tested up to a `wrangler deploy --dry-run`; a real deploy needs your account |
| Your own server, Node 22.13+ | One SQLite file (`node:sqlite`) | Tested end to end |

Fly.io, Railway, Render and Docker should work with the Node adapter, but the docs say plainly they were not tested. No Dockerfile ships.

**The database.** Same SQL on both hosts. Migrations are plain SQL files, applied in order, and only ever add things. On Cloudflare one Worker serves the API and the web pages, and one D1 database holds everything, including the rate limit counters, so there's nothing else to set up.

**Google Calendar sync.** You create your own Google OAuth client (your agent walks you through it). Slotwise asks for five scopes only: `openid`, `email`, list your calendars, read free/busy, and create or edit events. It never asks for full calendar access. The tokens are encrypted with AES-256-GCM before they're stored.

**The booking flow:**

1. A guest opens your link. Slotwise takes your hours, removes buffers, notice and existing bookings, then asks Google which of your chosen calendars are busy and hides those times.
2. The guest picks a time. The server checks that exact slot again, live. If Google can't be reached, it refuses the booking instead of guessing.
3. The booking is saved with one conditional SQL insert, so if two people race for the same slot exactly one wins and the other gets "That time is no longer available."
4. The event is written to your Google Calendar, with the guest as an attendee and a Meet link if you set one.
5. The guest gets a private manage link to cancel or reschedule. Cancel removes the event from your calendar.

## Let your agent set it up

The repo is built for this. `AGENTS.md` works for any agent, `CLAUDE.md` points at it, and the full runbook is `skills/setup-slotwise/SKILL.md`, with copies registered for Claude Code (`.claude/`) and agents that read `.agents/skills/`.

The command:

- **Claude Code**: `/setup`
- **Codex and other agents**: "Set up Slotwise for me by following AGENTS.md"

It saves progress in `.setup/state.json`, so if anything stops halfway, run it again and it picks up where it left off.

### What your agent does vs what you click

| Step | Your agent | You |
|---|---|---|
| Interview | Asks 5 questions with defaults: where to host, domain, Google Calendar, real email, your profile | Answer, or say "defaults" |
| Local check | `npm ci`, typecheck, tests, then a throwaway local run that signs up an owner, books and cancels | Nothing |
| Cloudflare | Dry run, deploy, database, migrations, secrets | Create the account, click **Allow** on `npx wrangler login`, confirm it's the right account |
| Own server | Install, build, env file, systemd, Caddy for HTTPS | Rent the server, add your SSH key if needed |
| Domain | Deploys with `--domain` so Cloudflare makes the DNS record and certificate | Buy the domain, change nameservers at your registrar |
| Google Calendar | Clicks through Google Cloud console with its browser tool (or gives you the exact clicks): project, Calendar API, consent screen, scopes, OAuth client, then wires the secret in | Sign in to Google Cloud, accept terms, later click **Connect** and **Allow** in Slotwise |
| First owner | Tells you where the setup code file is, logs the CLI in, sets your hours and event types | Sign up with your own password. It never asks for it in chat |
| Test booking | Books and cancels a real slot; with your OK, checks a busy event hides slots and the booking shows up and disappears in your calendar | Say yes before it touches your real calendar |
| Branding | Applies name, colors, logo, theme; can copy the look of a site you point at | Pick, or send a site you like (and a logo you have the right to use) |
| Payment | Never | Anything you choose to buy |

Two rules in the runbook I like. Secrets never go through the chat: they live in files under `.setup/secrets/` with tight permissions. And if something breaks that the runbook doesn't cover, the agent stops and reports instead of patching code to make it pass.

## Copy-paste prompt for your agent

Paste this into Claude Code, Codex, or whatever agent you use, in an empty folder.

```text
Set up Slotwise, a self-hosted booking app, for me.

1. Clone SLOTWISE_REPO_URL into a folder called slotwise and open it.
2. Read AGENTS.md, then follow skills/setup-slotwise/SKILL.md phase by phase.
   (In Claude Code you can just run /setup.)
3. Interview me first. Defaults are fine unless I say otherwise:
   Cloudflare free plan, no custom domain yet, Google Calendar on, no real email.
4. Do everything you can yourself. Use your browser or computer-use tools for the
   Cloudflare and Google Cloud dashboards once I've signed in. Hand me only the
   steps that need a human: account sign-ups, logins, consent screens, my own
   password, payment. One step at a time, tell me exactly what to click, then wait.
5. Never put a secret in the chat. Keep them in .setup/secrets/ as the runbook says.
6. Ask me before you create a test booking or busy event on my real calendar,
   and clean up anything you create.
7. Before finishing, offer me branding: product name, colors, light/dark/auto
   theme, logo, or copy the look of a site I point you at. Show me the values
   with --dry-run before you apply them, then redeploy.
8. If something fails that the runbook doesn't cover, stop and tell me the
   command, the output and what you tried. Don't edit the source to get past it.
9. When done, give me my booking link, my admin URL, where each secret lives
   (paths only), and how to redeploy.
```

Want to see it first with zero accounts? The repo has a two minute local check:

```bash
git clone SLOTWISE_REPO_URL slotwise && cd slotwise
npm ci
npm run --silent setup:local   # throwaway server: owner, event type, booking, cancel, prints JSON
npm run dev:node               # then click around at http://localhost:8787 (mock calendar)
```

Branding by hand, if you'd rather skip the agent for that bit:

```bash
npm run brand -- --name "Acme Bookings" --primary "#1d4ed8" --accent "#f97316" --theme auto --logo ./logo.svg --dry-run
npm run build    # then redeploy
```

## What it costs

Checked on Nov 25, 2026:

- **Slotwise**: free, MIT license.
- **Cloudflare Workers Free**: 100,000 requests per day, 10 ms of CPU time per invocation. The Paid plan has a minimum of $5 USD per month per account ([Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/)).
- **Cloudflare D1 on Workers Free**: 5 million rows read per day, 100,000 rows written per day, 5 GB storage total, 10 databases ([D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/)). Slotwise uses one database.
- **Google Calendar API**: the Standard Tier is "enabled by default at no cost" and usage on it "never produces charges on a Google Cloud bill" ([Calendar API quotas](https://developers.google.com/workspace/calendar/api/guides/quota)). The runbook says no billing account is needed for it.
- **Your own server instead**: whatever your VPS costs. The self-host doc says 1 vCPU and 512 MB RAM is plenty.
- **A custom domain or Resend email**: optional, priced by whoever you buy them from.

## What goes wrong

- **Your calendar disconnects after a week.** Google gives a refresh token that expires in 7 days to an External app in "Testing" status ([Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)). Fix: Publish the app and click through the "unverified app" screen. Google says personal use by you and a few people you know doesn't need verification ([brand verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/brand-verification)).
- **`redirect_uri_mismatch`.** The redirect URI must match exactly: scheme, host, port, no trailing slash. It's always `<your app url>/oauth/google/callback`.
- **"OAuth callback does not match the signed-in owner".** You hit Connect on a different hostname than your app URL. Sign in at the app URL and retry.
- **Custom domain won't attach.** Cloudflare needs an active zone on your account, and you can't put a custom domain on a hostname that already has a CNAME record ([Custom Domains](https://developers.cloudflare.com/workers/configuration/routing/custom-domains/)). Also: once you deploy with `--domain`, the old `workers.dev` address stops answering. Use the domain everywhere.
- **Waiting for a confirmation email that never comes.** The default is a log outbox. Real email needs Resend and a sending domain you control.
- **The deploy refuses to run.** Without a terminal it won't touch a Cloudflare account unless `--yes` is passed, and the runbook has your agent show you the account first. That's on purpose.
- **Rotating `ENCRYPTION_KEY`.** Don't. Stored calendar connections become unreadable and you reconnect. Bookings are fine.
- **Local sign-in or Google breaks on your laptop.** Open `http://localhost:8787`, not the numeric loopback address the server prints when it starts. Google accepts localhost redirects, and the cookie has to land on the same host.
- **Scaling Node to several copies.** SQLite is single-writer. Run one instance. On Railway or Render without a persistent disk, every deploy starts empty.
- **Forgot your password.** There's no email reset yet. The host runs `scripts/admin-reset-password.mjs`, which signs you out everywhere and revokes API tokens.
- **Hosts other than Cloudflare and plain Node.** Fly, Railway, Render and Docker are documented but untested. Expect to do a bit of work.

## Sources

| Claim | Source |
|---|---|
| Features, hosting table, config, branding, CLI, security notes, `/setup` and AGENTS.md shortcuts | Slotwise repo (SLOTWISE_REPO_URL): `README.md`, `AGENTS.md` |
| Interview, phases, human-only steps, secrets in files, stop instead of patching, state file and resume, test booking, branding from a reference site | Slotwise repo: `skills/setup-slotwise/SKILL.md`, `.claude/commands/setup.md` |
| Adapter layer, tested vs untested hosts, single SQLite writer | Slotwise repo: `docs/HOSTING.md` |
| Five scopes, no full calendar scope, AES-256-GCM, redirect URIs, Testing vs Publish, troubleshooting | Slotwise repo: `docs/GOOGLE-OAUTH-SETUP.md`, `src/adapters/google-calendar.ts` |
| Deploy steps, `--yes`, `--domain`, workers.dev turned off with a domain, password reset | Slotwise repo: `docs/DEPLOY-CLOUDFLARE.md` |
| Server size, Caddy, systemd | Slotwise repo: `docs/SELF-HOST.md` |
| Recheck at booking, one conditional insert, calendar write, manage link | Slotwise repo: `src/core/service.ts`, `skills/verify-slotwise/features/no-double-booking.md` |
| Scope meanings: free/busy, events, calendar list | [Google Calendar API scopes](https://developers.google.com/workspace/calendar/api/auth) |
| 7 day refresh token for External apps in Testing | [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2) |
| Personal use exception, unverified app screen, user cap | [Google brand verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/brand-verification) |
| Calendar API Standard Tier at no cost | [Calendar API quotas](https://developers.google.com/workspace/calendar/api/guides/quota) |
| Workers Free 100,000 requests per day, 10 ms CPU, Paid minimum $5 per month | [Cloudflare Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/) |
| D1 free limits | [Cloudflare D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/) |
| Custom Domains create DNS and certificates, need an active zone, no existing CNAME | [Cloudflare Workers Custom Domains](https://developers.cloudflare.com/workers/configuration/routing/custom-domains/) |

Docs checked on Nov 25, 2026. Prices and Google's OAuth rules change, so check the links before you rely on a detail.

## Want more like this?

More agent breakdowns and the full lessons are inside my Skool community, **Agent Architects**: https://www.skool.com/agent-architects
