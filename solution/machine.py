"""Reference stack VM with mark-sweep GC."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any

HEAP_CAP = 256
MAX_CALL = 64
MAX_STACK = 4096


class Trap(Exception):
    pass


@dataclass
class Obj:
    slots: list[Any]
    marked: bool = False
    free: bool = False


@dataclass
class Frame:
    return_ip: int
    # no locals beyond stack for this ISA


@dataclass
class Machine:
    stack: list[Any] = field(default_factory=list)
    heap: list[Obj | None] = field(default_factory=lambda: [None] * HEAP_CAP)
    free_list: list[int] = field(default_factory=lambda: list(range(HEAP_CAP)))
    frames: list[Frame] = field(default_factory=list)
    code: list[tuple] = field(default_factory=list)
    labels: dict[str, int] = field(default_factory=dict)
    ip: int = 0

    def load(self, path: str) -> None:
        raw: list[str] = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.split("#", 1)[0].strip()
                if line:
                    raw.append(line)
        # First pass labels
        ops: list[str] = []
        for line in raw:
            if line.endswith(":") and " " not in line.strip():
                name = line[:-1]
                self.labels[name] = len(ops)
            else:
                ops.append(line)
        self.code = []
        for line in ops:
            parts = line.split()
            op = parts[0].upper()
            if op in {"PUSH", "ALLOC", "SET", "GET"}:
                self.code.append((op, int(parts[1])))
            elif op in {"CALL", "JMP", "JZ"}:
                self.code.append((op, parts[1]))
            else:
                self.code.append((op,))

    def _push(self, v: Any) -> None:
        if len(self.stack) >= MAX_STACK:
            raise Trap("stack overflow")
        self.stack.append(v)

    def _pop(self) -> Any:
        if not self.stack:
            raise Trap("stack underflow")
        return self.stack.pop()

    def _as_int(self, v: Any) -> int:
        if type(v) is not int:
            # heap refs are tagged tuples ("R", idx)
            raise Trap("expected int")
        return v

    def gc(self) -> None:
        for o in self.heap:
            if o is not None:
                o.marked = False

        def mark(v: Any) -> None:
            if isinstance(v, tuple) and len(v) == 2 and v[0] == "R":
                idx = v[1]
                obj = self.heap[idx]
                if obj is None or obj.marked:
                    return
                obj.marked = True
                for slot in obj.slots:
                    mark(slot)

        for v in self.stack:
            mark(v)
        # frames hold only return ips; values live on stack
        for i, obj in enumerate(self.heap):
            if obj is not None and not obj.marked:
                self.heap[i] = None
                self.free_list.append(i)
        self.free_list.sort()

    def alloc(self, n: int) -> tuple:
        if n < 0 or n > 16:
            raise Trap("bad alloc size")
        if not self.free_list:
            self.gc()
        if not self.free_list:
            raise Trap("OOM")
        idx = self.free_list.pop(0)
        self.heap[idx] = Obj(slots=[0] * n)
        return ("R", idx)

    def execute(self) -> None:
        while self.ip < len(self.code):
            inst = self.code[self.ip]
            self.ip += 1
            op = inst[0]
            if op == "PUSH":
                self._push(inst[1])
            elif op == "ADD":
                b, a = self._pop(), self._pop()
                self._push(self._as_int(a) + self._as_int(b))
            elif op == "SUB":
                b, a = self._pop(), self._pop()
                self._push(self._as_int(a) - self._as_int(b))
            elif op == "MUL":
                b, a = self._pop(), self._pop()
                self._push(self._as_int(a) * self._as_int(b))
            elif op == "PRINT":
                v = self._pop()
                if isinstance(v, tuple):
                    raise Trap("print ref")
                print(int(v))
            elif op == "ALLOC":
                self._push(self.alloc(inst[1]))
            elif op == "SET":
                val = self._pop()
                ref = self._pop()
                if not (isinstance(ref, tuple) and ref[0] == "R"):
                    raise Trap("set needs ref")
                obj = self.heap[ref[1]]
                if obj is None:
                    raise Trap("dangling")
                i = inst[1]
                if i < 0 or i >= len(obj.slots):
                    raise Trap("slot")
                obj.slots[i] = val
            elif op == "GET":
                ref = self._pop()
                if not (isinstance(ref, tuple) and ref[0] == "R"):
                    raise Trap("get needs ref")
                obj = self.heap[ref[1]]
                if obj is None:
                    raise Trap("dangling")
                i = inst[1]
                if i < 0 or i >= len(obj.slots):
                    raise Trap("slot")
                self._push(obj.slots[i])
            elif op == "DUP":
                if not self.stack:
                    raise Trap("stack underflow")
                self._push(self.stack[-1])
            elif op == "DROP":
                self._pop()
            elif op == "SWAP":
                b, a = self._pop(), self._pop()
                self._push(b)
                self._push(a)
            elif op == "CALL":
                if len(self.frames) >= MAX_CALL:
                    raise Trap("call overflow")
                if inst[1] not in self.labels:
                    raise Trap("bad label")
                self.frames.append(Frame(return_ip=self.ip))
                self.ip = self.labels[inst[1]]
            elif op == "RET":
                if not self.frames:
                    raise Trap("ret")
                fr = self.frames.pop()
                self.ip = fr.return_ip
            elif op == "JMP":
                if inst[1] not in self.labels:
                    raise Trap("bad label")
                self.ip = self.labels[inst[1]]
            elif op == "JZ":
                v = self._pop()
                if self._as_int(v) == 0:
                    if inst[1] not in self.labels:
                        raise Trap("bad label")
                    self.ip = self.labels[inst[1]]
            elif op == "HALT":
                return
            else:
                raise Trap(f"bad opcode {op}")
        raise Trap("fell off end")


def run_file(path: str) -> None:
    m = Machine()
    m.load(path)
    try:
        m.execute()
    except Trap as e:
        print(f"TRAP: {e}", file=sys.stderr)
        raise SystemExit(1) from e
