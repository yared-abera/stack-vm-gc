"""Incomplete VM stub — replace with a working interpreter + GC."""

from __future__ import annotations


class Machine:
    def load(self, path: str) -> None:
        self.path = path

    def execute(self) -> None:
        raise RuntimeError("not implemented")
