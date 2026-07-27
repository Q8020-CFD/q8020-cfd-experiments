#!/bin/bash
#SBATCH -J q8020_sweep
#SBATCH -A ard189
#SBATCH -t 00:30:00
#SBATCH -N 8
#SBATCH -C nvme
#SBATCH -p batch
#SBATCH -o /ccs/home/ishangore/q8020_aer_rocm_smoke/2026-07-27/_d5961e91/slurm_%j.out
#SBATCH -e /ccs/home/ishangore/q8020_aer_rocm_smoke/2026-07-27/_d5961e91/slurm_%j.err

echo "Job ID: $SLURM_JOB_ID"
echo "Nodes:  $SLURM_JOB_NUM_NODES"
echo "Cases:  8"
echo "Start:  $(date)"
echo ""

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

cd $SLURM_SUBMIT_DIR || exit 1


# --- Launch all cases in parallel ---
echo "Launching 8 cases..."
START_TIME=$(date +%s)

srun -N 1 -n 1 -c 56 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/q8020_aer_rocm_smoke/2026-07-27/_d5961e91/74182a47/pipeline_args.json &
srun -N 1 -n 1 -c 56 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/q8020_aer_rocm_smoke/2026-07-27/_d5961e91/270acf7e/pipeline_args.json &
srun -N 1 -n 1 -c 56 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/q8020_aer_rocm_smoke/2026-07-27/_d5961e91/60d64eae/pipeline_args.json &
srun -N 1 -n 1 -c 56 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/q8020_aer_rocm_smoke/2026-07-27/_d5961e91/d0515755/pipeline_args.json &
srun -N 1 -n 1 -c 56 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/q8020_aer_rocm_smoke/2026-07-27/_d5961e91/7d9c3408/pipeline_args.json &
srun -N 1 -n 1 -c 56 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/q8020_aer_rocm_smoke/2026-07-27/_d5961e91/b756f000/pipeline_args.json &
srun -N 1 -n 1 -c 56 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/q8020_aer_rocm_smoke/2026-07-27/_d5961e91/8a7b6d7f/pipeline_args.json &
srun -N 1 -n 1 -c 56 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/q8020_aer_rocm_smoke/2026-07-27/_d5961e91/be819afd/pipeline_args.json &

# Wait for all background srun tasks
wait

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "All cases finished."
echo "Wall time: $((ELAPSED / 60))m $((ELAPSED % 60))s"
