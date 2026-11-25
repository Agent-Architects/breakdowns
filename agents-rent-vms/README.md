# My agents rent their own computers: the scripts and rules I give them

You commented VM, so here's the full breakdown.

**The short version.** My agents don't run heavy work on my own computer. When a job needs real compute, an agent rents a Linux box from Hetzner or DigitalOcean, joins it to my private Tailscale network, sets it up with one script, copies the files over, does the job there, copies the result back, and deletes the box. A box costs cents an hour and billing stops when it's deleted. Below are the three scripts they use, the rules I put in their instructions, and a prompt to get your own agent doing it.

## Why let your agents rent computers

In the video I give four reasons.

1. **They can do way more for you.** "They can render more motion graphics on videos, they can do 3D renders, they can fine-tune their own AI model." And for software: "you're running a bunch of tests, and if you're doing that all serially, one at a time, on your own computer, it could be a lot faster if you just parallelized that on a bunch of Linux VMs."
2. **It's really cheap.** "You can rent a bunch of VMs from Hetzner or DigitalOcean that cost only a few cents an hour and allow you to parallelize your work so much more." I render many videos at the same time and run tests in parallel, each on its own box.
3. **Your agents can run 24/7.** If you don't have your own always-on machine, put the agents on a VM "so you can have agents running for you all the time, texting you, being your personal assistants, working around the clock."
4. **They allocate their own compute when they need it.** The agent decides it needs a box, rents one, uses it, gives it back. You don't babysit servers.

## What it costs

Both providers I use bill by time, and billing only stops when the box is **deleted**.

| Provider | Example box | Price (excl. VAT) | Billing rule |
|---|---|---|---|
| Hetzner, cost-optimized | CX43: 8 vCPU, 16 GB | from EUR 0.0264 per hour | per hour, rounded up; a 5 minute box is billed as 1 hour |
| Hetzner, regular performance | CPX52: 12 vCPU, 24 GB | from EUR 0.1370 per hour | same |
| Hetzner, dedicated vCPU | CCX33: 8 dedicated vCPU, 32 GB | from EUR 0.1891 per hour | same |
| DigitalOcean Droplets | many sizes | see their pricing page | per second since Jan 1, 2026, minimum 60 seconds or $0.01 |

