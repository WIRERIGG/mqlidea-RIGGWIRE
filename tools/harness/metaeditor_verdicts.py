#!/usr/bin/env python3
"""MetaEditor referee for the plugin harness (specs/001-metaeditor-harness).

Compiles each corpus program with MetaQuotes' MetaEditor and stores its verdict (errors and
warnings with file and line) so the plugin's diagnostics can be scored against the real
compiler. Read-only toward MetaTrader: every program is staged under /tmp (copies, with the
Standard Library linked in), so MetaEditor writes its .ex5 and per-file log there, never into
MetaTrader's MQL5 folder or a corpus repository. The one write MetaTrader always gets from any
compile is the summary line MetaEditor appends to <MetaTrader>/logs/metaeditor.log, outside MQL5.

Never compiles beside a backtest or another MetaEditor (checked before every compile), and
holds its own lock so two harness runs never overlap.

    metaeditor_verdicts.py --self-test
    metaeditor_verdicts.py --corpus tools/harness/corpus.json [--source NAME] [--stage-only]
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mutate  # noqa: E402

HOME = Path.home()
WINE = Path("/Applications/MetaTrader 5.app/Contents/SharedSupport/wine/bin/wine64")
WINEPREFIX = HOME / "Library/Application Support/net.metaquotes.wine.metatrader5"
MT5_ROOT = Path(os.environ.get("MT5_ROOT", WINEPREFIX / "drive_c/Program Files/MetaTrader 5"))
MQL5 = MT5_ROOT / "MQL5"
STAGE_ROOT = Path(os.environ.get("MQL_HARNESS_STAGE", "/tmp/mqlidea-harness"))
STORE = Path(os.environ.get("MQL_HARNESS_STORE", HOME / ".cache/mqlidea-harness/verdicts"))
LOCK = Path(os.environ.get("MQL_HARNESS_LOCK", "/tmp/mqlidea-harness.lock"))
COMPILE_TIMEOUT = int(os.environ.get("MQL_HARNESS_TIMEOUT", "180"))
MUTANTS_PER_KIND = int(os.environ.get("MQL_HARNESS_MUTANTS", "2"))  # per clean program and kind (FR-017)
MUTATION_SEED = os.environ.get("MQL_HARNESS_SEED", "20261117")

# MetaQuotes' own Standard Library (same list as tools/corpus-gate.sh): the rest of Include is the user's.
MQL5_FOLDERS = ["Experts", "Indicators", "Scripts", "Libraries", "Files", "Images", "Sounds"]
STDLIB = ["Arrays", "Canvas", "ChartObjects", "Charts", "Controls", "Expert", "Files", "Generic", "Graphics",
          "Indicators", "Math", "OpenCL", "Strings", "Tools", "Trade", "WinAPI", "Object.mqh", "StdLibErr.mqh",
          "VirtualKeys.mqh", "MovingAverages.mqh"]


# ---- busy check (research R4, FR-019) ---------------------------------------------------------------

def read_process_table():
    """Command lines of every process, or None when the table can't be read (which counts as busy)."""
    try:
        out = subprocess.run(["ps", "-axww", "-o", "command="], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.splitlines() if out.returncode == 0 else None


def _runs(line, exe):
    low = line.lower()
    return f"\\{exe}" in low or f"/{exe}" in low or low.startswith(exe)


def busy_reason(table, own_pids=()):
    """Why compiling now could disturb MetaTrader or another compile, or None when it is safe.

    Busy: any strategy-tester agent (metatester64.exe; until T001 shows whether idle /run agents
    persist, every agent counts, the safe side of the ruin line), an `mt5 backtest` driver, a
    terminal64.exe started with /config: (a tester run), or another MetaEditor. A plain terminal with
    charts open is not busy. An unreadable table is busy."""
    if table is None:
        return "process table unreadable"
    for line in table:
        if any(str(p) in line.split()[:1] for p in own_pids):
            continue
        if _runs(line, "metatester64.exe"):
            return "strategy tester agent running: " + line[:120]
        if re.search(r"\bmt5 backtest\b", line):
            return "mt5 backtest running: " + line[:120]
        if _runs(line, "terminal64.exe") and "/config:" in line.lower():
            return "tester run of terminal64: " + line[:120]
        if _runs(line, "metaeditor64.exe"):
            return "another MetaEditor running: " + line[:120]
    return None


# ---- MetaTrader untouched (FR, T005) ----------------------------------------------------------------

def snapshot(root):
    """{relative path: (size, mtime_ns)} of every file under root."""
    snap = {}
    for dirpath, _, files in os.walk(root):
        for f in files:
            p = Path(dirpath) / f
            try:
                st = p.lstat()
            except OSError:
                continue
            snap[str(p.relative_to(root))] = (st.st_size, st.st_mtime_ns)
    return snap


def snapshot_diff(before, after):
    """Sorted list of 'added|removed|changed path' lines; empty when nothing changed."""
    out = [f"added {p}" for p in after.keys() - before.keys()]
    out += [f"removed {p}" for p in before.keys() - after.keys()]
    out += [f"changed {p}" for p in before.keys() & after.keys() if before[p] != after[p]]
    return sorted(out)


# ---- lock (FR-019) ----------------------------------------------------------------------------------

def acquire_lock(path=None):
    path = path or LOCK
    """Takes the harness lock (owner PID inside); a lock whose owner is gone is taken over."""
    while True:
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return True
        except FileExistsError:
            try:
                owner = int(Path(path).read_text().strip() or "0")
            except (OSError, ValueError):
                owner = 0
            if owner and owner != os.getpid() and _alive(owner):
                return False
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass


def release_lock(path=None):
    path = path or LOCK
    try:
        if Path(path).read_text().strip() == str(os.getpid()):
            os.unlink(path)
    except OSError:
        pass


def _alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


# ---- log parser (T006) ------------------------------------------------------------------------------

LOCATED = re.compile(r"^\s*(.+?)\((\d+),(\d+)\)\s*:\s*(error|warning)\s*(\d+)?\s*:?\s*(.*\S)\s*$", re.I)
RESULT = re.compile(r"^\s*result:\s*(\d+)\s*errors?,\s*(\d+)\s*warnings?", re.I)


def decode_log(data):
    """MetaEditor's logs are UTF-16 with a BOM; sources are UTF-16, UTF-8 (BOM or not) or ANSI."""
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        text = data.decode("utf-16")
    elif len(data) > 1 and data[1:2] == b"\x00":
        text = data.decode("utf-16-le")
    else:
        text = data.decode("utf-8", "replace")
    return text[1:] if text.startswith("\ufeff") else text


def parse_log(text, to_repo_path):
    """(diagnostics, result) from a MetaEditor per-file log. `to_repo_path(log_path)` maps the path
    MetaEditor printed to a repo-relative one (or a '<stdlib>/...' / '<unknown>/...' label).
    result is (errors, warnings) from the Result line, or None when the log has none."""
    diags, result = [], None
    for line in text.splitlines():
        m = LOCATED.match(line)
        if m:
            diags.append({"file": to_repo_path(m[1].strip()), "line": int(m[2]), "col": int(m[3]),
                          "severity": m[4].lower(), "code": int(m[5]) if m[5] else 0, "message": m[6]})
            continue
        r = RESULT.match(line)
        if r:
            result = (int(r[1]), int(r[2]))
    diags.sort(key=lambda d: (d["file"], d["line"], d["col"], d["severity"], d["code"], d["message"]))
    return diags, result


def path_mapper(stage_mql5, mapping):
    """A to_repo_path for parse_log: MetaEditor prints absolute (Z:\\tmp\\...) or MQL5-relative paths;
    `mapping` is {staged path relative to stage_mql5: repo-relative path}."""
    stage_mql5 = Path(stage_mql5)

    def to_repo(printed):
        p = printed.replace("\\", "/")
        if re.match(r"^[A-Za-z]:/", p):
            p = p[2:] if p[0] in "Zz" else p
        p = Path(p)
        if not p.is_absolute():
            parts = p.parts
            p = stage_mql5.joinpath(*parts[1:]) if parts and parts[0].lower() == "mql5" else stage_mql5 / p
        try:
            rel = str(p.relative_to(stage_mql5))
        except ValueError:
            return "<unknown>/" + p.name
        if rel in mapping:
            return mapping[rel]
        first = Path(rel).parts[1] if rel.startswith("Include/") and len(Path(rel).parts) > 1 else None
        if first in STDLIB:
            return "<stdlib>/" + rel[len("Include/"):]
        return "<unknown>/" + rel
    return to_repo


# ---- verdict key and store (T007, research R3) -------------------------------------------------------

def metaeditor_build(exe=None):
    """MetaEditor's build number from its version resource ("5.0.0.5430" -> 5430), or 0."""
    exe = Path(exe or MT5_ROOT / "MetaEditor64.exe")
    try:
        data = exe.read_bytes()
    except OSError:
        return 0
    marker = "FileVersion".encode("utf-16-le")
    i = data.find(marker)
    while i >= 0:
        tail = data[i + len(marker):i + len(marker) + 80]
        m = re.search(r"(\d+)\.(\d+)\.(\d+)\.(\d+)", tail.decode("utf-16-le", "ignore"))
        if m:
            return int(m[4])
        i = data.find(marker, i + 1)
    return 0


def verdict_key(program_bytes, header_files, build, where=""):
    """sha256 over where the program sits (source and path: quoted includes resolve beside it), its
    bytes, every header-root file (sorted by relative path, path and bytes both hashed) and the
    MetaEditor build: a header edit or MetaEditor update invalidates it."""
    h = hashlib.sha256()
    h.update(b"where\0" + where.encode() + b"\0program\0" + program_bytes + b"\0build\0" + str(build).encode())
    for rel, data in sorted(header_files):
        h.update(b"\0header\0" + rel.encode() + b"\0" + data)
    return h.hexdigest()


def store_path(key, store=None):
    return Path(store or STORE) / f"{key}.json"


def load_verdict(key, store=None):
    p = store_path(key, store)
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return None


def save_verdict(verdict, store=None):
    p = store_path(verdict["key"], store)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(verdict, indent=1, sort_keys=True))
    os.replace(tmp, p)


