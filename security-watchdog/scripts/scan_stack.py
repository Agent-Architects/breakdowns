#!/usr/bin/env python3
"""Map a user's stack for the security watchdog.

usage: scan_stack.py <out stack.json> <project folder> [<project folder> ...] [--no-home]

Reads lockfiles and manifests under the given folders (npm, yarn, pnpm, bun, PyPI, Go, Cargo, RubyGems,
Composer, GitHub Actions workflows) and, unless --no-home, the local machine: OS, installed CLIs, MCP servers
configured in AI tools, and editor extensions. Writes:
  packages   {ecosystem: [every package name, direct and transitive]}   (the script matches advisories on these)
  direct     {ecosystem: [names declared in manifests]}                 (what the weak model reads)
  repos      [{path, manifests, deploy, env_names}]                     (env_names = variable NAMES only, never values)
  tools, ai {mcp_servers, configs}, extensions, machine, scanned_at
  services   kept exactly as they were: the agent adds them (see SKILL.md); this script never removes them.
Stdlib only, Python 3.9+. Never reads or stores a secret value."""
import json
import os
import platform
import re
import shutil
import sys
import time

SKIP = {"node_modules", "venv", "env", "__pycache__", "dist", "build", "target", "vendor", "site-packages",
        "bower_components", "Pods", "DerivedData", "coverage"}
MAX_FILE = 60 * 1024 * 1024
ECOS = ("npm", "PyPI", "Go", "crates.io", "RubyGems", "Packagist", "GitHub Actions")
DEPLOY = {"railway.json", "railway.toml", "vercel.json", "fly.toml", "wrangler.toml", "wrangler.json",
          "wrangler.jsonc", "netlify.toml", "render.yaml", "app.yaml", "Dockerfile", "docker-compose.yml",
          "docker-compose.yaml", "compose.yaml", "compose.yml", "Procfile", "serverless.yml", "firebase.json",
          "amplify.yml", "Chart.yaml", ".gitlab-ci.yml", "bitbucket-pipelines.yml", "heroku.yml", "now.json"}
TOOLS = ["git", "gh", "docker", "podman", "kubectl", "helm", "terraform", "tofu", "pulumi", "ansible", "aws", "gcloud",
         "az", "doctl", "hcloud", "flyctl", "fly", "railway", "vercel", "netlify", "wrangler", "supabase", "firebase",
         "heroku", "tailscale", "cloudflared", "ngrok", "node", "npm", "pnpm", "yarn", "bun", "deno", "python3",
         "pip", "uv", "poetry", "go", "cargo", "ruby", "php", "java", "brew", "ollama", "claude", "codex", "gemini",
         "opencode", "cursor", "cursor-agent", "agent", "code", "windsurf", "aider", "goose", "copilot", "agy",
         "redis-server", "postgres", "psql", "mysql", "mongod", "nginx", "caddy"]


def read(path):
    try:
        if os.path.getsize(path) > MAX_FILE:
            return ""
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def load(path):
    try:
        return json.loads(read(path) or "null", strict=False)
    except ValueError:
        return None


def pep503(n):
    return re.sub(r"[-_.]+", "-", n.strip().lower())


# ---------------------------------------------------------------- npm family
def npm_lock(path, allp, _direct):
    j = load(path) or {}

    def deps_v1(d):            # lockfile v1 nests dependencies
        for k, v in (d or {}).items():
            allp.add(k)
            if isinstance(v, dict):
                deps_v1(v.get("dependencies"))
    for k in (j.get("packages") or {}):
        if "node_modules/" in k:
            allp.add(k.split("node_modules/")[-1])
    deps_v1(j.get("dependencies"))


def pkg_json(path, allp, direct):
    j = load(path) or {}
    for sec in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
        d = j.get(sec)
        if isinstance(d, dict):
            allp.update(d.keys())
            direct.update(d.keys())


def yarn_lock(path, allp, _direct):
    for line in read(path).splitlines():
        if not line or line[0] in " #" or not line.endswith(":") or line.startswith("__metadata"):
            continue
        for entry in line[:-1].split(","):
            m = re.match(r'\s*"?((?:@[^@/"\s]+/)?[^@/"\s]+)@', entry)
            if m:
                allp.add(m.group(1))


