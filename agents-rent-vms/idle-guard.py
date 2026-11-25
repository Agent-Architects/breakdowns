#!/usr/bin/env python3
"""Cost guard for agent boxes: report every rented box with its age and cost so far, and delete the ones
that are idle. A backstop for the rule "delete the box the second the work is saved", for when an agent forgets.

  idle-guard.py            report only (default, changes nothing)
  idle-guard.py --apply    also delete idle boxes

Only touches Hetzner servers labelled managed-by=agent (hcloud.py sets it). A box counts as BUSY when:
  - it has a keep lock: a file named after the box in $AGENT_BOX_DIR/keep/ (a manual hold), or
  - a job is running on it: the file ~worker/jobs/BUSY exists (your job script touches it at start and
    removes it at the end), checked over SSH as worker. A box we cannot reach counts as busy until it
    is UNREACHABLE_H hours old, so a box still booting is never deleted.
Idle = not busy and older than IDLE_MIN minutes since it was created or last seen busy.
Run it every 15 minutes from cron or launchd. Keys as in hcloud.py.
"""
import datetime, json, os, subprocess, sys, urllib.request

API = "https://api.hetzner.cloud/v1"
D = os.path.expanduser(os.environ.get("AGENT_BOX_DIR", "~/.config/agent-boxes"))
SSH_KEY = os.path.expanduser(os.environ.get("AGENT_BOX_SSH_KEY", "~/.ssh/agent_box_ed25519"))
IDLE_MIN, UNREACHABLE_H = 30, 2
STATE = os.path.join(D, "idle-guard-state.json")


def api(method, path):
    tok = open(os.path.join(D, "hcloud_token")).read().strip()
    req = urllib.request.Request(API + path, method=method, headers={"Authorization": "Bearer " + tok})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read() or b"{}")


def busy_on_box(name):
    """True = job running, False = no job, None = could not check. Reaches the box by its Tailscale name."""
    try:
        r = subprocess.run(["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", f"worker@{name}",
                            "test -e ~/jobs/BUSY && echo BUSY || echo FREE"], capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return None
    out = r.stdout.strip()
    return True if out == "BUSY" else False if out == "FREE" else None


def hourly(s):
    loc = (s.get("location") or (s.get("datacenter") or {}).get("location") or {}).get("name")
    for p in s["server_type"].get("prices", []):
        if p.get("location") == loc:
            return float(p["price_hourly"]["gross"])
    return 0.0


def main():
    apply = "--apply" in sys.argv
    now = datetime.datetime.now(datetime.timezone.utc)
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    seen = {}
    boxes = [s for s in api("GET", "/servers?per_page=50")["servers"] if s.get("labels", {}).get("managed-by") == "agent"]
    for s in boxes:
        name = s["name"]
        created = datetime.datetime.fromisoformat(s["created"].replace("Z", "+00:00"))
        age_h = (now - created).total_seconds() / 3600
        cost = hourly(s) * (int(age_h) + 1)   # Hetzner bills every started hour
        job = busy_on_box(name)
        why = []
        if os.path.exists(os.path.join(D, "keep", name)):
            why.append("keep lock")
        if job:
            why.append("job running")
        if job is None and age_h < UNREACHABLE_H:
            why.append("unreachable, young")
        last = now.isoformat() if why else state.get(name, s["created"])
        seen[name] = last
        idle_min = (now - datetime.datetime.fromisoformat(last.replace("Z", "+00:00"))).total_seconds() / 60
        verdict = "keep" if why or idle_min < IDLE_MIN else "DELETE"
        print(f"{name} {s['server_type']['name']} age={age_h:.1f}h cost_so_far={cost:.2f} idle={idle_min:.0f}m -> "
              f"{verdict}{' (' + ', '.join(why) + ')' if why else ''}")
        if verdict == "DELETE" and apply:
            api("DELETE", f"/servers/{s['id']}")
            print(f"{name} deleted")
            seen.pop(name, None)
    if not boxes:
        print("no agent boxes, nothing is billing")
    os.makedirs(D, exist_ok=True)
    json.dump(seen, open(STATE, "w"), indent=1)


if __name__ == "__main__":
    main()
