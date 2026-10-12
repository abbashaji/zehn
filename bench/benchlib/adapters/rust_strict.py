"""Rust under strict tooling (the H5 competitor): `cargo build`, then `cargo clippy -- -D warnings`,
then `cargo fmt --check`. A formatting diff is a failing diagnostic (code "fmt"). Stdlib only, Python 3.9+.

`tool_check` reports the strict verdict. `run_hidden` is inherited unchanged: it builds and runs the
hidden tests, so it measures behaviour; whether the program is clippy- and rustfmt-clean is what the
last `tool_check` says.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Tuple

from . import rust as _rust


class RustStrictAdapter(_rust.RustAdapter):
    name = "rust_strict"
    ext = ".rs"
    needs = ("cargo", "rustc", "cargo-clippy", "cargo-fmt", "rustfmt")

    def _tool_note(self) -> str:
        return ("The feedback tool runs `cargo build`, then `cargo clippy -- -D warnings` (every warning is an "
                "error), then `cargo fmt --check` with default rustfmt settings: code that rustfmt would change "
                "is rejected, so write the code exactly as rustfmt formats it.")

    def _fmt(self, crate: str, nuser: int) -> Tuple[bool, List[Dict[str, Any]]]:
        rc, out, err, timed_out = _rust._run(["cargo", "fmt", "--check", "--", "--color", "never"], crate,
                                             _rust._cargo_env(), self.build_timeout)
        if rc == 0 and not timed_out:
            return True, []
        diags = _rust.parse_fmt_diff(out, nuser)
        if not diags:
            first = next((x for x in err.splitlines() if x.strip()), "cargo fmt --check failed (exit %d)" % rc)
            diags.append(_rust._diag("cargo", first.strip(), None, (err or out)[-4000:]))
        return False, diags

    def tool_check(self, task: Dict[str, Any], code: str, workdir: str) -> Dict[str, Any]:
        t0 = time.monotonic()
        crate, nuser = self._prepare(task, code, None, workdir)
        ok, diags = self._build(crate, nuser)
        if ok:
            clippy_ok, clippy_diags = self._cargo(
                crate, ["clippy", "--quiet", "--offline", "--message-format=json", "--", "-D", "warnings"], nuser)
            fmt_ok, fmt_diags = self._fmt(crate, nuser)
            ok = clippy_ok and fmt_ok
            diags = clippy_diags + fmt_diags
        return {"ok": ok, "diagnostics": diags, "tool_ms": _rust._ms(t0)}
