#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs results work
exec > >(tee logs/prepare.log) 2>&1
hostname
whoami
sinfo
squeue -u "$USER"
if type module >/dev/null 2>&1; then
  module list 2>&1 || true
  module avail > logs/modules.txt 2>&1 || true
fi
for tool in gcc mpicc mpirun python3; do
  if ! command -v "$tool"; then
    echo "MISSING: $tool. Load the cluster's compiler/MPI/Python modules and rerun bash scripts/cluster_prepare.sh"
    exit 2
  fi
done
python3 -c 'import numpy, scipy, mpi4py, matplotlib' || {
  echo 'Missing Python dependencies. Use a compatible cluster Python environment with numpy scipy mpi4py matplotlib; see README.md.'
  exit 2
}
make -j3
python3 scripts/generate.py work/benchmark.txt --n 1000000
echo 'Build ready. Request a compute allocation and run tests/correctness.sh; see README.md.'