def pnpm_lock(path, allp, _direct):
    for m in re.finditer(r"""^  ['"]?/?((?:@[^/@\s'"]+/)?[^/@\s'"(]+)[@/]\d""", read(path), re.M):
        allp.add(m.group(1))


def bun_lock(path, allp, _direct):
    for m in re.finditer(r'^\s*"((?:@[^"/]+/)?[^"@/]+)":\s*\["', read(path), re.M):
        allp.add(m.group(1))


# ---------------------------------------------------------------- Python
def py_reqs(path, allp, direct):
    for line in read(path).splitlines():
        line = line.split(" #")[0].strip()
        if not line or line.startswith(("#", "-")) or ("://" in line and " @ " not in line):
            continue
        m = re.match(r"([A-Za-z0-9][A-Za-z0-9._-]*)", line)
        if m:
            allp.add(pep503(m.group(1)))
            direct.add(pep503(m.group(1)))


def py_lock(path, allp, _direct):       # poetry.lock, uv.lock, pdm.lock: [[package]] name = "x"
    for m in re.finditer(r'^name\s*=\s*"([^"]+)"', read(path), re.M):
        allp.add(pep503(m.group(1)))


def pipfile_lock(path, allp, _direct):
    j = load(path) or {}
    for sec in ("default", "develop"):
        allp.update(pep503(k) for k in (j.get(sec) or {}))


def pyproject(path, allp, direct):
    t = read(path)
    names = set()
    try:
        import tomllib                    # Python 3.11+
        d = tomllib.loads(t)
        proj = d.get("project") or {}
        reqs = list(proj.get("dependencies") or [])
        for v in (proj.get("optional-dependencies") or {}).values():
            reqs += v
        for v in (d.get("dependency-groups") or {}).values():
            reqs += [x for x in v if isinstance(x, str)]
        names.update(re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", r).group(1) for r in reqs
                     if re.match(r"\s*[A-Za-z0-9]", r))
        poetry = (d.get("tool") or {}).get("poetry") or {}
        for sec in [poetry.get("dependencies") or {}, poetry.get("dev-dependencies") or {}] + \
                [g.get("dependencies") or {} for g in (poetry.get("group") or {}).values()]:
            names.update(sec.keys())
    except ImportError:              # Python 3.9/3.10: read only the dependency tables, section by section
        arr = r"""=\s*\[((?:\s*(?:"[^"]*"|'[^']*'|#[^\n]*)\s*,?)*)\s*\]"""
        for sec in re.finditer(r"^\[([^\]\n]+)\]\s*$(.*?)(?=^\[|\Z)", t, re.M | re.S):
            head, body = sec.group(1).strip(), sec.group(2)
            if head == "project":
                bodies = [m.group(1) for m in re.finditer(r"^dependencies\s*" + arr, body, re.M)]
            elif head in ("project.optional-dependencies", "dependency-groups"):
                bodies = [m.group(1) for m in re.finditer(r"^[\w.-]+\s*" + arr, body, re.M)]
            elif re.match(r"tool\.poetry\.(?:[\w.-]*\.)?(?:dev-)?dependencies$", head):
                names.update(re.findall(r"^([A-Za-z0-9][A-Za-z0-9._-]*)\s*=", body, re.M))
                continue
            else:
                continue
            for b in bodies:
                for q in re.finditer(r""""([^"]*)"|'([^']*)'""", b):
                    m = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", q.group(1) or q.group(2) or "")
                    if m:
                        names.add(m.group(1))
    except Exception:
        pass
    names.discard("python")
    names = {pep503(n) for n in names if n}
    allp.update(names)
    direct.update(names)


# ---------------------------------------------------------------- others
def go_mod(path, allp, direct):
    for m in re.finditer(r"^\s*(?:require\s+)?([A-Za-z0-9.\-]+\.[A-Za-z]+/\S+)\s+v\d\S*(\s*//\s*indirect)?",
                         read(path), re.M):
        allp.add(m.group(1))
        if not m.group(2):
            direct.add(m.group(1))


