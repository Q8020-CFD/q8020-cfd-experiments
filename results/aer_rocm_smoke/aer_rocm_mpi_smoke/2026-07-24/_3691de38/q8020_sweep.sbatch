#!/bin/bash
#SBATCH -J q8020_sweep
#SBATCH -A ard189
#SBATCH -t 00:30:00
#SBATCH -N 4
#SBATCH -C nvme
#SBATCH -p batch
#SBATCH -o /ccs/home/ishangore/aer_rocm_mpi_smoke/2026-07-24/_3691de38/slurm_%j.out
#SBATCH -e /ccs/home/ishangore/aer_rocm_mpi_smoke/2026-07-24/_3691de38/slurm_%j.err

echo "Job ID: $SLURM_JOB_ID"
echo "Nodes:  $SLURM_JOB_NUM_NODES"
echo "Cases:  2"
echo "Start:  $(date)"
echo ""

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

cd $SLURM_SUBMIT_DIR || exit 1


# --- Launch all cases in parallel ---
echo "Launching 2 cases..."
START_TIME=$(date +%s)

python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/aer_rocm_mpi_smoke/2026-07-24/_3691de38/29c85dac/pipeline_args.json &
python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/aer_rocm_mpi_smoke/2026-07-24/_3691de38/2fa3db7e/pipeline_args.json &

# Wait for all background srun tasks
wait

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "All cases finished."
echo "Wall time: $((ELAPSED / 60))m $((ELAPSED % 60))s"
