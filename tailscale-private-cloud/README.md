# Tailscale: your own private cloud for you and your agents

You commented TAILSCALE, so here's the full breakdown.

**The short version.** Put Tailscale on a computer you leave on 24/7 and on every device you own. Now they're all on one private network. Your coding agents build small apps on that computer, put each one behind `tailscale serve`, and send you a link that opens on your laptop, iPad and phone from anywhere, but not for anyone else on the internet. Add Taildrop for files, node sharing for friends and family, and Tailscale SSH for getting into your boxes, and you've got your own little version of the internet.

## What a tailnet is, in plain words

In the video I say: "Tailscale is basically an app that allows you to create your own private network between your devices called a tailnet."

That's really it. You install the app, sign in, and every device you sign in on can talk to every other one like they're on the same Wi-Fi, even when one is at home and the other is on your phone's data in another country. Tailscale's docs call it "a peer-to-peer mesh network (known as a tailnet)" built on WireGuard, where "only devices on your private network can communicate with each other." It works "across firewalls and Network Address Translation (NAT) without requiring port forwarding."

No router settings. No public IP. No opening ports to the world.

## Why this matters if you build with agents

"A 24/7 computer plus Tailscale plus these frontier coding agents basically just makes the sky the limit and you can just create your own little version of the internet with all these custom apps, all these custom interfaces."

Your agent can build you a dashboard in ten minutes. But if it's only on `localhost`, you can only open it on that one computer, and putting it on the public internet means hosting, a domain, logins and your private stuff online. With a tailnet, the agent runs the app on your always-on computer and you open it from any of your devices. That's how I've "rebuilt pretty much every single paid software that I use in my personal life and in my business."

What actually runs on my tailnet right now:

- **My agent dashboard.** The main page on my main computer's tailnet address. I check on my agents from my phone.
- **A video review page.** My agents put each cut of my videos on it. I open the link on my phone, watch, talk through my notes and draw on frames. The upload gets transcribed and my editing agent gets a message with my notes.
- **A few more internal tools**, each on its own HTTPS port of the same machine.
- **Cloud boxes my agents rent.** They join the tailnet when they boot, my agents reach them over it, and they get deleted when the job is done.

Every one of those says "tailnet only" when I run `tailscale serve status`. None of them are on the public internet.

## Setup in 5 steps