def cargo_lock(path, allp, _direct):
    for m in re.finditer(r'^name\s*=\s*"([^"]+)"', read(path), re.M):
        allp.add(m.group(1))


def cargo_toml(path, allp, direct):
    for sec in re.finditer(r"^\[(?:[\w.-]*\.)?(?:dev-|build-)?dependencies\]\n(.*?)(?=^\[|\Z)", read(path), re.S | re.M):
        n = re.findall(r"^([A-Za-z0-9_-]+)\s*=", sec.group(1), re.M)
        allp.update(n)
        direct.update(n)


def gemfile_lock(path, allp, _direct):
    for m in re.finditer(r"^    ([A-Za-z0-9_.\-]+) \(", read(path), re.M):
        allp.add(m.group(1))


def composer_lock(path, allp, _direct):
    j = load(path) or {}
    for sec in ("packages", "packages-dev"):
        allp.update(p.get("name") for p in j.get(sec) or [] if isinstance(p, dict) and p.get("name"))


def workflow(path, allp, direct):
    for m in re.finditer(r"""uses:\s*['"]?([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)(?:/[^@\s'"]*)?@""", read(path)):
        allp.add(m.group(1))
        direct.add(m.group(1))


def env_names(path):
    """Variable NAMES from a .env file. Values are never read into memory beyond the line split."""
    out = []
    for line in read(path).splitlines():
        m = re.match(r"\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=", line)
        if m:
            out.append(m.group(1))
    return out


PARSERS = {"package-lock.json": ("npm", npm_lock), "npm-shrinkwrap.json": ("npm", npm_lock),
           "package.json": ("npm", pkg_json), "yarn.lock": ("npm", yarn_lock), "pnpm-lock.yaml": ("npm", pnpm_lock),
           "bun.lock": ("npm", bun_lock), "poetry.lock": ("PyPI", py_lock), "uv.lock": ("PyPI", py_lock),
           "pdm.lock": ("PyPI", py_lock), "Pipfile.lock": ("PyPI", pipfile_lock), "pyproject.toml": ("PyPI", pyproject),
           "go.mod": ("Go", go_mod), "Cargo.lock": ("crates.io", cargo_lock), "Cargo.toml": ("crates.io", cargo_toml),
           "Gemfile.lock": ("RubyGems", gemfile_lock), "composer.lock": ("Packagist", composer_lock)}


def scan_roots(roots, allp, direct):
    repos = {}

    def repo_for(d):
        p = d
        while True:
            if p in repos:
                return repos[p]
            parent = os.path.dirname(p)
            if parent == p:
                return None
            p = parent

    for root in roots:
        root = os.path.abspath(os.path.expanduser(root))
        if not os.path.isdir(root):
            print(f"warning: {root} is not a folder, skipped", file=sys.stderr)
            continue
        for d, dirs, files in os.walk(root):
            if ".git" in dirs or ".git" in files:
                repos[d] = {"path": d, "manifests": [], "deploy": [], "env_names": []}
            dirs[:] = [x for x in dirs if x not in SKIP and (not x.startswith(".") or x == ".github")]
            repo = repo_for(d) or repos.setdefault(root, {"path": root, "manifests": [], "deploy": [], "env_names": []})
            rel = os.path.relpath(d, repo["path"])
            for f in files:
                p = os.path.join(d, f)
                relf = os.path.normpath(os.path.join(rel, f))
                if f in PARSERS or re.match(r"requirements[\w.-]*\.txt$", f):
                    eco, fn = PARSERS.get(f, ("PyPI", py_reqs))
                    fn(p, allp[eco], direct[eco])
                    repo["manifests"].append(relf)
                elif f.endswith((".yml", ".yaml")) and os.path.basename(d) == "workflows" and \
                        os.path.basename(os.path.dirname(d)) == ".github":
                    workflow(p, allp["GitHub Actions"], direct["GitHub Actions"])
                    repo["deploy"].append(relf)
                elif f in DEPLOY or f.endswith(".tf") or (f == "config.toml" and os.path.basename(d) == "supabase"):
                    repo["deploy"].append(relf)
                elif f.startswith(".env") and not f.endswith((".py", ".js", ".ts", ".sh")):
                    repo["env_names"] = sorted(set(repo["env_names"]) | set(env_names(p)))
    for r in repos.values():
        r["manifests"] = sorted(set(r["manifests"]))[:200]
        r["deploy"] = sorted(set(r["deploy"]))[:200]
    return sorted((r for r in repos.values() if r["manifests"] or r["deploy"] or os.path.isdir(os.path.join(r["path"], ".git"))
                   or os.path.isfile(os.path.join(r["path"], ".git"))), key=lambda r: r["path"])


