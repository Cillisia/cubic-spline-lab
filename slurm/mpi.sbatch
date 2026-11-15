#!/usr/bin/env bash
#SBATCH --nodes=4
#SBATCH --ntasks=112
#SBATCH --ntasks-per-node=28
#SBATCH --partition=tornado
#SBATCH --time=01:00:00
#SBATCH --output=logs/mpi-%j.out
#SBATCH --error=logs/mpi-%j.err
set -euo pipefail
module load compiler/gcc/11 mpi/openmpi/4.1.6/gcc/11 python/3.10
source "$HOME/spline-lab/.venv/bin/activate"
export OMPI_MCA_pml=ob1
export OMPI_MCA_btl=self,vader,tcp
cd "$SLURM_SUBMIT_DIR"
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=1
for n in 10000 100000 1000000; do
  python3 scripts/generate.py work/mpi-$SLURM_JOB_ID.txt --n "$n"
  for p in 1 2 4 8 16 28 56 84 112; do
    mpirun -np "$p" --bind-to core ./bin/spline_mpi work/mpi-$SLURM_JOB_ID.txt "$p" work/mpi-out-$SLURM_JOB_ID.txt 5
    mpirun -np "$p" --bind-to core python3 src/spline_mpi.py work/mpi-$SLURM_JOB_ID.txt "$p" work/mpi-out-$SLURM_JOB_ID.txt 5
  done
done
