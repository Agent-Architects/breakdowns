#!/bin/bash
# First setup of a rented Ubuntu 24.04 box for agent jobs. Run as root, from your own computer:
#   ssh root@<box> "WORKER_PUBKEY='$(cat ~/.ssh/agent_box_ed25519.pub)' bash -s" < bootstrap.sh
#
# What it does (safe to re-run, finished steps are skipped):
#   1. apt basics (add your own tools in EXTRA_PACKAGES or at the marked spot)
#   2. a non-root `worker` user with ~/jobs; jobs run as this user, never as root
#   3. key-only SSH (no passwords)
#   4. an egress guard: jobs can reach the internet, but not your tailnet (your laptop, phone, other
#      servers) and not the cloud metadata service, which holds the box's cloud-init user-data
#      (and with it the Tailscale auth key)
# Ends with one BOOTSTRAP_RESULT line.
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "run as root"; exit 2; }
: "${WORKER_PUBKEY:?set WORKER_PUBKEY to the public key your agent uses to log in as worker}"
U=worker
log() { echo "[bootstrap] $(date -u +%FT%TZ) $*"; }

log "apt packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq --no-install-recommends python3 git curl xz-utils ca-certificates nftables time ${EXTRA_PACKAGES:-} > /dev/null

# >>> your tools go here (ffmpeg, a test runner, Node, a model file, ...). Pin versions so every box is the same.

log "user $U"
id $U > /dev/null 2>&1 || useradd -m -s /bin/bash $U
H=$(getent passwd $U | cut -d: -f6)
install -d -m 700 -o $U -g $U "$H/.ssh" "$H/jobs"
touch "$H/.ssh/authorized_keys"
grep -qxF "$WORKER_PUBKEY" "$H/.ssh/authorized_keys" || echo "$WORKER_PUBKEY" >> "$H/.ssh/authorized_keys"
chown $U:$U "$H/.ssh/authorized_keys"; chmod 600 "$H/.ssh/authorized_keys"

log "key-only sshd"
printf 'PasswordAuthentication no\nKbdInteractiveAuthentication no\n' > /etc/ssh/sshd_config.d/10-agent-box.conf
systemctl reload ssh

log "egress guard"
# 100.100.100.100 is Tailscale's DNS resolver, 100.64.0.0/10 and fd7a:115c:a1e0::/48 are the address ranges
# Tailscale gives devices, 169.254.169.254 is the cloud metadata service. Root (tailscaled itself) keeps
# metadata access; everyone else is blocked. Inbound SSH from you is established traffic and still works.
cat > /etc/agent-egress-guard.nft <<'EOF'
table inet agentguard
delete table inet agentguard
table inet agentguard {
  chain out {
    type filter hook output priority 0; policy accept;
    oifname "lo" accept
    ct state established,related accept
    ip daddr 100.100.100.100 accept
    ip daddr 169.254.169.254 meta skuid != 0 drop
    ip daddr 100.64.0.0/10 drop
    ip6 daddr fd7a:115c:a1e0::/48 drop
  }
}
EOF
cat > /etc/systemd/system/agent-egress-guard.service <<'EOF'
[Unit]
Description=agent box egress guard (no tailnet or metadata access for jobs)
After=network-pre.target
Before=tailscaled.service
[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/sbin/nft -f /etc/agent-egress-guard.nft
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable agent-egress-guard.service > /dev/null 2>&1
systemctl restart agent-egress-guard.service

echo "BOOTSTRAP_RESULT host=$(hostname) cpus=$(nproc) mem=$(free -g | awk '/^Mem:/{print $2}')G" \
  "free_disk=$(df -BG --output=avail "$H" | tail -1 | tr -dc 0-9)G python=$(python3 --version | cut -d' ' -f2)" \
  "tailscale=$(command -v tailscale > /dev/null && echo up || echo missing)"
