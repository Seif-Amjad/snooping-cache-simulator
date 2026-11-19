# Snooping Cache Simulator Verification

Full simulator traces and final statistics for both benchmarks under all three protocols.

## Benchmark 1

### Write-Through

```text
=======================================================================================
Serial | Event                 | Mem(X) | P Val(X) | P State(X) | Q Val(X) | Q State(X)
=======================================================================================
0      | Initial State         | 5      | -        | -          | -        | -
1      | P reads X (Read-Miss) | 5      | 5        | VALID      | -        | -
2      | Q reads X (Read-Miss) | 5      | 5        | VALID      | 5        | VALID
3      | Q updates X (W-Hit)   | 10     | 5        | INV        | 10       | VALID
4      | Q reads X (Read-Hit)  | 10     | 5        | INV        | 10       | VALID
5      | Q updates X (W-Hit)   | 15     | 5        | INV        | 15       | VALID
6      | P writes X (W-Miss)   | 20     | 20       | VALID      | 15       | INV
7      | Q reads X (Read-Miss) | 20     | 20       | VALID      | 20       | VALID
=======================================================================================

Final Summary
Memory: X=20
P: X=20 (VALID)
Q: X=20 (VALID)
Read-Hits: 1
Read-Misses: 3
Write-Hits: 2
Write-Misses: 1
Bus invalidation commands: 3
Memory write-backs: 0
Memory write-throughs: 3
```

### Write-Back Ownership

```text
=======================================================================================
Serial | Event                 | Mem(X) | P Val(X) | P State(X) | Q Val(X) | Q State(X)
=======================================================================================
0      | Initial State         | 5      | -        | -          | -        | -
1      | P reads X (Read-Miss) | 5      | 5        | RO         | -        | -
2      | Q reads X (Read-Miss) | 5      | 5        | RO         | 5        | RO
3      | Q updates X (W-Hit)   | 5      | 5        | INV        | 10       | RW
4      | Q reads X (Read-Hit)  | 5      | 5        | INV        | 10       | RW
5      | Q updates X (W-Hit)   | 5      | 5        | INV        | 15       | RW
6      | P writes X (W-Miss)   | 15     | 20       | RW         | 15       | INV
7      | Q reads X (Read-Miss) | 20     | 20       | RO         | 20       | RO
=======================================================================================

Final Summary
Memory: X=20
P: X=20 (RO)
Q: X=20 (RO)
Read-Hits: 1
Read-Misses: 3
Write-Hits: 2
Write-Misses: 1
Bus invalidation commands: 2
Memory write-backs: 2
Memory write-throughs: 0
```

### Write-Once

```text
=======================================================================================
Serial | Event                 | Mem(X) | P Val(X) | P State(X) | Q Val(X) | Q State(X)
=======================================================================================
0      | Initial State         | 5      | -        | -          | -        | -
1      | P reads X (Read-Miss) | 5      | 5        | VALID      | -        | -
2      | Q reads X (Read-Miss) | 5      | 5        | VALID      | 5        | VALID
3      | Q updates X (W-Hit)   | 10     | 5        | INV        | 10       | RES
4      | Q reads X (Read-Hit)  | 10     | 5        | INV        | 10       | RES
5      | Q updates X (W-Hit)   | 10     | 5        | INV        | 15       | DIRTY
6      | P writes X (W-Miss)   | 15     | 20       | DIRTY      | 15       | INV
7      | Q reads X (Read-Miss) | 20     | 20       | VALID      | 20       | VALID
=======================================================================================

Final Summary
Memory: X=20
P: X=20 (VALID)
Q: X=20 (VALID)
Read-Hits: 1
Read-Misses: 3
Write-Hits: 2
Write-Misses: 1
Bus invalidation commands: 2
Memory write-backs: 2
Memory write-throughs: 1
```

## Benchmark 2

### Write-Through

```text
=============================================================================================================================================================================================================
Serial | Event                  | Mem(X) | Mem(Z) | P1 Val(X) | P1 State(X) | P1 Val(Z) | P1 State(Z) | P2 Val(X) | P2 State(X) | P2 Val(Z) | P2 State(Z) | P3 Val(X) | P3 State(X) | P3 Val(Z) | P3 State(Z)
=============================================================================================================================================================================================================
0      | Initial State          | 10     | 80     | -         | -           | -         | -           | -         | -           | -         | -           | -         | -           | -         | -
1      | P1 reads X (Read-Miss) | 10     | 80     | 10        | VALID       | -         | -           | -         | -           | -         | -           | -         | -           | -         | -
2      | P2 reads X (Read-Miss) | 10     | 80     | 10        | VALID       | -         | -           | 10        | VALID       | -         | -           | -         | -           | -         | -
3      | P3 reads X (Read-Miss) | 10     | 80     | 10        | VALID       | -         | -           | 10        | VALID       | -         | -           | 10        | VALID       | -         | -
4      | P1 updates X (W-Hit)   | 35     | 80     | 35        | VALID       | -         | -           | 10        | INV         | -         | -           | 10        | INV         | -         | -
5      | P1 reads Z (Read-Miss) | 35     | 80     | 35        | VALID       | 80        | VALID       | 10        | INV         | -         | -           | 10        | INV         | -         | -
6      | P2 reads X (Read-Miss) | 35     | 80     | 35        | VALID       | 80        | VALID       | 35        | VALID       | -         | -           | 10        | INV         | -         | -
7      | P3 writes X (W-Miss)   | 15     | 80     | 35        | INV         | 80        | VALID       | 35        | INV         | -         | -           | 15        | VALID       | -         | -
8      | P1 updates Z (W-Hit)   | 15     | 81     | 35        | INV         | 81        | VALID       | 35        | INV         | -         | -           | 15        | VALID       | -         | -
=============================================================================================================================================================================================================

Final Summary
Memory: X=15, Z=81
P1: X=35 (INV), Z=81 (VALID)
P2: X=35 (INV), Z=- (-)
P3: X=15 (VALID), Z=- (-)
Read-Hits: 0
Read-Misses: 5
Write-Hits: 2
Write-Misses: 1
Bus invalidation commands: 3
Memory write-backs: 0
Memory write-throughs: 3
```

