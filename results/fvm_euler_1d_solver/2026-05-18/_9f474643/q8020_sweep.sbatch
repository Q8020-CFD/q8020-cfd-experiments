#!/bin/bash
#SBATCH -J q8020_sweep
#SBATCH -A ard189
#SBATCH -t 02:00:00
#SBATCH -N 1
#SBATCH -C nvme
#SBATCH -p batch
#SBATCH -o /ccs/home/ishangore/bloqade_stack_smoke_test/2026-05-18/_9f474643/slurm_%j.out
#SBATCH -e /ccs/home/ishangore/bloqade_stack_smoke_test/2026-05-18/_9f474643/slurm_%j.err

echo "Job ID: $SLURM_JOB_ID"
echo "Nodes:  $SLURM_JOB_NUM_NODES"
echo "Cases:  1"
echo "Start:  $(date)"
echo ""

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

cd $SLURM_SUBMIT_DIR || exit 1

# No _slurm_conda_archive specified -- using default environment

# --- Launch all cases in parallel ---
echo "Launching 1 cases..."
START_TIME=$(date +%s)

srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/bloqade_stack_smoke_test/2026-05-18/_9f474643/c6482caf/pipeline_args.json &

# Wait for all background srun tasks
wait

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "All cases finished."
echo "Wall time: $((ELAPSED / 60))m $((ELAPSED % 60))s"