# ---- staging --------------------------------------------------------------------------------------

def stage_source(source, stage_root=None, mql5=None):
    """Stages one corpus source: MQL5/Include links the Standard Library entries (or, with
    "link_metatrader_include", every entry of MetaTrader's Include, for the owner's EA) and holds
    copies of the source's header roots; MQL5/Experts/<name>/ holds a copy of the whole repository,
    names unchanged, so quoted includes resolve beside each program and MetaEditor's outputs land in
    /tmp. MetaEditor under Wine can't compile from a path with a space: a program whose file name has
    one gets a space-free copy beside it, and staged folder names replace spaces with '_' (quoted
    includes name files, rarely folders; one that does shows up as missing-include).
    Every repository header no program includes gets a stub program in MQL5/Scripts/<name>/ (FR-018):
    its #include and an empty OnStart, in /tmp only. A stub's verdict is filed under the header's
    repo path, so the plugin side scores the header itself; errors MetaEditor puts on the stub's own
    lines map to "<stub>/..." and never count.
    Returns (stage_mql5, mapping staged-rel -> repo-rel, programs as staged-rel paths, unsupported
    repo-rel paths, stubs staged-rel -> header repo-rel)."""
    stage_root, mql5 = stage_root or STAGE_ROOT, mql5 or MQL5
    repo = Path(source["path"]).expanduser()
    stage_mql5 = Path(stage_root) / source["name"].replace(" ", "_") / "MQL5"
    if stage_mql5.exists():
        shutil.rmtree(stage_mql5)
    include = stage_mql5 / "Include"
    include.mkdir(parents=True)
    linked = sorted(e.name for e in (mql5 / "Include").iterdir()) if source.get("link_metatrader_include") and (mql5 / "Include").exists() else STDLIB
    for entry in linked:
        src = mql5 / "Include" / entry
        if src.exists():
            (include / entry).symlink_to(src)
    mapping = {}
    mount = Path(source.get("include_as", ""))  # "MALE5": the repo is meant to sit at Include/MALE5
    for root in source.get("include_roots", []):
        root_dir = repo / root
        for f in sorted(root_dir.rglob("*")):
            if f.is_file() and ".git" not in f.relative_to(repo).parts:
                rel = mount / f.relative_to(root_dir)
                if rel.parts[0] in linked:
                    continue  # never shadow the Standard Library
                dest = include / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dest)
                mapping[str(dest.relative_to(stage_mql5))] = str(f.relative_to(repo))
    # #resource "\\Indicators\\X.ex5" resolves from the MQL5 root: a repo laid out like an MQL5
    # folder (at its top or under MQL5/) also gets those folders mirrored there, names space-free
    for layout in (repo, repo / "MQL5"):
        for folder in MQL5_FOLDERS:
            top = layout / folder
            if not top.is_dir():
                continue
            for f in sorted(top.rglob("*")):
                rel = f.relative_to(repo)
                if f.is_file() and ".git" not in rel.parts:
                    dest = stage_mql5.joinpath(folder, *[d.replace(" ", "_") for d in f.relative_to(top).parts[:-1]], f.name)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, dest)
                    mapping.setdefault(str(dest.relative_to(stage_mql5)), str(rel))
    experts = stage_mql5 / "Experts" / source["name"].replace(" ", "_")
    programs, unsupported = [], []
    wanted = {p.resolve() for p in repo.glob(source.get("programs", "**/*.mq5"))}
    for f in sorted(repo.rglob("*")):
        rel = f.relative_to(repo)
        if not f.is_file() or ".git" in rel.parts:
            continue
        dest = experts.joinpath(*[d.replace(" ", "_") for d in rel.parts[:-1]], rel.name)  # folders space-free
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)
        mapping[str(dest.relative_to(stage_mql5))] = str(rel)
        if f.resolve() not in wanted:
            continue
        if " " in str(dest.parent):
            unsupported.append(str(rel))
            continue
        if " " in dest.name:
            spaced = dest
            dest = dest.with_name(dest.name.replace(" ", "_"))
            shutil.copy2(spaced, dest)
            mapping[str(dest.relative_to(stage_mql5))] = str(rel)
        programs.append(str(dest.relative_to(stage_mql5)))
    stubs = {}
    covered = included_repo_files(stage_mql5, mapping, programs)
    prefix = str(experts.relative_to(stage_mql5)) + "/"
    headers = sorted((staged, rel) for staged, rel in mapping.items()
                     if staged.startswith(prefix) and rel.lower().endswith(".mqh") and rel not in covered)
    for n, (staged, rel) in enumerate(headers, 1):
        stub = stage_mql5 / "Scripts" / source["name"].replace(" ", "_") / f"stub_{n}.mq5"
        stub.parent.mkdir(parents=True, exist_ok=True)
        target = os.path.relpath(stage_mql5 / staged, stub.parent).replace("/", "\\")
        stub.write_text(f'// harness stub for {rel} (FR-018)\n#include "{target}"\nvoid OnStart() {{ }}\n')
        staged_stub = str(stub.relative_to(stage_mql5))
        mapping[staged_stub] = "<stub>/" + rel
        stubs[staged_stub] = rel
        programs.append(staged_stub)
    return stage_mql5, mapping, programs, unsupported, stubs


