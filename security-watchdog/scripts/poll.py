#!/usr/bin/env python3
"""Security watchdog: the free layer. No model is involved here.

usage:
  poll.py <WD>                    fetch every source in WD/sources.json, write only NEW items to WD/new_items.json
  poll.py <WD> --baseline         record what already exists, report nothing (first run, or after a long break)
  poll.py <WD> --inject-test      also add one synthetic TEST item (for the "verify it works" step)
  poll.py <WD> --only <name>      poll just one source (debugging a new source)
  poll.py <WD> --after-judge      check WD/relevant.json against new_items.json; archive new_items.json when valid
  poll.py <WD> --pending-triage   is there a relevant.json that still needs the frontier model?
  poll.py <WD> --after-triage     count a triage attempt (gives up after 3)
  poll.py <WD> --print-cmd judge|triage [--json]   the configured headless command, prompt included
  poll.py <WD> --get <key>        one value from WD/config.json (empty if unset)
  poll.py <WD> --status           one-screen health report (sources, failures, last run)

exit codes for a poll: 0 = nothing new (stop, spend nothing) | 10 = new_items.json has items for the weak model
| 2 = nothing new but some sources failed ("could not look", never "nothing found") | 1 = config error.
--after-judge: 11 = relevant items or blind spots need triage, 0 = nothing relevant, 3 = judge output missing/invalid.
--pending-triage: 11 = triage still needed, 0 = no.
Stdlib only, Python 3.9+. WD defaults to ~/.security-watchdog if the argument is "-".
"""
import concurrent.futures as cf
import csv
import datetime as dt
import email.utils
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

VERSION = "1.1"
UA = "security-watchdog/" + VERSION
MAX_BYTES = 25 * 1024 * 1024          # refuse anything bigger: a feed is never this large
LOOKBACK_H = {"ghsa": 6, "osv": 6, "kev": 72, "feed": 0}   # re-check this far back; ids already seen are skipped
SEEN_CAP = {"osv": 20000}             # ids remembered per source (newest kept)
SEEN_CAP_DEFAULT = 3000
FAIL_ALERT = 6                        # consecutive failed runs (3 h at 30 min) before the user is told
PENDING_CAP = 1000                    # unjudged items carried between runs
TRIAGE_MAX_ATTEMPTS = 3
GHSA_ECO = {"npm": "npm", "pip": "PyPI", "go": "Go", "rust": "crates.io", "actions": "GitHub Actions",
            "rubygems": "RubyGems", "composer": "Packagist", "maven": "Maven", "nuget": "NuGet"}
COMMON = {"next", "react", "requests", "express", "core", "utils", "util", "test", "node", "app", "ssh", "api",
          "client", "server", "cli", "http", "https", "json", "debug", "chalk", "commander", "types", "config",
          "common", "shared", "security", "update", "auth", "data", "cloud", "github", "linux", "windows", "python"}


def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def norm(ts):
    """Any ISO-ish timestamp -> 'YYYY-MM-DDTHH:MM:SS' so plain string comparison is safe."""
    return (ts or "").strip().replace(" ", "T")[:19]


def shift(ts, hours):
    t = dt.datetime.strptime(norm(ts), "%Y-%m-%dT%H:%M:%S")
    return (t - dt.timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S")


def wd_path(wd, *parts):
    return os.path.join(wd, *parts)


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, obj, indent=1):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=indent, ensure_ascii=False)
    os.replace(tmp, path)   # atomic: a crash never leaves half a state file


# ---------------------------------------------------------------- fetching
class RateLimited(Exception):
    pass


