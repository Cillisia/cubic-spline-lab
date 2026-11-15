#!/usr/bin/env bash
set -euo pipefail
mkdir -p work results
for spec in 'two 2' 'constant 17' 'linear 33' 'sin 128' 'uneven 129'; do
  read -r kind n <<< "$spec"
  python3 scripts/generate.py work/test.txt --case "$kind" --n "$n"
  for p in 1 2 4; do
    for impl in pthreads openmp; do
      ./bin/spline_$impl work/test.txt "$p" work/out.txt
      python3 scripts/check.py work/test.txt work/out.txt
    done
    mpirun -np "$p" ./bin/spline_mpi work/test.txt "$p" work/out.txt
    python3 scripts/check.py work/test.txt work/out.txt
    mpirun -np "$p" python3 src/spline_mpi.py work/test.txt "$p" work/out.txt
    python3 scripts/check.py work/test.txt work/out.txt
  done
done
echo 'ALL FOUR IMPLEMENTATIONS PASSED'