INCLUDE = re.compile(r'^\s*#\s*include\s*([<"])([^>"]+)[>"]', re.M)


def included_repo_files(stage_mql5, mapping, programs):
    """Repo paths of every staged file the programs reach through #include, read as text the way
    MetaEditor resolves it: "x" beside the including file first, then MQL5/Include; <x> from Include.
    File names compare case-insensitively, as on Windows."""
    by_lower = {k.lower(): k for k in mapping}
    seen, queue = set(), list(programs)
    while queue:
        staged = queue.pop()
        if staged in seen:
            continue
        seen.add(staged)
        try:
            text = decode_log((Path(stage_mql5) / staged).read_bytes())
        except OSError:
            continue
        for quote, name in INCLUDE.findall(text):
            name = name.strip().replace("\\", "/")
            options = ([os.path.join(os.path.dirname(staged), name)] if quote == '"' else []) + [os.path.join("Include", name)]
            for option in options:
                hit = by_lower.get(os.path.normpath(option).lower())
                if hit:
                    queue.append(hit)
                    break
    return {mapping[s] for s in seen if s in mapping}


def header_files(source):
    """(repo-relative path, bytes) of every file in the source's header roots and every .mqh/.h in
    the repository (a quoted include can reach one outside the roots), for the key. Programs are
    left out, so editing one program invalidates only its own verdict."""
    repo = Path(source["path"]).expanduser()
    out = {}
    files = [f for root in source.get("include_roots", []) for f in (repo / root).rglob("*")]
    files += [f for f in repo.rglob("*") if f.suffix.lower() in (".mqh", ".h")]
    for f in files:
        rel = f.relative_to(repo)
        if f.is_file() and ".git" not in rel.parts:
            out[str(rel)] = f.read_bytes()
    return sorted(out.items())