def get(url, timeout=30, headers=None, tries=2):
    """GET with one retry on network errors and 5xx. Returns (body bytes or None on 304, headers)."""
    h = {"User-Agent": UA}
    h.update(headers or {})
    host = urllib.parse.urlparse(url).hostname or ""
    if host == "api.github.com":
        h.setdefault("Accept", "application/vnd.github+json")
        tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if tok:   # only ever sent to api.github.com
            h["Authorization"] = "Bearer " + tok
    last = None
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
                body = r.read(MAX_BYTES + 1)
                if len(body) > MAX_BYTES and r.status != 206:
                    raise ValueError(f"response larger than {MAX_BYTES // 1048576} MB")
                return body, r.headers
        except urllib.error.HTTPError as e:
            if e.code == 304:
                return None, e.headers
            if host == "api.github.com" and e.code in (403, 429) and (
                    e.headers.get("X-RateLimit-Remaining") == "0" or e.headers.get("Retry-After")):
                reset = e.headers.get("X-RateLimit-Reset")
                when = time.strftime("%H:%M UTC", time.gmtime(int(reset))) if reset and reset.isdigit() else "later"
                raise RateLimited(f"GitHub API rate limit hit (resets {when}); set GITHUB_TOKEN for 5000 req/h")
            if e.code < 500 or attempt == tries - 1:
                raise
            last = e
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            if attempt == tries - 1:
                raise
            last = e
        time.sleep(3)
    raise last


def loads(body):
    return json.loads(body.decode("utf-8", "replace"), strict=False)


def next_link(link_header):
    for part in (link_header or "").split(","):
        m = re.search(r'<([^>]+)>\s*;\s*rel="next"', part)
        if m:
            return m.group(1)
    return None


# ---------------------------------------------------------------- matching hints (the weak model decides; these are hints)
def build_terms(stack):
    def pypi(n):
        return re.sub(r"[-_.]+", "-", n.lower())
    pk = {}
    for eco, names in (stack.get("packages") or {}).items():
        pk[eco] = {pypi(n) if eco == "PyPI" else n.lower() for n in names}
    words = set()
    for s in stack.get("services") or []:
        for w in [s.get("name", "")] + list(s.get("aliases") or []):
            if len(w) >= 3:
                words.add(w.lower())
    for t in stack.get("tools") or []:
        if len(t) >= 4:
            words.add(t.lower())
    direct = set()
    for eco, names in (stack.get("direct") or {}).items():
        direct.update(n.lower().split("/")[-1] for n in names if len(n.split("/")[-1]) >= 4)
    return pk, words - COMMON, direct - COMMON


def pkg_hit(pk, eco, name):
    if not eco or not name:
        return False
    n = re.sub(r"[-_.]+", "-", name.lower()) if eco == "PyPI" else name.lower()
    return n in pk.get(eco, ())


def text_hits(text, words):
    t = (text or "").lower()
    return sorted(w for w in words if re.search(r"(?<![a-z0-9])" + re.escape(w) + r"(?![a-z0-9])", t))


# ---------------------------------------------------------------- source kinds
# each returns (items, quiet_ids). quiet_ids are remembered as seen but never shown to the model.

def kind_ghsa(src, ss, ctx):
    since = ss.get("since") or shift(ctx["now"], 24)
    floor = shift(since, LOOKBACK_H["ghsa"])
    url, items, pages = src["url"], [], 0
    while url and pages < int(src.get("max_pages", 5)):
        body, hdr = get(url)
        arr = loads(body)
        if not isinstance(arr, list):
            raise ValueError("unexpected GitHub response: " + str(arr)[:120])
        pages += 1
        stop = False
        for a in arr:
            pub = norm(a.get("published_at"))
            if pub and pub <= floor:
                stop = True
                break          # sorted newest first
            pkgs = [(GHSA_ECO.get((v.get("package") or {}).get("ecosystem", ""), (v.get("package") or {}).get("ecosystem")),
                     (v.get("package") or {}).get("name")) for v in a.get("vulnerabilities") or []]
            items.append({"id": a.get("ghsa_id"), "cve": a.get("cve_id"), "summary": a.get("summary"),
                          "url": a.get("html_url"), "severity": a.get("severity"), "type": a.get("type"),
                          "published": a.get("published_at"),
                          "packages": [f"{e}:{n}" for e, n in pkgs[:10]],
                          "hint": sorted({f"{e}:{n}" for e, n in pkgs if pkg_hit(ctx["pk"], e, n)})})
        if stop:
            break
        url = next_link(hdr.get("Link"))
    ss["since"] = ctx["now"]
    return [i for i in items if i["id"]], []