# ---------------------------------------------------------------- local machine
def home_paths():
    h = os.path.expanduser("~")
    appdata = os.environ.get("APPDATA") or os.path.join(h, "AppData", "Roaming")
    mac_sup = os.path.join(h, "Library", "Application Support")
    xdg = os.environ.get("XDG_CONFIG_HOME") or os.path.join(h, ".config")
    code_user = [os.path.join(b, n, "User") for b in (mac_sup, xdg, appdata) for n in ("Code", "Cursor", "Windsurf")]
    mcp = [("claude-code", os.path.join(h, ".claude.json")),
           ("claude-code", os.path.join(h, ".claude", "settings.json")),
           ("claude-desktop", os.path.join(mac_sup, "Claude", "claude_desktop_config.json")),
           ("claude-desktop", os.path.join(appdata, "Claude", "claude_desktop_config.json")),
           ("claude-desktop", os.path.join(xdg, "Claude", "claude_desktop_config.json")),
           ("cursor", os.path.join(h, ".cursor", "mcp.json")),
           ("gemini", os.path.join(h, ".gemini", "settings.json")),
           ("windsurf", os.path.join(h, ".codeium", "windsurf", "mcp_config.json")),
           ("opencode", os.path.join(xdg, "opencode", "opencode.json")),
           ("codex", os.path.join(h, ".codex", "config.toml"))]
    mcp += [("vscode-family", os.path.join(u, f)) for u in code_user for f in ("mcp.json", "settings.json")]
    ext = [os.path.join(h, d, "extensions") for d in (".vscode", ".vscode-insiders", ".cursor", ".windsurf", ".vscode-oss")]
    return h, mcp, ext


def server_package(spec):
    """npx/uvx style launches name a package that never shows up in a lockfile."""
    if not isinstance(spec, dict):
        return None
    cmd = os.path.basename(str(spec.get("command") or "")).lower().replace(".cmd", "").replace(".exe", "")
    args = [str(a) for a in spec.get("args") or []] if isinstance(spec.get("args"), list) else []
    if isinstance(spec.get("command"), list):          # opencode: "command": ["npx", "-y", "pkg"]
        parts = [str(x) for x in spec["command"]]
        cmd, args = os.path.basename(parts[0]).lower(), parts[1:]
    eco = {"npx": "npm", "bunx": "npm", "pnpx": "npm", "uvx": "PyPI", "pipx": "PyPI"}.get(cmd)
    if cmd in ("pnpm", "yarn", "npm", "bun") and args[:1] in (["dlx"], ["exec"], ["x"]):
        eco, args = "npm", args[1:]
    if cmd == "uv" and args[:2] == ["tool", "run"]:
        eco, args = "PyPI", args[2:]
    if not eco:
        return None
    skip_next = False
    for a in args:
        if skip_next:
            skip_next = False
            continue
        if a in ("--from", "--package", "-p", "--with"):
            skip_next = a in ("--with",)
            continue
        if a.startswith("-") or a in ("run", "exec"):
            continue
        name = re.sub(r"(?<=.)@[^/]*$", "", a) if eco == "npm" else re.split(r"[=<>@\[]", a)[0]
        return eco, (pep503(name) if eco == "PyPI" else name)
    return None