# ---- compile ----------------------------------------------------------------------------------------

def win_path(p):
    return "Z:" + str(p).replace("/", "\\")


def compile_program(stage_mql5, staged_program, timeout=COMPILE_TIMEOUT):
    """Runs MetaEditor on one staged program; returns (log bytes or None, exclusion reason or None)."""
    program = Path(stage_mql5) / staged_program
    log = program.with_suffix(".log")
    if log.exists():
        log.unlink()
    env = dict(os.environ, WINEPREFIX=str(WINEPREFIX))
    cmd = [str(WINE), "MetaEditor64.exe", f"/compile:{win_path(program)}", f"/include:{win_path(stage_mql5)}", "/log"]
    try:
        subprocess.run(cmd, cwd=MT5_ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "timeout"
    deadline = time.time() + 15
    while time.time() < deadline and not log.exists():
        time.sleep(0.5)
    if not log.exists():
        return None, "no-log"
    return log.read_bytes(), None


def make_verdict(key, source, program_rel, build, log_bytes, reason, mapping, stage_mql5):
    v = {"key": key, "source": source["name"], "program": program_rel, "metaeditor_build": build,
         "status": "ok", "diagnostics": []}
    if reason is None:
        diags, result = parse_log(decode_log(log_bytes), path_mapper(stage_mql5, mapping))
        if result is None:
            reason = "crash"
        elif any(d["severity"] == "error" and d["code"] == 106 for d in diags):
            reason = "missing-include"  # error 106: can't open include file
        else:
            v["diagnostics"] = diags
    if reason is not None:
        v["status"], v["excluded_reason"] = "excluded", reason
    return v


# ---- referee loop (T008) ----------------------------------------------------------------------------

def referee(sources, stage_only=False, table_reader=read_process_table, compile_fn=compile_program, out=print):
    """Compiles every program without a fresh verdict. Stops cleanly (verdicts so far kept) as soon
    as MetaTrader is busy. Then, for each program whose verdict is clean, compiles its seeded
    mutants (FR-017); a mutant's verdict carries its kind, line and text, and it counts only if
    MetaEditor rejects it. Returns (compiled, reused, stopped_reason or None, untouched_diff)."""
    reason = busy_reason(table_reader(), own_pids=(os.getpid(),))
    if reason and not stage_only:
        out(f"not starting: {reason}")
        return 0, 0, reason, []
    build = metaeditor_build()
    before = snapshot(MQL5) if MQL5.exists() else {}
    compiled = reused = 0
    stopped = None
    current, mutants = [], []

    def finish():
        diff = snapshot_diff(before, snapshot(MQL5) if MQL5.exists() else {})
        if not stage_only:
            write_current(current, build, stopped is None, diff, mutants=mutants)
        return compiled, reused, stopped, diff

    def judge(stage_mql5, staged, key, source, program, mapping, extra=None):
        """Reuses or compiles one staged file; returns the verdict, or None when MetaTrader got busy."""
        nonlocal compiled, reused, stopped
        verdict = load_verdict(key)
        if verdict is not None:
            reused += 1
            return verdict
        why_busy = busy_reason(table_reader(), own_pids=(os.getpid(),))
        if why_busy:
            stopped = why_busy
            out(f"stopping before {program}: {why_busy}")
            return None
        log_bytes, why = compile_fn(stage_mql5, staged)
        why_busy = busy_reason(table_reader(), own_pids=(os.getpid(),))
        if why_busy:  # a backtest started mid-compile and may have killed MetaEditor: don't keep it
            stopped = why_busy
            out(f"discarding {program}: MetaTrader got busy during the compile ({why_busy})")
            return None
        verdict = make_verdict(key, source, program, build, log_bytes, why, mapping, stage_mql5)
        verdict.update(extra or {})
        save_verdict(verdict)
        compiled += 1
        return verdict

    if True:
        for source in sources:
            stage_mql5, mapping, programs, unsupported, stubs = stage_source(source)
            out(f"{source['name']}: {len(programs) - len(stubs)} programs and {len(stubs)} header stubs staged at {stage_mql5}"
                + (f", {len(unsupported)} unsupported (space in folder)" if unsupported else ""))
            if stage_only:
                continue
            headers = header_files(source)
            for rel in unsupported:
                key = verdict_key(b"", headers, build, source["name"] + ":" + rel)
                current.append({"source": source["name"], "program": rel, "key": key})
                save_verdict({"key": key, "source": source["name"], "program": rel, "metaeditor_build": build,
                              "status": "excluded", "excluded_reason": "unsupported-path", "diagnostics": []})
            clean = []
            for staged in programs:
                program = stubs.get(staged, mapping[staged])  # a stub is scored as its header
                program_bytes = (stage_mql5 / staged).read_bytes()
                key = verdict_key(program_bytes, headers, build, source["name"] + ":" + program)
                verdict = judge(stage_mql5, staged, key, source, program, mapping)
                if verdict is None:
                    return finish()
                current.append({"source": source["name"], "program": program, "key": key})
                if staged not in stubs and verdict["status"] == "ok" and not any(
                        d["severity"] == "error" for d in verdict["diagnostics"]):
                    clean.append((staged, program, program_bytes))
            for staged, program, program_bytes in clean:
                text = decode_log(program_bytes)
                for kind in mutate.KINDS:
                    for i, m in enumerate(mutate.mutate(text, kind, MUTATION_SEED, MUTANTS_PER_KIND)):
                        mutant_staged = str(Path(staged).with_name(f"{Path(staged).stem}__mutant_{kind}_{i}.mq5"))
                        data = b"\xef\xbb\xbf" + m.text.encode("utf-8")  # BOM: non-ASCII comments stay UTF-8
                        (stage_mql5 / mutant_staged).write_bytes(data)
                        mapping[mutant_staged] = program  # its errors belong on the program's lines
                        key = verdict_key(data, headers, build, f"{source['name']}:{program}#mutant:{kind}:{i}")
                        verdict = judge(stage_mql5, mutant_staged, key, source, program, mapping,
                                        {"mutant": {"kind": kind, "index": i, "line": m.line, "text": m.text}})
                        if verdict is None:
                            return finish()
                        mutants.append({"source": source["name"], "program": program, "kind": kind, "index": i, "key": key})
    return finish()


def write_current(entries, build, complete, untouched_diff, store=None, mutants=()):
    """The verdict index the plugin side reads (current.json beside the store): one key per program
    for this run and one per mutant, the MetaEditor build, whether the run finished, and the
    untouched check."""
    p = Path(store or STORE).parent / "current.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    data = {"metaeditor_build": build, "complete": complete, "metatrader_untouched": not untouched_diff,
            "programs": sorted(entries, key=lambda e: (e["source"], e["program"])),
            "mutants": sorted(mutants, key=lambda e: (e["source"], e["program"], e["kind"], e["index"]))}
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1, sort_keys=True))
    os.replace(tmp, p)


