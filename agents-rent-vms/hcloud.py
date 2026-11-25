#!/usr/bin/env python3
"""Rent, list and delete Hetzner Cloud boxes for your agents. Python standard library only.

  hcloud.py list
  hcloud.py create <name>:<type> [<name>:<type> ...] [--location nbg1]   e.g. render-1:ccx33 test-1:cpx52
  hcloud.py delete <name> [<name> ...]
  hcloud.py firewall        attach a no-inbound firewall to every box (reach them over Tailscale only)

Keys are read from files, never from chat or the command line, and never printed:
  $AGENT_BOX_DIR/hcloud_token   Hetzner Cloud API token (read + write)
  $AGENT_BOX_DIR/ts_authkey     Tailscale auth key (one-off or ephemeral, tagged)
AGENT_BOX_DIR defaults to ~/.config/agent-boxes. SSH key: $AGENT_BOX_SSH_KEY (default ~/.ssh/agent_box_ed25519).
Every box gets the label managed-by=agent so idle-guard.py only ever touches boxes made here.
"""
import json, os, sys, urllib.error, urllib.request

API = "https://api.hetzner.cloud/v1"
D = os.path.expanduser(os.environ.get("AGENT_BOX_DIR", "~/.config/agent-boxes"))
SSH_KEY = os.path.expanduser(os.environ.get("AGENT_BOX_SSH_KEY", "~/.ssh/agent_box_ed25519"))
KEY_NAME = "agent-box"
FW_NAME = "agent-boxes-no-inbound"
LABEL = {"managed-by": "agent"}


def secret(name):
    with open(os.path.join(D, name)) as f:
        return f.read().strip()


def api(method, path, body=None):
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": "Bearer " + secret("hcloud_token"),
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        sys.exit(f"{method} {path}: HTTP {e.code} {e.read().decode()[:300]}")


def servers():
    return api("GET", "/servers?per_page=50")["servers"]


def show(s):
    loc = (s.get("location") or (s.get("datacenter") or {}).get("location") or {}).get("name")
    print(f'{s["name"]} id={s["id"]} type={s["server_type"]["name"]} status={s["status"]} '
          f'location={loc} created={s["created"]}')


if len(sys.argv) < 2:
    sys.exit(__doc__)
cmd, args = sys.argv[1], sys.argv[2:]
if cmd == "list":
    for s in servers():
        show(s)
elif cmd == "create":
    loc = "nbg1"
    if "--location" in args:
        i = args.index("--location"); loc = args[i + 1]; del args[i:i + 2]
    if not any(k["name"] == KEY_NAME for k in api("GET", "/ssh_keys")["ssh_keys"]):
        api("POST", "/ssh_keys", {"name": KEY_NAME, "public_key": open(SSH_KEY + ".pub").read().strip()})
    existing = {s["name"] for s in servers()}
    for spec in args:
        name, stype = spec.split(":")
        if name in existing:
            print(f"{name} exists, skipped"); continue
        # cloud-init joins the box to your tailnet on first boot, so you never need its public IP.
        user_data = ("#cloud-config\nruncmd:\n  - curl -fsSL https://tailscale.com/install.sh | sh\n"
                     f"  - tailscale up --authkey={secret('ts_authkey')} --hostname={name}\n")
        r = api("POST", "/servers", {"name": name, "server_type": stype, "image": "ubuntu-24.04", "location": loc,
                                     "ssh_keys": [KEY_NAME], "user_data": user_data, "labels": LABEL,
                                     "start_after_create": True})
        show(r["server"])
elif cmd == "firewall":
    # A firewall with no rules drops all inbound traffic on the public IP. SSH goes over Tailscale instead.
    fw = next((f for f in api("GET", "/firewalls")["firewalls"] if f["name"] == FW_NAME), None)
    if not fw:
        fw = api("POST", "/firewalls", {"name": FW_NAME, "rules": []})["firewall"]
    on = {r["server"]["id"] for r in fw.get("applied_to", []) if r.get("type") == "server"}
    todo = [{"type": "server", "server": {"id": s["id"]}} for s in servers()
            if s["id"] not in on and s.get("labels", {}).get("managed-by") == "agent"]
    if todo:
        api("POST", f'/firewalls/{fw["id"]}/actions/apply_to_resources', {"apply_to": todo})
    print(f"{FW_NAME}: applied to {len(on) + len(todo)} servers")
elif cmd == "delete":
    by_name = {s["name"]: s for s in servers()}
    for name in args:
        if name not in by_name:
            print(f"{name} not found"); continue
        api("DELETE", f'/servers/{by_name[name]["id"]}')
        print(f"{name} deleted")
else:
    sys.exit(__doc__)