def kind_osv(src, ss, ctx):
    eco = src["ecosystem"]
    if not ctx["pk"].get(eco) and not src.get("always"):
        ss["note"] = f"skipped: no {eco} packages in stack.json"
        return [], []
    since = ss.get("since") or shift(ctx["now"], 24)
    floor = shift(since, LOOKBACK_H["osv"])
    head = int(src.get("head_bytes", 524288))      # the CSV is newest first; read only its head, never the whole file
    body, _ = get(src["url"], timeout=60, headers={"Range": f"bytes=0-{head - 1}"})
    lines = body.decode("utf-8", "replace").splitlines()
    if len(body) >= head and lines:
        lines = lines[:-1]                            # last line may be cut in half
    rows = []
    for r in csv.reader(lines):
        if len(r) >= 2 and re.match(r"\d{4}-\d\d-\d\dT", r[0]):
            rows.append((norm(r[0]), r[1].split("/")[-1].strip()))
    if not rows:
        raise ValueError("no rows parsed from OSV CSV")
    seen = ctx["seen"]
    cand = [(t, i) for t, i in rows if t > floor and i not in seen]
    ss["since"] = ctx["now"]
    ss.pop("note", None)
    if rows[-1][0] > floor and len(body) >= head:
        ss["note"] = f"head of CSV ({head // 1024} KB) did not reach back to {floor}; raise head_bytes if this repeats"
    if ctx["baseline"]:
        return [], [i for _, i in cand]
    cand.sort(key=lambda r: (not r[1].startswith("MAL-"), r[0]), reverse=False)
    cap = int(src.get("max_details", 100))
    todo, rest = cand[:cap], cand[cap:]
    if rest:
        ss["note"] = f"{len(rest)} changed ids left for the next run (cap max_details={cap})"

    def detail(tid):
        try:
            return tid, loads(get("https://api.osv.dev/v1/vulns/" + urllib.parse.quote(tid[1]), timeout=20)[0])
        except Exception:
            return tid, None
    items, quiet, failed = [], [], 0
    max_age = shift(ctx["now"], 24 * float(src.get("max_age_days", 14)))
    with cf.ThreadPoolExecutor(8) as ex:
        for (t, vid), v in ex.map(detail, todo):
            if v is None:
                failed += 1
                continue                              # not marked seen: retried next run while inside the lookback
            if norm(v.get("published")) and norm(v.get("published")) < max_age:
                quiet.append(vid)                     # an old record that was only edited: not news
                continue
            pk = [((a.get("package") or {}).get("ecosystem"), (a.get("package") or {}).get("name"))
                  for a in v.get("affected") or []]
            items.append({"id": vid, "aliases": (v.get("aliases") or [])[:5],
                          "summary": v.get("summary") or (v.get("details") or "")[:200],
                          "url": "https://osv.dev/vulnerability/" + vid, "published": v.get("published"),
                          "modified": t, "malware": vid.startswith("MAL-"),
                          "packages": [f"{e}:{n}" for e, n in pk[:10]],
                          "hint": sorted({f"{e}:{n}" for e, n in pk if pkg_hit(ctx["pk"], e, n)})})
    if todo and failed > len(todo) // 2:
        raise RuntimeError(f"OSV detail lookups failed for {failed}/{len(todo)} ids")
    return items, quiet


