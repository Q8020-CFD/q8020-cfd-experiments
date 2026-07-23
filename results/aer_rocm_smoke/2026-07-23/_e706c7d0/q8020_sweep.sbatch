#!/bin/bash
#SBATCH -J q8020_sweep
#SBATCH -A ard189
#SBATCH -t 00:20:00
#SBATCH -N 1
#SBATCH -C nvme
#SBATCH -p batch
#SBATCH -o /ccs/home/ishangore/q8020_aer_rocm_smoke/2026-07-23/_e706c7d0/slurm_%j.out
#SBATCH -e /ccs/home/ishangore/q8020_aer_rocm_smoke/2026-07-23/_e706c7d0/slurm_%j.err

echo "Job ID: $SLURM_JOB_ID"
echo "Nodes:  $SLURM_JOB_NUM_NODES"
echo "Cases:  3"
echo "Start:  $(date)"
echo ""

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

cd $SLURM_SUBMIT_DIR || exit 1


# --- Launch all cases in parallel ---
echo "Launching 3 cases..."
START_TIME=$(date +%s)

srun -n 1 -c 7 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/q8020_aer_rocm_smoke/2026-07-23/_e706c7d0/488a58d1/pipeline_args.json &
srun -n 1 -c 7 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/q8020_aer_rocm_smoke/2026-07-23/_e706c7d0/11725b1f/pipeline_args.json &
srun -n 1 -c 7 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/q8020_aer_rocm_smoke/2026-07-23/_e706c7d0/59ef821f/pipeline_args.json &

# Wait for all background srun tasks
wait

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "All cases finished."
echo "Wall time: $((ELAPSED / 60))m $((ELAPSED % 60))s"
