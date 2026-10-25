# Stack VM with Mark-Sweep GC

Implement a small stack machine with a mark-sweep garbage collector under `/app`.

The instruction set, public programs, and a failing stub live in the workspace. Your binary entrypoint must be:

```bash
python -m vm.run /path/to/program.svm
```

It should execute the program and print the machine’s stdout exactly as specified by the ISA. On success exit with code 0. On trap (stack overflow, invalid opcode, out of memory after GC) print a single line starting with `TRAP:` to stderr and exit with code 1.

## Instruction set (summary)

Programs are text files with one instruction per line. Comments start with `#`. Supported ops:

- `PUSH <int>` — push a 32-bit signed integer
- `ADD` / `SUB` / `MUL` — pop two ints, push result
- `PRINT` — pop one value and print it as decimal followed by newline
- `ALLOC <n>` — allocate a heap object with `n` integer slots (0..16), push a heap reference
- `SET <i>` — pop value, pop ref, store value into slot `i` of the object
- `GET <i>` — pop ref, push slot `i`
- `DUP` / `DROP` / `SWAP` — stack helpers
- `CALL <label>` / `RET` — call stack with return addresses (max depth 64)
- `JMP <label>` / `JZ <label>` — control flow; `JZ` pops and jumps if zero
- `HALT` — stop successfully
- Labels: `NAME:`

Heap references are distinct from integers. Mixing them incorrectly is a `TRAP`.

## GC requirements

The heap has a fixed capacity of **256 objects**. When `ALLOC` cannot find a free slot, run a mark-sweep GC from the operand stack and call frames (any stored heap refs in object slots are also roots transitively). If still full, trap with `TRAP: OOM`.

A correct GC must reclaim unreachable objects so that allocation-heavy programs in `/app/programs/` complete.

## Local check

```bash
cd /app
python -m vm.run programs/arith.svm
python -m vm.run programs/heap_basic.svm
```

Work offline and autonomously. Keep the `vm` package import path stable.
