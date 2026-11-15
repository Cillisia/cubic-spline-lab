#!/usr/bin/env bash
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=48
#SBATCH --partition=cascade
#SBATCH --time=00:30:00
#SBATCH --output=logs/threads-%j.out
#SBATCH --error=logs/threads-%j.err
set -euo pipefail
module load compiler/gcc/11 mpi/openmpi/4.1.6/gcc/11 python/3.10
source "$HOME/spline-lab/.venv/bin/activate"
cd "$SLURM_SUBMIT_DIR"
export OMP_PROC_BIND=true OMP_PLACES=cores
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
for n in 10000 100000 1000000; do
  python3 scripts/generate.py work/threads-$SLURM_JOB_ID.txt --n "$n"
  for p in 1 2 4 8 12 16 24 32 48; do
    for impl in pthreads openmp; do
      srun -n1 -c "$p" --cpu-bind=cores ./bin/spline_$impl work/threads-$SLURM_JOB_ID.txt "$p" work/threads-out-$SLURM_JOB_ID.txt 5
    done
  done
done