### Write-Back Ownership

```text
=============================================================================================================================================================================================================
Serial | Event                  | Mem(X) | Mem(Z) | P1 Val(X) | P1 State(X) | P1 Val(Z) | P1 State(Z) | P2 Val(X) | P2 State(X) | P2 Val(Z) | P2 State(Z) | P3 Val(X) | P3 State(X) | P3 Val(Z) | P3 State(Z)
=============================================================================================================================================================================================================
0      | Initial State          | 10     | 80     | -         | -           | -         | -           | -         | -           | -         | -           | -         | -           | -         | -
1      | P1 reads X (Read-Miss) | 10     | 80     | 10        | RO          | -         | -           | -         | -           | -         | -           | -         | -           | -         | -
2      | P2 reads X (Read-Miss) | 10     | 80     | 10        | RO          | -         | -           | 10        | RO          | -         | -           | -         | -           | -         | -
3      | P3 reads X (Read-Miss) | 10     | 80     | 10        | RO          | -         | -           | 10        | RO          | -         | -           | 10        | RO          | -         | -
4      | P1 updates X (W-Hit)   | 10     | 80     | 35        | RW          | -         | -           | 10        | INV         | -         | -           | 10        | INV         | -         | -
5      | P1 reads Z (Read-Miss) | 10     | 80     | 35        | RW          | 80        | RO          | 10        | INV         | -         | -           | 10        | INV         | -         | -
6      | P2 reads X (Read-Miss) | 35     | 80     | 35        | RO          | 80        | RO          | 35        | RO          | -         | -           | 10        | INV         | -         | -
7      | P3 writes X (W-Miss)   | 35     | 80     | 35        | INV         | 80        | RO          | 35        | INV         | -         | -           | 15        | RW          | -         | -
8      | P1 updates Z (W-Hit)   | 35     | 80     | 35        | INV         | 81        | RW          | 35        | INV         | -         | -           | 15        | RW          | -         | -
=============================================================================================================================================================================================================

Final Summary
Memory: X=35, Z=80
P1: X=35 (INV), Z=81 (RW)
P2: X=35 (INV), Z=- (-)
P3: X=15 (RW), Z=- (-)
Read-Hits: 0
Read-Misses: 5
Write-Hits: 2
Write-Misses: 1
Bus invalidation commands: 3
Memory write-backs: 1
Memory write-throughs: 0
```

### Write-Once

```text
=============================================================================================================================================================================================================
Serial | Event                  | Mem(X) | Mem(Z) | P1 Val(X) | P1 State(X) | P1 Val(Z) | P1 State(Z) | P2 Val(X) | P2 State(X) | P2 Val(Z) | P2 State(Z) | P3 Val(X) | P3 State(X) | P3 Val(Z) | P3 State(Z)
=============================================================================================================================================================================================================
0      | Initial State          | 10     | 80     | -         | -           | -         | -           | -         | -           | -         | -           | -         | -           | -         | -
1      | P1 reads X (Read-Miss) | 10     | 80     | 10        | VALID       | -         | -           | -         | -           | -         | -           | -         | -           | -         | -
2      | P2 reads X (Read-Miss) | 10     | 80     | 10        | VALID       | -         | -           | 10        | VALID       | -         | -           | -         | -           | -         | -
3      | P3 reads X (Read-Miss) | 10     | 80     | 10        | VALID       | -         | -           | 10        | VALID       | -         | -           | 10        | VALID       | -         | -
4      | P1 updates X (W-Hit)   | 35     | 80     | 35        | RES         | -         | -           | 10        | INV         | -         | -           | 10        | INV         | -         | -
5      | P1 reads Z (Read-Miss) | 35     | 80     | 35        | RES         | 80        | VALID       | 10        | INV         | -         | -           | 10        | INV         | -         | -
6      | P2 reads X (Read-Miss) | 35     | 80     | 35        | VALID       | 80        | VALID       | 35        | VALID       | -         | -           | 10        | INV         | -         | -
7      | P3 writes X (W-Miss)   | 35     | 80     | 35        | INV         | 80        | VALID       | 35        | INV         | -         | -           | 15        | DIRTY       | -         | -
8      | P1 updates Z (W-Hit)   | 35     | 81     | 35        | INV         | 81        | RES         | 35        | INV         | -         | -           | 15        | DIRTY       | -         | -
=============================================================================================================================================================================================================

Final Summary
Memory: X=35, Z=81
P1: X=35 (INV), Z=81 (RES)
P2: X=35 (INV), Z=- (-)
P3: X=15 (DIRTY), Z=- (-)
Read-Hits: 0
Read-Misses: 5
Write-Hits: 2
Write-Misses: 1
Bus invalidation commands: 3
Memory write-backs: 0
Memory write-throughs: 2
```