def kind_kev(src, ss, ctx):
    hdr_in = {}
    if ss.get("etag"):
        hdr_in["If-None-Match"] = ss["etag"]
    if ss.get("last_modified"):
        hdr_in["If-Modified-Since"] = ss["last_modified"]
    body, hdr = get(src["url"], timeout=90, headers=hdr_in)
    since = ss.get("since") or shift(ctx["now"], 24)
    ss["since"] = ctx["now"]
    if body is None:
        return [], []                                 # 304 not modified
    j = loads(body)
    if not isinstance(j.get("vulnerabilities"), list):
        raise ValueError("KEV JSON has no vulnerabilities list")
    ss["etag"], ss["last_modified"] = hdr.get("ETag"), hdr.get("Last-Modified")
    floor_day = shift(since, LOOKBACK_H["kev"])[:10]
    items = []
    for v in j["vulnerabilities"]:
        if (v.get("dateAdded") or "") < floor_day or not v.get("cveID"):
            continue
        items.append({"id": v["cveID"], "summary": v.get("vulnerabilityName"),
                      "vendor": v.get("vendorProject"), "product": v.get("product"),
                      "url": "https://nvd.nist.gov/vuln/detail/" + v["cveID"], "added": v.get("dateAdded"),
                      "action": v.get("requiredAction"), "ransomware": v.get("knownRansomwareCampaignUse"),
                      "hint": text_hits(f'{v.get("vendorProject")} {v.get("product")}', ctx["words"])})
    return items, []


def _local(tag):
    return tag.rsplit("}", 1)[-1].lower() if isinstance(tag, str) else ""