# ---- self-test --------------------------------------------------------------------------------------

def self_test():
    import tempfile
    failures = []

    def check(name, cond):
        if not cond:
            failures.append(name)

    # busy rule
    check("idle", busy_reason(["/bin/zsh", "/usr/sbin/cfprefsd agent"]) is None)
    check("plain terminal is not busy", busy_reason(
        [r"C:\Program Files\MetaTrader 5\terminal64.exe /portable"]) is None)
    check("tester agent", busy_reason([r"C:\Program Files\MetaTrader 5\metatester64.exe /local /address:127.0.0.1:3000"]) is not None)
    check("idle /run agent counts until T001", busy_reason([r"C:\Program Files\MetaTrader 5\metatester64.exe /run /address:0.0.0.0:2000"]) is not None)
    check("terminal tester run", busy_reason([r"C:\Program Files\MetaTrader 5\terminal64.exe /config:C:\t.ini /portable"]) is not None)
    check("backtest driver", busy_reason(["bash /Users/x/.local/bin/mt5 backtest --symbol EURUSD"]) is not None)
    check("another MetaEditor", busy_reason([r"C:\Program Files\MetaTrader 5\MetaEditor64.exe /compile:Z:\a.mq5"]) is not None)
    check("unreadable table", busy_reason(None) is not None)
    check("a grep for the name is not a tester", busy_reason(["grep metatester64"]) is None)

    # log parsing and path mapping (synthetic log in MetaEditor's format, UTF-16 with BOM)
    with tempfile.TemporaryDirectory() as td:
        stage = Path(td) / "src" / "MQL5"
        mapping = {"Experts/src/Experts/A.mq5": "Experts/A.mq5", "Include/Util.mqh": "Include/Util.mqh"}
        log = ("\ufeff" + f"{win_path(stage)}\\Experts\\src\\Experts\\A.mq5 : information: compiling A.mq5\r\n"
               + f"{win_path(stage)}\\Include\\Util.mqh(12,5) : error 256: 'x' - undeclared identifier\r\n"
               + "MQL5\\Experts\\src\\Experts\\A.mq5(40,1) : warning 43: possible loss of data\r\n"
               + f"{win_path(stage)}\\Include\\Trade\\Trade.mqh(3,1) : error 149: unexpected token\r\n"
               + "Result: 2 errors, 1 warnings, 100 msec elapsed\r\n").encode("utf-16")
        diags, result = parse_log(decode_log(log), path_mapper(stage, mapping))
        check("result line", result == (2, 1))
        check("three diagnostics", len(diags) == 3)
        check("header mapped", any(d["file"] == "Include/Util.mqh" and d["line"] == 12 and d["code"] == 256 for d in diags))
        check("relative path mapped", any(d["file"] == "Experts/A.mq5" and d["severity"] == "warning" for d in diags))
        check("stdlib labelled", any(d["file"] == "<stdlib>/Trade/Trade.mqh" for d in diags))
        check("no result -> crash", make_verdict("k" * 64, {"name": "s"}, "A.mq5", 1, b"", None, {}, stage)["excluded_reason"] == "crash")
        missing = ("\ufeffA.mq5(1,1) : error 106: can't open include file\r\nResult: 1 errors, 0 warnings\r\n").encode("utf-16")
        check("error 106 -> missing-include", make_verdict("k" * 64, {"name": "s"}, "A.mq5", 1, missing, None, {}, stage)["excluded_reason"] == "missing-include")

        # key: header edits and builds change it, header order doesn't
        k1 = verdict_key(b"p", [("a", b"1"), ("b", b"2")], 5430)
        check("key stable under order", k1 == verdict_key(b"p", [("b", b"2"), ("a", b"1")], 5430))
        check("header edit changes key", k1 != verdict_key(b"p", [("a", b"1"), ("b", b"3")], 5430))
        check("build changes key", k1 != verdict_key(b"p", [("a", b"1"), ("b", b"2")], 5431))
        check("location changes key", verdict_key(b"p", [], 1, "s:A.mq5") != verdict_key(b"p", [], 1, "s:B.mq5"))

        # store round trip
        store = Path(td) / "store"
        save_verdict({"key": k1, "x": 1}, store)
        check("store round trip", load_verdict(k1, store) == {"key": k1, "x": 1})

        # snapshot diff
        root = Path(td) / "mt"
        root.mkdir()
        (root / "a.mq5").write_text("1")
        before = snapshot(root)
        check("unchanged tree", snapshot_diff(before, snapshot(root)) == [])
        (root / "b.ex5").write_text("2")
        check("added file seen", snapshot_diff(before, snapshot(root)) == ["added b.ex5"])

        # lock: second holder refused while the owner lives, stale lock taken over
        lock = Path(td) / "lock"
        check("lock taken", acquire_lock(lock))
        lock.write_text("1")  # launchd: alive and never ours
        check("live owner refuses", not acquire_lock(lock))
        lock.write_text("999999")
        check("stale lock taken over", acquire_lock(lock))
        release_lock(lock)
        check("lock released", not lock.exists())

        # referee refuses to start, and stops mid-run, when MetaTrader becomes busy
        tester = [r"C:\Program Files\MetaTrader 5\metatester64.exe /local /address:127.0.0.1:3000"]
        msgs = []
        c, r, why, _ = referee([], table_reader=lambda: tester, out=msgs.append)
        check("refuses to start while busy", c == 0 and why is not None and "tester" in msgs[0])
        repo = Path(td) / "repo"
        (repo / "Experts").mkdir(parents=True)
        for n in ("A", "B"):
            (repo / "Experts" / f"{n}.mq5").write_text("void OnStart(){}\n")
        tables = iter([[], [], [], tester])  # start, before A, after A, before B
        calls = []
        global STAGE_ROOT, STORE
        saved = (STAGE_ROOT, STORE)
        STAGE_ROOT, STORE = Path(td) / "stage", Path(td) / "verdicts"
        try:
            src = {"name": "demo repo", "path": str(repo), "include_roots": [], "programs": "**/*.mq5"}
            c, r, why, _ = referee([src], table_reader=lambda: next(tables),
                                   compile_fn=lambda s, p: (calls.append(p), (b"\xff\xfeR\x00", None))[1], out=msgs.append)
            check("stops before the next compile", c == 1 and len(calls) == 1 and why is not None)
            check("verdicts so far are kept", len(list((Path(td) / "verdicts").glob("*.json"))) == 1)
            idx = json.loads((Path(td) / "current.json").read_text())
            check("index marks a partial run", idx["complete"] is False and len(idx["programs"]) == 1)
            check("staged names have no spaces", all(" " not in p for p in calls))
            tables = iter([[], [], tester])  # start, before A, busy right after A's compile
            calls.clear()
            c2, _, why2, _ = referee([dict(src, name="demo two")], table_reader=lambda: next(tables),
                                     compile_fn=lambda s, p: (calls.append(p), (b"\xff\xfeR\x00", None))[1], out=msgs.append)
            check("a compile that overlapped a backtest is discarded", c2 == 0 and len(calls) == 1 and why2 is not None)
            (repo / "Experts" / "My EA.mq5").write_text("x")
            (repo / "Spaced Dir").mkdir()
            (repo / "Spaced Dir" / "C.mq5").write_text("x")
            (repo / "Include").mkdir()
            (repo / "Include" / "My Utils.mqh").write_text("x")
            st, mp, progs, unsup, stubs = stage_source(dict(src, include_roots=["Include"]))
            check("spaced file name gets a space-free copy", "Experts/demo_repo/Experts/My_EA.mq5" in progs
                  and mp["Experts/demo_repo/Experts/My_EA.mq5"] == "Experts/My EA.mq5")
            check("spaced folder staged space-free", "Experts/demo_repo/Spaced_Dir/C.mq5" in progs and unsup == [])
            check("header names keep their spaces", (st / "Include" / "My Utils.mqh").exists())
            check("MQL5-layout folders mirrored at the stage root for #resource", (st / "Experts" / "My_EA.mq5").exists() is False
                  and (st / "Experts" / "My EA.mq5").exists() and mp.get("Experts/My EA.mq5") == "Experts/My EA.mq5")

            # header stubs (FR-018): only headers no program reaches, filed under the header's path
            (repo / "Experts" / "A.mq5").write_text('#include "Used.mqh"\nvoid OnStart(){}\n')
            (repo / "Experts" / "used.MQH").write_text('#include <Lib/Deep.mqh>\n')
            (repo / "Include" / "Lib").mkdir()
            (repo / "Include" / "Lib" / "Deep.mqh").write_text("int deep;\n")
            (repo / "Include" / "Lonely.mqh").write_text("int lonely;\n")
            st, mp, progs, unsup, stubs = stage_source(dict(src, include_roots=["Include"]))
            check("stubs only for unreached headers", sorted(stubs.values()) == ["Include/Lonely.mqh", "Include/My Utils.mqh"])
            stub = next(k for k, v in stubs.items() if v == "Include/Lonely.mqh")
            check("stub is a program in Scripts", stub in progs and stub.startswith("Scripts/demo_repo/"))
            check("stub includes the repo copy", '"..\\..\\Experts\\demo_repo\\Include\\Lonely.mqh"' in (st / stub).read_text())
            check("stub's own lines never map to the repo", mp[stub] == "<stub>/Include/Lonely.mqh")

            # key covers a header outside the roots; another program's edit doesn't touch it
            loose = dict(src, include_roots=[])
            k_before = verdict_key(b"p", header_files(loose), 1)
            (repo / "Experts" / "used.MQH").write_text("int changed;\n")
            check("loose header edit changes the key", k_before != verdict_key(b"p", header_files(loose), 1))
            k_before = verdict_key(b"p", header_files(loose), 1)
            (repo / "Experts" / "B.mq5").write_text("void OnStart(){ int b; }\n")
            check("another program's edit keeps the key", k_before == verdict_key(b"p", header_files(loose), 1))

            # mutants: only from clean programs, compiled after them, recorded with kind and line
            mrepo = Path(td) / "mrepo"
            (mrepo / "Experts").mkdir(parents=True)
            (mrepo / "Experts" / "Clean.mq5").write_text("int F(int a) { return a; }\nvoid OnStart()\n  {\n   int x = F(1);\n   x = F(x);\n  }\n")
            (mrepo / "Experts" / "Broken.mq5").write_text("void OnStart() { int x = F(1); }\n")
            clean_log = "\ufeffResult: 0 errors, 0 warnings\r\n".encode("utf-16")
            bad_log = "\ufeffBroken.mq5(1,26) : error 256: 'F' - undeclared identifier\r\nResult: 1 errors, 0 warnings\r\n".encode("utf-16")
            compiled_files = []

            def fake_compile(stage, staged):
                compiled_files.append(staged)
                return (bad_log if "Broken" in staged or "__mutant_" in staged else clean_log), None
            msrc = {"name": "m", "path": str(mrepo), "include_roots": [], "programs": "**/*.mq5"}
            c, r, why, _ = referee([msrc], table_reader=lambda: [], compile_fn=fake_compile, out=msgs.append)
            idx = json.loads((Path(td) / "current.json").read_text())
            check("finished run", why is None and idx["complete"] is True)
            check("mutants only from the clean program", idx["mutants"] and all(e["program"] == "Experts/Clean.mq5" for e in idx["mutants"]))
            check("mutants compiled after programs", compiled_files[:2] == sorted(compiled_files[:2]) and "__mutant_" not in "".join(compiled_files[:2]))
            mv = load_verdict(idx["mutants"][0]["key"])
            check("mutant verdict carries kind, line and text", mv["mutant"]["kind"] in mutate.KINDS
                  and mv["mutant"]["line"] >= 1 and mv["mutant"]["text"] != (mrepo / "Experts" / "Clean.mq5").read_text())
            n = len(compiled_files)
            c, r, why, _ = referee([msrc], table_reader=lambda: [], compile_fn=fake_compile, out=msgs.append)
            check("rerun compiles nothing", len(compiled_files) == n and c == 0 and r == n)

            # one build per score (FR-020): a MetaEditor update recompiles everything first
            global metaeditor_build
            real_build = metaeditor_build
            metaeditor_build = lambda exe=None: 999999
            try:
                c, r, why, _ = referee([msrc], table_reader=lambda: [], compile_fn=fake_compile, out=msgs.append)
            finally:
                metaeditor_build = real_build
            idx = json.loads((Path(td) / "current.json").read_text())
            check("build change recompiles every verdict", c == n and r == 0)
            check("index carries the new build only", idx["metaeditor_build"] == 999999 and all(
                load_verdict(e["key"])["metaeditor_build"] == 999999 for e in idx["programs"] + idx["mutants"]))
        finally:
            STAGE_ROOT, STORE = saved

    if failures:
        print("FAILED: " + ", ".join(failures))
        return 1
    print("self-test passed")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--corpus", default=str(Path(__file__).with_name("corpus.json")))
    ap.add_argument("--source", action="append", help="only these sources (repeatable)")
    ap.add_argument("--stage-only", action="store_true", help="stage, don't compile")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    sources = json.loads(Path(args.corpus).read_text())["sources"]
    sources = [s for s in sources if s["role"] != "report" or "path" in s]
    if args.source:
        sources = [s for s in sources if s["name"] in args.source]
    if not acquire_lock():
        print(f"another harness run holds {LOCK}")
        return 6
    try:
        compiled, reused, stopped, diff = referee(sources, stage_only=args.stage_only)
    finally:
        release_lock()
    print(f"compiled {compiled}, reused {reused}" + (f", stopped: {stopped}" if stopped else ""))
    if diff:
        print("!! MetaTrader's MQL5 folder changed during the run:\n  " + "\n  ".join(diff[:50]))
        return 7
    print("MetaTrader's MQL5 folder: untouched")
    return 5 if stopped else 0


if __name__ == "__main__":
    sys.exit(main())
