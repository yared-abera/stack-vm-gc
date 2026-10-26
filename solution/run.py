"""CLI entry used by the oracle."""

from __future__ import annotations

import sys

from vm.machine import Machine, Trap


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print("usage: python -m vm.run <program.svm>", file=sys.stderr)
        return 2
    m = Machine()
    try:
        m.load(args[0])
        m.execute()
        return 0
    except Trap as exc:
        print(f"TRAP: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