def scan_home(allp, direct):
    h, mcp_files, ext_dirs = home_paths()
    servers, configs = {}, []

    def add(label, name, spec):
        key = f"{label}:{name}"
        pkg = server_package(spec)
        servers[key] = {"name": name, "tool": label, "package": f"{pkg[0]}:{pkg[1]}" if pkg else None}
        if pkg:
            allp[pkg[0]].add(pkg[1])
            direct[pkg[0]].add(pkg[1])

    for label, path in mcp_files:
        if not os.path.isfile(path):
            continue
        configs.append(path.replace(h, "~", 1))
        if path.endswith(".toml"):
            for m in re.finditer(r'^\[mcp_servers\.("[^"]+"|[^\].\s]+)\]\s*\n(.*?)(?=^\[|\Z)', read(path), re.M | re.S):
                c = re.search(r'^command\s*=\s*"([^"]+)"', m.group(2), re.M)
                a = re.search(r"^args\s*=\s*\[(.*?)\]", m.group(2), re.M | re.S)
                add(label, m.group(1).strip('"'), {"command": c.group(1) if c else "",
                                                    "args": re.findall(r'"([^"]*)"', a.group(1)) if a else []})
            continue
        j = load(path)
        if not isinstance(j, dict):
            continue
        blocks = [j.get("mcpServers"), j.get("mcp"), (j.get("mcp") or {}).get("servers") if isinstance(j.get("mcp"), dict) else None,
                  j.get("servers") if path.endswith("mcp.json") else None]
        for p in (j.get("projects") or {}).values() if isinstance(j.get("projects"), dict) else []:
            if isinstance(p, dict):
                blocks.append(p.get("mcpServers"))
        for b in blocks:
            if isinstance(b, dict):
                for name, spec in b.items():
                    if isinstance(spec, dict) and name != "servers":
                        add(label, name, spec)
    exts = set()
    for d in ext_dirs:
        try:
            for e in os.listdir(d):
                m = re.match(r"([A-Za-z0-9][\w-]*\.[\w.-]+?)-\d+\.\d+", e)
                if m:
                    exts.add(m.group(1).lower())
        except OSError:
            pass
    tools = sorted({t for t in TOOLS if shutil.which(t)})
    ai_dirs = [p.replace(h, "~", 1) for p in (os.path.join(h, x) for x in
               (".claude", ".codex", ".cursor", ".gemini", ".codeium", ".continue", ".aider.conf.yml", ".ollama"))
               if os.path.exists(p)]
    return tools, {"mcp_servers": sorted(servers.values(), key=lambda s: (s["tool"], s["name"])),
                   "configs": configs, "ai_dirs": ai_dirs}, sorted(exts)


def main():
    argv = [a for a in sys.argv[1:] if a != "--no-home"]
    if len(argv) < 2:
        print(__doc__)
        sys.exit(1)
    out_path, roots = os.path.abspath(os.path.expanduser(argv[0])), argv[1:]
    try:
        with open(out_path, encoding="utf-8") as f:
            prev = json.load(f)
    except (OSError, ValueError):
        prev = {}
    allp = {e: set() for e in ECOS}
    direct = {e: set() for e in ECOS}
    repos = scan_roots(roots, allp, direct)
    stack = {"scanned_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "roots": roots,
             "machine": {"os": platform.system(), "release": platform.release(), "arch": platform.machine()}}
    if "--no-home" not in sys.argv:
        stack["tools"], stack["ai"], stack["extensions"] = scan_home(allp, direct)
    else:
        for k in ("tools", "ai", "extensions"):
            if k in prev:
                stack[k] = prev[k]
    stack["services"] = prev.get("services", [])
    stack["servers"] = prev.get("servers", [])
    stack["direct"] = {k: sorted(v) for k, v in direct.items() if v}
    stack["repos"] = repos
    stack["packages"] = {k: sorted(v) for k, v in allp.items() if v}
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(stack, f, indent=1, ensure_ascii=False)
    os.replace(tmp, out_path)
    pk = ", ".join(f"{k} {len(v)} ({len(stack['direct'].get(k, []))} direct)" for k, v in stack["packages"].items())
    print(f"{out_path}: {pk or 'no packages'}; repos {len(repos)}; tools {len(stack.get('tools', []))}; "
          f"mcp servers {len((stack.get('ai') or {}).get('mcp_servers', []))}; extensions {len(stack.get('extensions', []))}; "
          f"services {len(stack['services'])} (added by the agent)")


if __name__ == "__main__":
    main()
