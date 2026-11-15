import sys
import numpy as np
from mpi4py import MPI
from spline_math import system, reduce_rows, coefficients
comm = MPI.COMM_WORLD
rank, size = (comm.rank, comm.size)
data = np.loadtxt(sys.argv[1], skiprows=1, ndmin=2)
x, y = data.T
n = len(x)
if n < 2 or not np.isfinite(data).all() or (not (np.diff(x) > 0).all()):
    raise ValueError('Nodes must be finite and strictly increasing')
repeats = int(sys.argv[4]) if len(sys.argv) > 4 else 1
edges = np.arange(size + 1, dtype=np.int64) * n // size
lo, hi = edges[rank:rank + 2]
counts, offsets = (np.diff(edges) * 4, edges[:-1] * 4)
best = float('inf')
for _ in range(repeats):
    old = system(x, y)
    new = np.empty_like(old)
    comm.Barrier()
    start = MPI.Wtime()
    stride = 1
    while stride < n:
        local = reduce_rows(old, lo, hi, stride)
        comm.Allgatherv(local, [new, counts, offsets, MPI.DOUBLE])
        old, new = (new, old)
        stride *= 2
    m = np.empty(n)
    local_m = np.ascontiguousarray(old[lo:hi, 3] / old[lo:hi, 1])
    comm.Allgatherv(local_m, [m, np.diff(edges), edges[:-1], MPI.DOUBLE])
    end = min(hi, n - 1)
    begin = min(lo, n - 1)
    local_c = coefficients(x, y, m, begin, end)
    c = np.empty((n - 1, 4))
    ce = np.minimum(edges, n - 1)
    comm.Allgatherv(local_c, [c, np.diff(ce) * 4, ce[:-1] * 4, MPI.DOUBLE])
    elapsed = comm.allreduce(MPI.Wtime() - start, op=MPI.MAX)
    best = min(best, elapsed)
if rank == 0:
    np.savetxt(sys.argv[3], c, fmt='%.17g')
    print(f'python_mpi,{n},{size},{best:.9g}')