def _strip_html(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def kind_feed(src, ss, ctx):
    """RSS 2.0, RSS 1.0 (RDF) and Atom. Namespaces are ignored."""
    hdr_in = {}
    if ss.get("etag"):
        hdr_in["If-None-Match"] = ss["etag"]
    if ss.get("last_modified"):
        hdr_in["If-Modified-Since"] = ss["last_modified"]
    body, hdr = get(src["url"], headers=hdr_in)
    ss["since"] = ctx["now"]
    if body is None:
        return [], []
    try:
        root = ET.fromstring(body)
    except ET.ParseError as e:
        raise ValueError(f"not a valid RSS/Atom feed ({e}); first bytes: {body[:60]!r}")
    entries = [el for el in root.iter() if _local(el.tag) in ("item", "entry")]
    if not entries and _local(root.tag) not in ("rss", "feed", "rdf"):
        raise ValueError(f"not an RSS/Atom feed (root <{_local(root.tag)}>)")
    ss["etag"], ss["last_modified"] = hdr.get("ETag"), hdr.get("Last-Modified")
    words = ctx["words"] | (ctx["direct"] if src.get("match_packages") else set())
    items = []
    for it in entries:
        f = {}
        link = ""
        for ch in it:
            n = _local(ch.tag)
            if n == "link":
                href = ch.get("href")
                if href and (ch.get("rel") in (None, "alternate") or not link):
                    link = href
                elif (ch.text or "").strip() and not link:
                    link = ch.text.strip()
            elif n not in f:
                f[n] = "".join(ch.itertext()).strip()
        title = _strip_html(f.get("title"))
        detail = _strip_html(f.get("description") or f.get("summary") or f.get("content") or f.get("encoded"))
        key = f.get("guid") or f.get("id") or link or title
        if not key:
            continue
        when = f.get("pubdate") or f.get("published") or f.get("updated") or f.get("date") or ""
        try:
            when = email.utils.parsedate_to_datetime(when).astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            pass
        hint = text_hits(title + " " + detail, words)
        if src.get("always_report"):
            hint = hint + ["(vendor's own security channel)"]
        items.append({"id": src["name"] + ":" + key[:300], "summary": title[:300], "url": link,
                      "published": when, "detail": detail[:400], "hint": hint})
    return items, []


KINDS = {"ghsa": kind_ghsa, "osv": kind_osv, "kev": kind_kev, "feed": kind_feed}


# ---------------------------------------------------------------- helpers for the wrapper
def config(wd):
    return load_json(wd_path(wd, "config.json"), {}) or {}


def prompt_for(wd, step):
    skill = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = os.path.join(skill, "prompts", step + ".md")
    return (f"Security watchdog {step} run. Read the file {p} and follow it exactly. "
            f"Watchdog folder: {wd} . Skill folder: {skill} .")


def print_cmd(wd, step, as_json):
    cmd = config(wd).get(step + "_command")
    if not cmd:
        sys.exit(f"no {step}_command in {wd_path(wd, 'config.json')}")
    if isinstance(cmd, str):
        sys.exit(f"{step}_command must be a JSON list of arguments, e.g. [\"claude\", \"-p\", \"--model\", \"haiku\"]")
    prompt = prompt_for(wd, step)
    argv = [prompt if a == "{prompt}" else a for a in cmd]
    if "{prompt}" not in cmd:
        argv.append(prompt)
    if as_json:
        print(json.dumps(argv))
    else:
        sys.stdout.write("\0".join(argv) + "\0")


def relevant_status(wd):
    rel = load_json(wd_path(wd, "relevant.json"), None)
    if not isinstance(rel, dict):
        return None, 0
    n = sum(1 for i in rel.get("items") or [] if str(i.get("verdict", "")).upper() == "RELEVANT")
    n += len(rel.get("could_not_look") or [])
    return rel, n


def after_judge(wd):
    new = load_json(wd_path(wd, "new_items.json"), None)
    try:
        rel, n = relevant_status(wd)
    except ValueError as e:
        print("judge wrote invalid JSON in relevant.json:", e)
        sys.exit(3)
    if not new or not rel or rel.get("run") != new.get("run"):
        print("judge did not write relevant.json for run", (new or {}).get("run"), "- items stay pending")
        sys.exit(3)
    judged = {i.get("id") for i in rel.get("items") or []}
    missing = [i["id"] for i in new.get("items") or [] if i["id"] not in judged]
    if missing:
        print(f"judge skipped {len(missing)} item(s); they stay pending")
        new["items"] = [i for i in new["items"] if i["id"] in missing]
        save_json(wd_path(wd, "new_items.json"), new)
    else:
        os.replace(wd_path(wd, "new_items.json"), wd_path(wd, "last_judged.json"))
    rel["triaged"] = n == 0            # only the triage step may set this to true
    rel["triage_attempts"] = 0
    save_json(wd_path(wd, "relevant.json"), rel)
    print(f"judge ok: {len(judged)} judged, {n} need triage")
    sys.exit(11 if n else 0)


def pending_triage(wd):
    try:
        rel, n = relevant_status(wd)
    except ValueError:
        sys.exit(0)
    sys.exit(11 if rel and n and not rel.get("triaged") and not rel.get("triage_gave_up") else 0)


def after_triage(wd):
    rel, _ = relevant_status(wd)
    if not rel or rel.get("triaged"):
        print("triage done")
        sys.exit(0)
    rel["triage_attempts"] = int(rel.get("triage_attempts", 0)) + 1
    if rel["triage_attempts"] >= TRIAGE_MAX_ATTEMPTS:
        rel["triage_gave_up"] = True
        print(f"TRIAGE FAILED {rel['triage_attempts']} times for run {rel.get('run')}: a person must look at relevant.json")
        save_json(wd_path(wd, "relevant.json"), rel)
        sys.exit(4)
    save_json(wd_path(wd, "relevant.json"), rel)
    print(f"triage did not finish (attempt {rel['triage_attempts']}); retried next run")
    sys.exit(3)


def status(wd):
    st = load_json(wd_path(wd, "state.json"), {}) or {}
    print("last run:", st.get("last_run", "never"))
    for name, ss in sorted((st.get("sources") or {}).items()):
        ok = "FAILING x%d: %s" % (ss.get("fails"), ss.get("last_error")) if ss.get("fails") else "ok"
        print(f"  {name:24} last ok {ss.get('last_ok', 'never'):22} {ok} {ss.get('note', '')}")
    rel, n = relevant_status(wd)
    if rel:
        print("relevant.json run", rel.get("run"), "needs triage:", n, "triaged:", rel.get("triaged"),
              "gave up:", rel.get("triage_gave_up", False))
    new = load_json(wd_path(wd, "new_items.json"), None)
    print("pending for judge:", len((new or {}).get("items") or []))


# ---------------------------------------------------------------- the poll
def stack_brief(stack):
    """What the weak model needs to judge meaning, small enough to read every run."""
    d = {k: stack.get(k) for k in ("machine", "services", "tools", "ai", "extensions") if stack.get(k)}
    d["direct"] = {e: n[:400] for e, n in (stack.get("direct") or {}).items()}
    d["ecosystems"] = {e: len(n) for e, n in (stack.get("packages") or {}).items()}
    d["repos"] = [r.get("path") if isinstance(r, dict) else r for r in stack.get("repos") or []][:100]
    return d


def poll(wd, args):
    try:
        sources = load_json(wd_path(wd, "sources.json"), None)
        stack = load_json(wd_path(wd, "stack.json"), None)
    except ValueError as e:
        sys.exit(f"config error: {e}")
    if not isinstance(sources, list) or not sources:
        sys.exit(f"config error: {wd_path(wd, 'sources.json')} missing or empty (copy references/base-sources.json)")
    if not isinstance(stack, dict):
        sys.exit(f"config error: {wd_path(wd, 'stack.json')} missing (run scripts/scan_stack.py first)")
    bad = [s for s in sources if not isinstance(s, dict) or s.get("kind") not in KINDS or not s.get("name") or not s.get("url")]
    if bad:
        sys.exit(f"config error: sources need name, url and kind in {sorted(KINDS)}: {json.dumps(bad[:2])}")
    try:
        st = load_json(wd_path(wd, "state.json"), {}) or {}
    except ValueError:
        os.replace(wd_path(wd, "state.json"), wd_path(wd, "state.json.corrupt"))
        print("state.json was corrupt; moved to state.json.corrupt, every source re-baselines")
        st = {}
    st.setdefault("sources", {})
    baseline = "--baseline" in args
    only = args[args.index("--only") + 1] if "--only" in args and args.index("--only") + 1 < len(args) else None
    if only:
        sources = [s for s in sources if s["name"] == only]
    now = now_iso()
    pk, words, direct = build_terms(stack)

    def run_one(s):
        ss = st["sources"].setdefault(s["name"], {})
        first = "since" not in ss                    # never polled: baseline it so we do not flood the user
        seen = set(ss.get("seen") or [])
        ctx = {"now": now, "pk": pk, "words": words, "direct": direct, "seen": seen, "baseline": baseline or first}
        try:
            items, quiet = KINDS[s["kind"]](s, ss, ctx)
            new = []
            for i in items:
                if i["id"] not in seen:
                    seen.add(i["id"])
                    i["source"] = s["name"]
                    new.append(i)
            ids = [i["id"] for i in new] + [q for q in quiet if q not in ss.get("seen", [])]
            cap = SEEN_CAP.get(s["kind"], SEEN_CAP_DEFAULT)
            idset = set(ids)
            ss["seen"] = (ids + [x for x in ss.get("seen") or [] if x not in idset])[:cap]
            ss.update(fails=0, last_ok=now)
            ss.pop("last_error", None)
            return s["name"], ([] if ctx["baseline"] else new), None, first
        except Exception as e:
            ss["fails"] = int(ss.get("fails", 0)) + 1
            ss["last_error"] = f"{type(e).__name__}: {e}"[:300]
            return s["name"], [], ss["last_error"], first

    new_items, errors, baselined = [], {}, []
    with cf.ThreadPoolExecutor(max(1, min(8, len(sources)))) as ex:
        for name, items, err, first in ex.map(run_one, sources):
            new_items += items
            if err:
                errors[name] = err
            elif first and not baseline and not st["sources"][name].get("note", "").startswith("skipped"):
                baselined.append(name)
    if not only:
        names = {s["name"] for s in sources}
        st["sources"] = {k: v for k, v in st["sources"].items() if k in names}
    blind = [{"source": n, "failed_runs": ss["fails"], "error": ss.get("last_error")}
             for n, ss in st["sources"].items() if ss.get("fails", 0) >= FAIL_ALERT]
    newly_blind = [b for b in blind if b["failed_runs"] == FAIL_ALERT]

    try:
        pending = load_json(wd_path(wd, "new_items.json"), {}) or {}
    except ValueError:
        pending = {}
    carried = [i for i in pending.get("items") or [] if isinstance(i, dict) and i.get("id")]
    have = {i["id"] for i in new_items}
    items = [i for i in carried if i["id"] not in have] + new_items
    dropped = max(0, len(items) - PENDING_CAP)
    items = items[-PENDING_CAP:]
    if "--inject-test" in args:
        items.append(test_item(stack, now))
    st["last_run"] = now
    save_json(wd_path(wd, "state.json"), st)
    out = {"run": now + "#" + os.urandom(3).hex(), "items": items, "carried_from_earlier_runs": len(carried),
           "dropped_over_cap": dropped, "could_not_look": newly_blind, "still_failing": blind,
           "errors": errors, "stack": stack_brief(stack)}
    if items or newly_blind or not os.path.exists(wd_path(wd, "new_items.json")):
        save_json(wd_path(wd, "new_items.json"), out)
    hinted = sum(1 for i in items if i.get("hint"))
    msg = f"{now} sources {len(sources)} new {len(new_items)} pending {len(items)} hinted {hinted} errors {len(errors)}"
    if baselined:
        msg += " baselined " + ",".join(baselined)
    print(msg)
    for n, e in sorted(errors.items()):
        print(f"  could not look: {n}: {e}")
    if baseline:
        sys.exit(2 if errors else 0)
    sys.exit(10 if items or newly_blind else (2 if errors else 0))


def test_item(stack, now):
    pick = None
    for eco, names in list((stack.get("direct") or {}).items()) + list((stack.get("packages") or {}).items()):
        if names:
            pick = f"{eco}:{names[0]}"
            break
    if not pick and stack.get("services"):
        pick = "service:" + stack["services"][0].get("name", "unknown")
    pick = pick or "npm:left-pad"
    return {"id": "WATCHDOG-TEST-" + now.replace(":", "").replace("-", ""), "source": "self-test", "test": True,
            "summary": f"TEST ONLY, NOT REAL: synthetic malicious release of {pick} to check the watchdog pipeline",
            "url": "", "packages": [pick], "hint": [pick]}


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)
    wd = os.path.abspath(os.path.expanduser("~/.security-watchdog" if sys.argv[1] == "-" else sys.argv[1]))
    args = sys.argv[2:]
    if not os.path.isdir(wd):
        sys.exit(f"config error: watchdog folder {wd} does not exist")
    if "--print-cmd" in args:
        i = args.index("--print-cmd")
        print_cmd(wd, args[i + 1] if i + 1 < len(args) else "", "--json" in args)
    elif "--get" in args:
        v = config(wd).get(args[args.index("--get") + 1], "")
        print(v if not isinstance(v, (list, dict)) else json.dumps(v))
    elif "--after-judge" in args:
        after_judge(wd)
    elif "--pending-triage" in args:
        pending_triage(wd)
    elif "--after-triage" in args:
        after_triage(wd)
    elif "--status" in args:
        status(wd)
    else:
        poll(wd, args)


if __name__ == "__main__":
    main()
