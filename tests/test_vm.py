#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
import tempfile

APP = os.environ.get("APP_DIR", "/app")
HIDDEN = "/tests/programs"


def run_prog(path: str) -> tuple[int, str, str]:
    p = subprocess.run(
        [sys.executable, "-m", "vm.run", path],
        cwd=APP,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": APP},
    )
    return p.returncode, p.stdout, p.stderr


def expect(path: str, stdout: str, code: int = 0) -> None:
    rc, out, err = run_prog(path)
    if rc != code:
        raise AssertionError(f"{path}: rc={rc} stderr={err!r}")
    if out != stdout:
        raise AssertionError(f"{path}: stdout {out!r} != {stdout!r}")
    print(f"PASS {path}")


def main() -> int:
    expect(os.path.join(APP, "programs/arith.svm"), "14\n")
    expect(os.path.join(APP, "programs/heap_basic.svm"), "10\n20\n")
    expect(os.path.join(HIDDEN, "calls.svm"), "25\n")
    expect(os.path.join(HIDDEN, "gc_pressure.svm"), "42\n")

    # Invalid mix should trap
    with tempfile.NamedTemporaryFile("w", suffix=".svm", delete=False) as fh:
        fh.write("ALLOC 1\nPRINT\nHALT\n")
        bad = fh.name
    rc, _, err = run_prog(bad)
    if rc != 1 or "TRAP:" not in err:
        raise AssertionError(f"expected trap on print ref, got rc={rc} err={err!r}")
    print("PASS trap_print_ref")
    print("ALL_PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1) from exc