Prices from the [Hetzner Cloud pages](https://www.hetzner.com/cloud/) and the [DigitalOcean Droplet pricing page](https://www.digitalocean.com/pricing/droplets), checked Nov 25, 2026. The exact price depends on the location, and these change, so check before you rely on them.

Two billing facts that matter more than the price:

- **A powered-off box still bills.** Hetzner's billing FAQ: "We will bill you for each cloud server until you choose to delete them. Even if you aren't actively using your server, we will bill you for it." So "shut it down" is not the rule. "Delete it" is.
- **The monthly price is a cap, not what you pay.** Hetzner says a server's bill "will never exceed its monthly price cap" and if you delete it earlier you only pay the hourly rate. A box that lives two hours costs two hours.

Macs are different. Apple's license means cloud Macs come with a minimum: AWS bills EC2 Mac "per second with a 24-hour minimum allocation period to comply with the Apple macOS Software License Agreement" ([AWS EC2 Mac](https://aws.amazon.com/ec2/instance-types/mac/)). So a Mac box only makes sense for a day of work, not a 10 minute job.

## How it works

```text
agent decides it needs compute
  -> hcloud.py create render-1:ccx33          rent the box, cloud-init joins it to Tailscale
  -> wait until it shows up on the tailnet    about 1 to 3 minutes
  -> ssh root@render-1 bootstrap.sh           non-root user, key-only SSH, egress guard, your tools
  -> copy the inputs over, run the job as the worker user, copy the result back
  -> check the result is saved where it belongs
  -> hcloud.py delete render-1                billing stops
idle-guard.py, every 15 minutes              backstop: deletes any box an agent forgot
```

Three design choices do most of the work:

- **No public doors.** Every box gets a firewall with no inbound rules. Hetzner: "If you do not set any rule, all inbound traffic will automatically be blocked and all outbound traffic will automatically be permitted" ([Hetzner Firewalls](https://docs.hetzner.com/cloud/firewalls/overview/)). The box joins my Tailscale network on first boot, so SSH goes over Tailscale and nothing on the box is reachable from the internet.
- **Keys never pass through chat.** The API token and the Tailscale auth key live in files on my machine. The scripts read them and never print them, so they never end up in the agent's context or a log.
- **Jobs can't reach back.** The job runs as a normal user on a rented machine, often running code or tools I didn't write. The egress guard stops that user from reaching my other devices over Tailscale or reading the cloud metadata service, where the auth key sits in the box's cloud-init data.

## The scripts

All three are in this folder. Python standard library and bash only, no SDK to install.

### hcloud.py: rent, list, delete

[`hcloud.py`](hcloud.py) talks to the [Hetzner Cloud API](https://docs.hetzner.cloud/reference/cloud).

```bash
python3 hcloud.py create render-1:ccx33 --location nbg1   # Ubuntu 24.04, joins your tailnet on boot
python3 hcloud.py firewall                               # no-inbound firewall on every agent box
python3 hcloud.py list
python3 hcloud.py delete render-1
```

On create it uploads your SSH public key once, labels the box `managed-by=agent` (so the guard knows it's an agent box), and passes a small cloud-init script that installs Tailscale with the [official install script](https://tailscale.com/install.sh) and runs `tailscale up` with your auth key and the box name as the hostname. After that you reach the box by name, like `ssh root@render-1`.

If a type is out of stock in one location, try the next: `for l in nbg1 fsn1 hel1; do python3 hcloud.py create render-1:ccx33 --location $l && break; done`.

Using DigitalOcean instead? Same shape: their [API](https://docs.digitalocean.com/reference/api/digitalocean/) has create, list and delete for Droplets, a firewall resource and a `user_data` field for cloud-init. Ask your agent to write `do.py` with the same four commands.

### bootstrap.sh: set up a fresh box

[`bootstrap.sh`](bootstrap.sh) runs once as root, from your machine, over SSH:

```bash
ssh root@render-1 "WORKER_PUBKEY='$(cat ~/.ssh/agent_box_ed25519.pub)' bash -s" < bootstrap.sh
```

It installs the basics, creates a `worker` user with `~/jobs`, turns off password logins, and installs the egress guard as a systemd service so it survives a reboot. There's a marked spot for your own tools. Mine puts a pinned ffmpeg build and whisper.cpp there for video work. Pin versions, so every box comes out the same and a rerun is safe. It ends with one `BOOTSTRAP_RESULT` line (CPUs, RAM, free disk, Tailscale) so the agent can check it in one read.

### idle-guard.py: the cost guard

[`idle-guard.py`](idle-guard.py) is the backstop for the one rule that matters most. It lists every agent box with its age and cost so far, and deletes boxes that are idle.

```bash
python3 idle-guard.py           # report only
python3 idle-guard.py --apply   # also delete idle boxes
```

A box counts as busy when the file `~worker/jobs/BUSY` exists on it (your job script creates it at the start and removes it at the end) or when you've put a keep lock in `~/.config/agent-boxes/keep/<box-name>`. A box it can't reach counts as busy for its first 2 hours, so a box that is still booting never gets deleted. Anything else idle for 30 minutes goes.

Run it every 15 minutes with cron or launchd. On a Mac, a launchd job is the reliable choice because it survives restarts. One crontab line also works:

```bash
*/15 * * * * /usr/bin/python3 /path/to/idle-guard.py --apply >> ~/.config/agent-boxes/idle-guard.log 2>&1
```

## One-time setup (the human part)

Only three things need you. Everything else your agent can do.

1. **A Hetzner Cloud account, a project, and an API token** with read and write access (Cloud Console, your project, Security, API tokens). New accounts start with limits on how many boxes and dedicated cores you can have. When we hit them, the API said `dedicated core limit exceeded` or `resource_limit_exceeded`. Hetzner raises them on request.
2. **A Tailscale auth key.** In the Tailscale admin console, Settings, Keys. Tailscale's docs explain the options ([auth keys](https://tailscale.com/kb/1085/auth-keys)). Reusable keys "can be very dangerous if stolen", so prefer a one-off or short-lived key, and make it ephemeral, so the box is "auto-removed shortly after going offline" from your tailnet ([ephemeral nodes](https://tailscale.com/kb/1111/ephemeral-nodes)).
3. **Put both keys in files, not in chat.** `~/.config/agent-boxes/hcloud_token` and `~/.config/agent-boxes/ts_authkey`, mode 600. If you're on your phone, have your agent open a one-time local form over Tailscale where you paste them, which writes the files and exits. Then the key never touches the chat at all.

Your agent makes its own SSH key: `ssh-keygen -t ed25519 -f ~/.ssh/agent_box_ed25519 -N ""`.

## The rules I give my agents

This is the block in my agents' instruction files. Paste it into your `CLAUDE.md` or `AGENTS.md` and change the paths.

```markdown
## Rented compute (cloud boxes)

- Nothing heavy runs on this computer. Rendering, encoding, transcribing, big test runs,
  model training and big downloads run on a rented box.
- Rent with `python3 ~/agent-boxes/hcloud.py create <name>:<type>`, then
  `python3 ~/agent-boxes/hcloud.py firewall`. Name boxes after the job (render-lesson-3, test-pr-412).
- Set up every new box with bootstrap.sh before use. Run jobs as `worker`, never as root.
  Touch ~/jobs/BUSY when a job starts and remove it when it ends.
- Size it: use the smallest type that finishes in a reasonable time. Say the hourly price
  before you create a box bigger than <your limit, e.g. 16 vCPU>.
- Spending limit: never more than <N> boxes at once and never more than <EUR X> a day
  without asking me first.
- Keys: read them from ~/.config/agent-boxes/. Never print, log, paste or commit them.
  Never put a key in a chat message or a file inside a repo.
- Delete the box the second the work is saved. "Saved" means the result is in its real
  home (Drive, the repo, the release) and you checked it there, not just "the job finished".
  Then run `hcloud.py list` and confirm the box is gone.
- Powered off is not deleted. A stopped box still bills.
- When I asked to review the result first, keep the box until I approve, then delete it.
- If you are unsure whether a box is still needed, ask me. Never leave a box running overnight
  without telling me which box, why, and what it costs per hour.
```

The "delete when saved" rule plus the guard is what keeps the bill at cents. Without the guard, one forgotten box costs more than a hundred short jobs.

## Copy-paste prompt: let your agent set this up

Run this in your coding agent (Claude Code, Codex or any agent with a shell) from the folder where you keep your tools.

```text
Set me up so you can rent your own Linux computers for heavy work.

1. Copy hcloud.py, bootstrap.sh and idle-guard.py from
   https://github.com/Agent-Architects/breakdowns/tree/main/agents-rent-vms into ~/agent-boxes/.
   Read all three before running anything.
2. Make an SSH key at ~/.ssh/agent_box_ed25519 (no passphrase).
3. I will put a Hetzner Cloud API token and a Tailscale auth key into
   ~/.config/agent-boxes/hcloud_token and ~/.config/agent-boxes/ts_authkey (mode 600).
   Tell me exactly where to click to create each one. Never ask me to paste a key into chat,
   and never print one.
4. Test the full loop with the cheapest type: create test-1, run `hcloud.py firewall`,
   wait until test-1 shows up in `tailscale status`, run bootstrap.sh on it, run
   `nproc && df -h` as worker, then delete it and show me `hcloud.py list` is empty.
   Tell me how long it took and what it cost.
5. Install idle-guard.py --apply as a job that runs every 15 minutes and survives restarts
   (launchd on macOS, cron or a systemd timer on Linux). Show me one report run.
6. Add the "Rented compute" rules from the README to your instruction file
   (CLAUDE.md or AGENTS.md), with a limit of <2> boxes and <EUR 5> a day.
```

## Security checklist

- [ ] Firewall with no inbound rules on every box; SSH only over Tailscale
- [ ] Password login off (`bootstrap.sh` does this)
- [ ] Jobs run as `worker`, not root
- [ ] Egress guard on: jobs can't reach your other devices or the metadata service
- [ ] Tailscale auth key is one-off or short-lived, and ephemeral
- [ ] API token and auth key only in files with mode 600, never in a repo, chat or log
- [ ] No personal credentials on the box: copy files to it, don't log it into your Google, GitHub or email
- [ ] After delete, the box is gone from `hcloud.py list` (ephemeral Tailscale devices clean themselves up; otherwise remove it from the Tailscale machines page)

## What goes wrong

- **Forgetting to delete.** The most expensive mistake and the most common one. The rule plus the guard fixes it.
- **Shutting down instead of deleting.** A stopped box still bills on Hetzner.
- **Deleting before the result is safe.** "The job finished" is not "the result is saved". Check the result in its real home first, then delete.
- **Out of stock or over the limit.** Some types are sold out in some locations, and new accounts have caps. Loop over locations, fall back to a similar type, or ask Hetzner to raise the limit.
- **The box isn't ready yet.** Cloud-init needs a minute or two before Tailscale is up. Wait for the box to show up in `tailscale status`, then check `cloud-init status` says done before bootstrapping.
- **A key ends up in chat.** Then it's in the transcript. Rotate it. Use files or a one-time form instead.
- **Running jobs as root with your tailnet open.** A bad script, or a tool you downloaded, can then reach every device you own. Keep the egress guard on.
- **Different setup on every box.** Unpinned tools give different results and make bugs hard to trace. Pin versions in `bootstrap.sh`.
- **Picking a giant box.** Parallel small boxes usually beat one huge box, and a 32 vCPU box is wasted on a job that only uses 8. Measure one run, then size.
- **Using a Mac box for a short job.** The 24 hour minimum makes it a full day's bill.

## Sources

| Claim | Source |
|---|---|
| Hetzner CX43, CPX52, CCX33 specs and hourly prices | [Hetzner Cloud](https://www.hetzner.com/cloud/), [cost-optimized](https://www.hetzner.com/cloud/cost-optimized), [regular performance](https://www.hetzner.com/cloud/regular-performance), [general purpose](https://www.hetzner.com/cloud/general-purpose) |
| Billed until deleted, even when not in use; usage rounded up to whole hours; monthly price is a cap | [Hetzner Cloud billing FAQ](https://docs.hetzner.com/cloud/billing/faq/) |
| No firewall rules: all inbound blocked, all outbound allowed | [Hetzner Firewalls overview](https://docs.hetzner.com/cloud/firewalls/overview/) |
| Server, SSH key and firewall API used by hcloud.py | [Hetzner Cloud API reference](https://docs.hetzner.cloud/reference/cloud) |
| DigitalOcean per-second billing from Jan 1, 2026, 60 second or $0.01 minimum | [DigitalOcean Droplet pricing](https://www.digitalocean.com/pricing/droplets) |
| DigitalOcean API | [DigitalOcean API reference](https://docs.digitalocean.com/reference/api/digitalocean/) |
| EC2 Mac billed per second with a 24 hour minimum for the macOS license | [AWS EC2 Mac instances](https://aws.amazon.com/ec2/instance-types/mac/) |
| Reusable auth keys "can be very dangerous if stolen" | [Tailscale auth keys](https://tailscale.com/kb/1085/auth-keys) |
| Ephemeral devices are auto-removed shortly after going offline | [Tailscale ephemeral nodes](https://tailscale.com/kb/1111/ephemeral-nodes) |
| cloud-init `runcmd` | [cloud-init modules](https://cloudinit.readthedocs.io/en/latest/reference/modules.html) |

Docs checked on Nov 25, 2026. Prices and limits change, so check the links before you rely on a number.

## Want more like this?

More agent breakdowns and the full lessons are inside my Skool community, **Agent Architects**: https://www.skool.com/agent-architects
