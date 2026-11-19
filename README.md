# Snooping Cache Simulator

A simulator for a bus-based shared-memory multiprocessor. It runs a sequence of
reads, writes, and replacements for one to three processors. Each has its own
cache; all share a bus and main memory. One variable equals one cache block.

## Requirements and usage

Python 3.7 or later; no third-party packages are needed.

```sh
python simulator.py examples/benchmark1_wb.txt
```

With no file argument, the simulator reads standard input. For example, in
PowerShell:

```powershell
Get-Content examples/benchmark1_wb.txt | python simulator.py
```

The output contains an aligned trace starting at step zero, followed by final
memory and cache values and transaction counts. Example file suffixes are
`wt` (write-through), `wb` (write-back), and `wo` (Write-Once).

## Input format

```text
# Example: one write to a cold cache
PROTOCOL: WRITE_INVALIDATE_WRITE_THROUGH
MEMORY: X=5, Y=10, Z=20
PROCESSORS: P1, P2, P3
P2: Write(X, 10)
```

Provide the three headers in this order, followed by zero or more operations:
`P1: Read(X)`, `P1: Write(X, -10)`, or `P1: Replace(X)`. Declare one to three
unique processors and variables. Identifiers are case-sensitive, start with an
ASCII letter or underscore, and may also contain digits after the first
character. Values are signed decimal integers. Blank lines and full-line `#`
comments are ignored. Invalid input is reported on standard error.

## Protocols

| Input name | States | Behavior |
| --- | --- | --- |
| `WRITE_INVALIDATE_WRITE_THROUGH` | `VALID`, `INV` | Every write updates memory and invalidates other copies. |
| `WRITE_INVALIDATE_WRITE_BACK` | `RO`, `RW`, `INV` | Shared copies are read-only. An `RW` owner can write locally and flushes on transfer or replacement. |
| `WRITE_ONCE` | `VALID`, `RES`, `DIRTY`, `INV` | A write hit on `VALID` invalidates other copies and writes through, becoming `RES`. A later local write in `RES` or `DIRTY` stays local and leaves the block `DIRTY`. |

## Modeling choices

- All protocols allocate on a write miss. If another cache holds `RW` or
  `DIRTY`, it flushes its **old** value to memory before invalidation; the
  requester's new value stays local. This yields memory `X=15` after Benchmark
  1 step 6 in write-back and Write-Once. The flush is in `SharedBus.broadcast_read`.
- A Write-Once write miss ends in `DIRTY` (including on a cold cache), as
  specified by the assignment. A peer read changes `RES` to `VALID` without a
  write-back, since memory already holds that value; this follows Goodman's
  original *Using Cache Memory to Reduce Processor-Memory Traffic*, section 3.2
  (ISCA 1983, DOI: `10.1145/800046.801647`). Benchmark 2 exercises that downgrade
  at step 6. A local read hit leaves the state unchanged in all protocols.
- An invalidated copy retains its old value for display but cannot satisfy a
  read or write hit. `Replace` removes the entry entirely, including `INV`
  entries, and does nothing if it is absent. Only `RW` or `DIRTY` replacements
  write back. There are no automatic evictions or final flushes; final memory
  may therefore be stale relative to an owning cache.

## Statistics

- Hits and misses are counted once per processor read or write, before the
  operation changes any cache state. Replacements do not count as accesses.
- Bus invalidations count commands, not the number of copies invalidated.
  A command counts even if no peer holds the block or there are no peers.
- Write-backs count actual memory updates from dirty-owner flushes and
  replacements. Write-through updates are counted separately. Initial memory
  values do not count as writes.

## Tests

```sh
python -m unittest discover -v
```

The suite checks both benchmarks under all three protocols, parsing errors,
replacement behavior, invalid copies, trace alignment, and summary counts.
