"""Results store: bench/results/<run_id>/records.jsonl and meta.json (stdlib only, Python 3.9+)."""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
from typing import Any, Dict, Iterator, List, Optional

from .schema import validate_record

_RUN_ID_OK = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")


def default_run_id() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def check_run_id(run_id: str) -> str:
    if not run_id or run_id.startswith(".") or any(c not in _RUN_ID_OK for c in run_id):
        raise ValueError("run id may only use letters, digits, . _ - (and must not start with '.'): %r" % run_id)
    return run_id


class RunStore:
    """One run directory. `append` validates every record against the schema before writing."""

    def __init__(self, out_dir: str, run_id: str, overwrite: bool = False, resume: bool = False):
        self.run_id = check_run_id(run_id)
        self._lock = threading.Lock()
        self.dir = os.path.join(out_dir, run_id)
        self.records_path = os.path.join(self.dir, "records.jsonl")
        self.meta_path = os.path.join(self.dir, "meta.json")
        if os.path.exists(self.records_path) and not overwrite and not resume:
            raise FileExistsError("%s already exists (use another --run-id, --force, or --resume)"
                                  % self.records_path)
        os.makedirs(self.dir, exist_ok=True)
        if resume and os.path.exists(self.records_path):
            repair_records(self.records_path)
        else:
            with open(self.records_path, "w", encoding="utf-8", newline="\n"):
                pass

    def append(self, record: Dict[str, Any]) -> None:
        errs = validate_record(record)
        if errs:
            raise ValueError("invalid record: " + "; ".join(errs))
        line = json.dumps(record, ensure_ascii=False, sort_keys=False) + "\n"
        with self._lock:
            with open(self.records_path, "a", encoding="utf-8", newline="\n") as f:
                f.write(line)
                f.flush()

    def write_meta(self, meta: Dict[str, Any]) -> None:
        with open(self.meta_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
            f.write("\n")


def repair_records(path: str) -> None:
    """Make a records file safe to append to after a kill: a last line that is not a complete JSON
    object (a write cut short) is dropped, and a missing final newline is added. Complete lines are
    never touched. A broken line that is not the last one is an error (nothing is guessed)."""
    with open(path, "rb") as f:
        data = f.read()
    if not data:
        return
    lines = data.split(b"\n")
    tail = lines[-1]            # b"" when the file ends with a newline
    body = lines[:-1]
    for n, raw in enumerate(body, 1):
        if raw.strip():
            try:
                json.loads(raw.decode("utf-8"))
            except ValueError:
                raise ValueError("%s line %d is not valid JSON; repair or remove it by hand" % (path, n))
    keep = b"".join(x + b"\n" for x in body)
    if tail.strip():
        try:
            json.loads(tail.decode("utf-8"))
            keep += tail + b"\n"
        except ValueError:
            pass            # cut-off last write: that run is redone
    if keep != data:
        with open(path, "wb") as f:
            f.write(keep)


def read_records(path: str) -> Iterator[Dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def source_hashes(project_root: str) -> Dict[str, Any]:
    """sha256 of zehn.py and of every .py under zehnlib/ (if that folder exists)."""
    out: Dict[str, Any] = {"zehn.py": None, "zehnlib": {}}
    zp = os.path.join(project_root, "zehn.py")
    if os.path.exists(zp):
        out["zehn.py"] = sha256_file(zp)
    lib = os.path.join(project_root, "zehnlib")
    if os.path.isdir(lib):
        for base, dirs, files in os.walk(lib):
            dirs[:] = sorted(d for d in dirs if d != "__pycache__")
            for fn in sorted(files):
                if fn.endswith(".py"):
                    p = os.path.join(base, fn)
                    out["zehnlib"][os.path.relpath(p, project_root).replace(os.sep, "/")] = sha256_file(p)
    return out


def tool_version(cmd: List[str]) -> Optional[str]:
    """First line of `<tool> --version`, or None if it cannot run."""
    try:
        p = subprocess.run(cmd + ["--version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           universal_newlines=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    text = (p.stdout or "").strip()
    return text.splitlines()[0] if text else None


def build_meta(argv: List[str], project_root: str, models: List[str], adapters: List[Any],
               extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Run metadata. `argv` is the CLI argument list; there is no option that carries a key, and the
    environment is never copied, so the API key cannot end up here."""
    tools: Dict[str, Optional[str]] = {}
    for ad in adapters:
        for name in getattr(ad, "external_tools", []):
            if name not in tools:
                resolve = getattr(ad, "tool_command", None)
                cmd = resolve(name) if resolve else shutil.which(name)
                tools[name] = tool_version(cmd if isinstance(cmd, list) else [cmd]) if cmd else None
    meta: Dict[str, Any] = {
        "date_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "argv": list(argv),
        "python": sys.version.split()[0],
        "sources": source_hashes(project_root),
        "tools": tools,
        "models": list(models),
        "langs": [ad.name for ad in adapters],
    }
    if extra:
        meta.update(extra)
    return meta