1. **Install Tailscale on your 24/7 computer and sign in.** Mac and Windows: the app from [tailscale.com/download](https://tailscale.com/download). Linux:
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up
   ```
   On a Mac, turn on the `tailscale` command in the app's Settings under CLI integration (needs macOS Ventura 13 or later). Otherwise the CLI is at `/Applications/Tailscale.app/Contents/MacOS/Tailscale`.
2. **Install it on your phone, iPad and laptop** with the same account. That's your tailnet.
3. **Check MagicDNS is on.** It gives every machine a name instead of an IP, so you (and your agent) can type `my-box` instead of a number. It's on by default for tailnets created since October 20, 2022. It's in the DNS page of the admin console.
4. **Rename your machines, then turn on HTTPS certificates** in the same DNS page. Serve needs this, and `tailscale serve` will walk you through enabling it the first time. Rename first, because machine names get published (more on that in the security section).
5. **Hand the rest to your agent** with the prompts below.

**What it costs (checked Nov 25, 2026):** the Personal plan is $0, up to 6 users, unlimited user devices, 50 tagged resources to start. Funnel, Taildrop, sharing, Tailscale SSH and MagicDNS each say "available for all plans" in the docs. One catch: Tailscale says Personal is "only suitable for non-commercial use." If you run a business on it, look at Standard at $8 per user per month.

## Tailscale Serve: host an app for your own devices

**What it is.** Serve takes an app running on your computer and makes it reachable by your other devices at an HTTPS address on your tailnet. Tailscale handles the certificate. The URL is your machine name plus your tailnet's domain, like `https://my-box.<your-tailnet-domain>`.

**The commands.**

```bash
# app on port 3000, served in the foreground (Ctrl+C stops it)
tailscale serve 3000

# same, but in the background, and it comes back after a reboot
tailscale serve --bg 3000

# a second app on its own HTTPS port
tailscale serve --bg --https=8443 3001

# or a second app on a path of the main address
tailscale serve --bg --set-path=/review 3002

# see what's being served, and whether it's tailnet only
tailscale serve status

# turn one off (repeat the flags you used), or clear everything
tailscale serve --https=8443 off
tailscale serve reset
```

Without `--bg`, you have to start Serve again by hand after a reboot. With it, Serve "automatically resumes sharing."

**How I use it.** One app per port. The dashboard sits on the main address, every other tool gets its own HTTPS port. The apps themselves run under pm2 so they also come back after a reboot. When an agent finishes an app, the last line of its job is "here's the link," and I open it on my phone.

**A nice extra:** when a request comes in through Serve, Tailscale adds headers saying who it is (`Tailscale-User-Login`, `Tailscale-User-Name`). So your agent's app can know it's you without building a login. Tailscale's advice: have the app listen only on localhost, so nobody can call it directly and fake those headers. These headers aren't added for tagged devices or for Funnel traffic.

## Taildrop: send files between your devices

**What it is.** AirDrop, but for every device you own, anywhere. Files go over encrypted peer-to-peer connections, "without third-party servers in the middle."

**Turn it on first.** Taildrop is in alpha, so you opt in: admin console, General settings, turn on **Send Files**. On a Mac, also enable sharing for Tailscale in System Settings > General > Login Items & Extensions > Sharing.

**The commands.** On phones and Macs you use the normal Share menu. From a terminal:

```bash
tailscale file cp clip.mov my-box:       # send
tailscale file cp --targets              # list where you can send
tailscale file get ~/inbox               # receive (Linux / CLI)
```

On macOS, received files land in `~/Downloads`.

**How I use it.** For one-off files between my phone and my main computer: a screen recording for an agent to work with, a finished cut back to my phone. Two limits to know: it only works between your own personal devices, and it doesn't work with tagged machines, so your agents' tagged cloud boxes can't receive Taildrop files.

## Node sharing: let someone in, but only to one machine

**What it is.** "Node sharing, which allows you to share one of your machines with someone not on your tailnet." They get that one machine and nothing else.

**How to do it.** Admin console, Machines page, find the machine, open its menu, **Share**. Send an invite by email, or copy an invite link (single-use, or reusable up to 1,000 times). Unused links expire after 30 days. The other person needs their own Tailscale account to accept.

What the docs promise:

- The shared machine is **quarantined** by default. It can answer their connections but can't start connections into their tailnet.
- They reach it by its full name, `my-box.<your-tailnet-domain>`, not the short name.
- Your access rules still apply, so you can limit them to the ports of your app.
- You can revoke the share from the Machines page any time.

**How I'd use it.** This is the "serve to yourself or your family and friends" part. Your agent builds the family photo inbox or the shared calendar, you put it behind Serve, then share that one computer with your partner. Because it's Serve, the app even sees who they are through the identity headers.

## Tailscale SSH: no SSH keys to manage

**What it is.** "Tailscale SSH, using only your Tailscale identity, no SSH keys necessary." Tailscale takes over port 22 for traffic coming from your tailnet and decides who gets in based on your tailnet's rules. Your normal `sshd_config` and `authorized_keys` aren't touched, so non-Tailscale SSH still works.

**The commands.**

```bash
# on the machine you want to get into (once)
sudo tailscale set --ssh

# from any of your devices
ssh my-box
ssh ubuntu@my-box
```

The server side runs on Linux, and on macOS only with the open source `tailscaled` variant, so the regular Mac app can't be a Tailscale SSH server. You can connect from anything. Heads up: turning it on makes any SSH session you already have to that machine's Tailscale address hang.

**How I use it.** Honestly, on the throwaway boxes my agents rent, I keep Tailscale SSH off and use normal keys, but only over the tailnet: the box firewall doesn't accept SSH from the public internet. Tailscale published several Tailscale SSH security bulletins this year, the latest (Oct 26, 2026) asking SSH users to be on version 1.104.4 or newer. If you use it, keep Tailscale updated and use check mode (below).

## The agent-hosted app pattern

This is the whole trick, written as rules. Paste it into your agent's CLAUDE.md (or your rules file) once, and every app it builds ends with a link you can open on your phone:

```text
When you build me an app to use on my devices:
- Run it on this computer, listening on localhost only, under pm2 (or the
  process manager already here) so it restarts after a reboot.
- Pick a free port. Put it behind Tailscale Serve in the background:
  tailscale serve --bg --https=<free https port> <app port>
- Never use tailscale funnel unless I explicitly ask for a public page.
- If the app needs to know who I am, read the Tailscale-User-Login header
  from Serve instead of building a login.
- Run tailscale serve status, confirm the line says tailnet only, then send
  me the https link and a one-line note on what the app does.
- Never paste my tailnet name, IPs or auth keys into code, logs or chat.
```

## 5 starter projects (copy-paste prompts)

**1. Agent dashboard.**

```text
Build me a small web dashboard for my agents. Show each agent, what it is
working on, its last 20 log lines and when it last ran. Read the data from
<where your agent logs live>. Keep it one page, mobile first, dark mode.
Follow my Tailscale app rules: localhost only, pm2, tailscale serve --bg on
its own port, then send me the link.
```

**2. Phone review page for anything your agents make.**

```text
Build me a review page I can use on my phone. You register a file (video,
image or PDF) and get a link. On the page I can view it, record a voice note,
and leave timestamped comments. Save my notes to <folder>, transcribe voice
notes, and message me (or the agent that made the file) when a review comes
in. Serve it on my tailnet with tailscale serve --bg and send me the link.
```

**3. Replace one paid app.**

```text
I pay for <app> and only use <the 3 features I use>. Build me my own version
with just those features, data stored in SQLite on this computer, a clean
mobile layout and a daily backup to <folder>. Serve it on my tailnet only,
never funnel. Send me the link and a list of what you did not copy.
```

**4. Family file and photo inbox, shared with one person.**

```text
Build a simple upload page: drag and drop or pick photos and files, they land
in <folder> sorted by date and uploader. Use the Tailscale-User-Login header
from Serve to record who uploaded. Serve it with tailscale serve --bg on its
own port. Then give me the exact steps to share this machine with
<person> from the admin console, and an access rule that limits shared users
to that one port.
```

**5. A cloud box that joins your tailnet and deletes itself.**

```text
Rent a small Linux box at <provider> for <job>. Join it to my tailnet at boot
with a one-off auth key that carries a tag (I will create the key, do not ask
me to paste it in chat). Block SSH from the public internet so it is only
reachable over the tailnet. Run the job, copy the results back, then delete
the box, remove it from my Tailscale machines page, and tell me the cost.
```

For number 5, auth keys can be one-off or reusable, expire after 1 to 90 days, and a key with tags makes the device a tagged device. Tailscale warns reusable keys "can be very dangerous if stolen," so use one-off keys for boxes.

## Security: what to get right

**Serve is private. Funnel is public.** `tailscale funnel` routes "traffic from the broader internet" to your app, "for anyone to access, even if they don't use Tailscale." It only listens on ports 443, 8443 and 10000, has bandwidth limits you can't change, and doesn't add identity headers, so your app can't tell who's calling. A port is whatever the last command made it: "If the most recent command to configure the port was funnel, then the port will be completely public." Run `tailscale serve status` and `tailscale funnel status` and read every line.

**Write access rules once you share or add boxes.** A new tailnet lets every device reach every other device. That's fine with only your own devices. When you add shared users or agent boxes, write rules in the tailnet policy file (Access controls page). Tailscale recommends grants for new policies. Rules are deny-by-default once you write them, so keep a rule for your own devices. To limit shared users to your app's port, the docs give this pattern:

```json
{
  "grants": [
    {
      "src": ["autogroup:shared"],
      "dst": ["*"],
      "ip": ["443"]
    }
  ]
}
```

It only narrows access on machines they were invited to. Be careful with `"src": ["*"]`, which also covers invited users.

**Use SSH check mode.** A check rule makes you sign in again before an SSH session, then lets you in for 12 hours by default. The default tailnet policy already uses check mode for your own devices:

```json
"ssh": [
  {
    "action": "check",
    "src": ["autogroup:member"],
    "dst": ["autogroup:self"],
    "users": ["autogroup:nonroot", "root"]
  }
]
```

Check mode can't be used on rules where a tagged device is the source, and `"checkPeriod": "always"` can break tools that open lots of SSH sessions. The pricing page lists custom check periods under "Advanced Tailscale SSH," so check your plan.

**Your machine names get published.** When you enable HTTPS, certificates go into the public Certificate Transparency log, and that "includes the fully qualified domain name of your devices." Don't use your real name, your company or a client in a machine name.

**Tag your agent boxes.** Servers should join "using a tag as the identity of the server" with an auth key. A device that joins with a tagged key carries the tag's identity, not yours, and tagged devices don't get key expiry by default. On my rented video boxes, the jobs also can't dial back into the rest of my tailnet, so a bad job can't reach my main computer.

## What goes wrong

- **Funnel by accident.** An agent "makes it work on my phone" with Funnel and your dashboard is public. Ban funnel in your rules file and check `serve status`.
- **Forgot `--bg`.** The app vanishes after a reboot. Use `--bg`, and run the app itself under pm2 or similar.
- **App works on the computer, not on the phone.** Usually the app isn't running or is on another port. Check it first with `curl localhost:<port>`, then `tailscale serve status`.
- **Two apps fighting over one address.** Give each app its own HTTPS port or its own `--set-path`. Serve and Funnel can't share a port at the same time.
- **Taildrop won't send.** You didn't turn on Send Files, you're sending to someone else's device, or the target is tagged.
- **The shared person can't open the link.** They need a Tailscale account, they must accept the invite, and they need the full name ending in your tailnet's domain, not the short name.
- **Turned on Tailscale SSH and lost the session.** Existing SSH sessions to that machine's Tailscale address hang. Have another way in first.
- **Old client.** Several 2026 security fixes for Serve and SSH need 1.104.4 or newer. Keep every machine updated.

## Sources

| Claim | Source |
|---|---|
| Tailnet is a peer-to-peer mesh on WireGuard; only your devices can talk; works across firewalls and NAT without port forwarding | [What is Tailscale?](https://tailscale.com/docs/concepts/what-is-tailscale) |
| Create a tailnet, add devices, servers join with a tag and auth key, MagicDNS on by default | [Quickstart](https://tailscale.com/docs/how-to/quickstart) |
| Linux install with `install.sh` and `sudo tailscale up` | [Install on Linux](https://tailscale.com/docs/install/linux) |
| macOS CLI integration (Ventura 13+), CLI path; `tailscale file cp` / `file get` | [Tailscale CLI](https://tailscale.com/docs/reference/tailscale-cli) |
| MagicDNS names, on by default since Oct 20, 2022, edit machine names | [MagicDNS](https://tailscale.com/docs/features/magicdns) |
| Serve needs HTTPS, `tailscale serve 3000`, identity headers, localhost advice, no headers for tagged devices or Funnel, same port can't be Serve and Funnel | [Tailscale Serve](https://tailscale.com/docs/features/tailscale-serve) |
| `--bg`, `--https`, `--set-path`, `status`, `reset`, `off`, resume after reboot only with `--bg` | [tailscale serve command](https://tailscale.com/docs/reference/tailscale-cli/serve) |
| Funnel is public, ports 443/8443/10000, bandwidth limits, needs a funnel node attribute, relay hides your IP | [Tailscale Funnel](https://tailscale.com/docs/features/tailscale-funnel), [tailscale funnel command](https://tailscale.com/docs/reference/tailscale-cli/funnel) |
| Taildrop alpha, Send Files opt-in, own devices only, not tagged nodes, macOS setup, files to Downloads | [Taildrop](https://tailscale.com/docs/features/taildrop) |
| Node sharing: Machines page, email or link invites, reusable up to 1,000, 30-day expiry, quarantine, full domain name, `autogroup:shared` grant, revoke | [Sharing](https://tailscale.com/docs/features/sharing) |
| Tailscale SSH: `tailscale set --ssh`, `ssh my-box`, Linux and open source macOS only, existing sessions hang, check mode 12h default, default policy, tagged source can't use check | [Tailscale SSH](https://tailscale.com/docs/features/tailscale-ssh) |
| Grants recommended for new policies, deny-by-default, default policy allows all devices | [Grants](https://tailscale.com/docs/features/access-control/grants), [ACLs](https://tailscale.com/docs/features/access-control/acls) |
| HTTPS certificates publish machine names in the CT log | [Enabling HTTPS](https://tailscale.com/docs/how-to/set-up-https-certificates) |
| One-off and reusable auth keys, 1 to 90 day expiry, tags, reusable keys dangerous if stolen, no key expiry for tagged devices by default | [Auth keys](https://tailscale.com/docs/features/access-control/auth-keys) |
| Personal $0, 6 users, unlimited user devices, 50 tagged resources, non-commercial; Standard $8 per user per month; Advanced Tailscale SSH lists custom check periods | [Pricing](https://tailscale.com/pricing) |
| Oct 26, 2026 bulletins: Serve and Tailscale SSH fixes in 1.104.4 or newer | [Security bulletins](https://tailscale.com/security-bulletins) |

Docs checked on Nov 25, 2026. Tailscale ships fast and several of these features are alpha or beta, so check the links before you rely on a detail.

## Want more like this?

More agent breakdowns and the full lessons are inside my Skool community, **Agent Architects**: https://www.skool.com/agent-architects
