#!/usr/bin/env bash
# Security watchdog, one scheduled run (macOS / Linux). Cheapest layer first:
#   1. poll.py (no model)                       exit 0 nothing new, 2 sources failed, 10 new items
#   2. judge_command (weak model)           only on exit 10, reads prompts/judge.md, writes relevant.json
#   3. triage_command (frontier model)      only when the judge found something relevant, reads prompts/triage.md
# usage: run.sh [--inject-test] [--baseline]       (extra args go to poll.py)
# env:   SECURITY_WATCHDOG_DIR (default ~/.security-watchdog), WATCHDOG_PYTHON (default python3)
# Commands come from $WD/config.json ("judge_command", "triage_command": JSON lists of arguments).
set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
WD="${SECURITY_WATCHDOG_DIR:-$HOME/.security-watchdog}"
PY="${WATCHDOG_PYTHON:-python3}"
POLL="$SKILL_DIR/scripts/poll.py"
LOG="$WD/run.log"
# schedulers start with a bare PATH; add the usual places CLIs are installed
export PATH="$HOME/.local/bin:$HOME/bin:$HOME/.npm-global/bin:$HOME/.bun/bin:$HOME/.cargo/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

[ -d "$WD" ] || { echo "watchdog folder $WD does not exist; run the setup in SKILL.md first" >&2; exit 1; }
if [ -f "$LOG" ] && [ "$(wc -c <"$LOG")" -gt 1048576 ]; then mv -f "$LOG" "$LOG.1"; fi
log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$LOG"; }

# one run at a time; a lock older than 3 hours is from a crashed run
LOCK="$WD/.lock"
if ! mkdir "$LOCK" 2>/dev/null; then
  if [ -n "$(find "$LOCK" -maxdepth 0 -mmin +180 2>/dev/null)" ]; then
    rm -rf "$LOCK"; mkdir "$LOCK" || exit 1; log "removed stale lock"
  else
    log "another run is in progress; skipping"; exit 0
  fi
fi
trap 'rm -rf "$LOCK"' EXIT INT TERM

# run_model judge|triage: build the command from config.json and run it in $WD with a timeout
run_model() {
  local step="$1" t argv=() a pid killer rc
  t="$("$PY" "$POLL" "$WD" --get "${step}_timeout_minutes")"; t="${t:-30}"
  while IFS= read -r -d '' a; do argv+=("$a"); done < <("$PY" "$POLL" "$WD" --print-cmd "$step")
  if [ "${#argv[@]}" -eq 0 ]; then log "$step: no ${step}_command in config.json"; return 1; fi
  log "$step: starting ${argv[0]} (timeout ${t} min)"
  set -m   # own process group, so a timeout stops the CLI and everything it started
  ( cd "$WD" && exec "${argv[@]}" </dev/null >>"$LOG" 2>&1 ) & pid=$!
  set +m
  ( sleep $((t * 60)); kill -TERM -- "-$pid" 2>/dev/null || kill "$pid" 2>/dev/null ) 2>/dev/null & killer=$!
  wait "$pid"; rc=$?
  pkill -P "$killer" 2>/dev/null; kill "$killer" 2>/dev/null; wait "$killer" 2>/dev/null
  log "$step: exit $rc"
  return "$rc"
}

notify_failure() {   # optional plain-text alert for failures the models cannot report themselves
  local msg="$1" argv=() a
  while IFS= read -r -d '' a; do argv+=("$a"); done < <("$PY" -c 'import json,sys
c=json.load(open(sys.argv[1],encoding="utf-8")).get("notify_command") or []
sys.stdout.write("".join(str(x)+"\0" for x in c))' "$WD/config.json" 2>/dev/null)
  if [ "${#argv[@]}" -gt 0 ]; then printf '%s\n' "$msg" | "${argv[@]}" >>"$LOG" 2>&1; fi
}

triage() {
  run_model triage
  "$PY" "$POLL" "$WD" --after-triage >>"$LOG" 2>&1
  if [ $? -eq 4 ]; then
    log "triage gave up after 3 attempts"
    notify_failure "Security watchdog: the triage step failed 3 times. Relevant items are waiting in $WD/relevant.json."
  fi
}

# 0. a relevant finding from an earlier run that triage did not finish
"$PY" "$POLL" "$WD" --pending-triage
if [ $? -eq 11 ]; then log "retrying unfinished triage"; triage; fi

# 1. poll (no model)
"$PY" "$POLL" "$WD" "$@" 2>&1 | tee -a "$LOG"
rc=${PIPESTATUS[0]}
case "$rc" in
  0) exit 0 ;;
  2) log "nothing new; some sources could not be checked (see state.json / --status)"; exit 0 ;;
  10) ;;
  *) log "poll.py failed with exit $rc"; notify_failure "Security watchdog: poll.py failed (exit $rc). See $LOG."; exit "$rc" ;;
esac

# 2. weak model judges relevance
run_model judge
"$PY" "$POLL" "$WD" --after-judge 2>&1 | tee -a "$LOG"
case "${PIPESTATUS[0]}" in
  11) triage ;;                       # 3. frontier model, only on a relevant item
  0) ;;
  *) log "judge output missing or invalid; items stay pending for the next run" ;;
esac
exit 0
