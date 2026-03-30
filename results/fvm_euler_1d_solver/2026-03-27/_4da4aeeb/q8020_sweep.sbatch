#!/bin/bash
#SBATCH -J q8020_sweep
#SBATCH -A ard189
#SBATCH -t 02:00:00
#SBATCH -N 1
#SBATCH -C nvme
#SBATCH -p batch
#SBATCH -o /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_base/2026-03-27/_4da4aeeb/slurm_%j.out
#SBATCH -e /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_base/2026-03-27/_4da4aeeb/slurm_%j.err

echo "Job ID: $SLURM_JOB_ID"
echo "Nodes:  $SLURM_JOB_NUM_NODES"
echo "Cases:  10"
echo "Start:  $(date)"
echo ""

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

cd $SLURM_SUBMIT_DIR || exit 1

# No _slurm_conda_archive specified -- using default environment

# --- Launch all cases in parallel ---
echo "Launching 10 cases..."
START_TIME=$(date +%s)

srun -n 1 -c 32 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_base/2026-03-27/_4da4aeeb/time_steps/trial_0_1af80a02/pipeline_args.json &
srun -n 1 -c 32 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_base/2026-03-27/_4da4aeeb/time_steps/trial_1_332a495e/pipeline_args.json &
srun -n 1 -c 32 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_base/2026-03-27/_4da4aeeb/time_steps/trial_2_354b6403/pipeline_args.json &
srun -n 1 -c 32 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_base/2026-03-27/_4da4aeeb/time_steps/trial_3_aa0d9a4f/pipeline_args.json &
srun -n 1 -c 32 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_base/2026-03-27/_4da4aeeb/time_steps/trial_4_283c3033/pipeline_args.json &
srun -n 1 -c 32 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_base/2026-03-27/_4da4aeeb/time_steps/trial_5_83ceeb45/pipeline_args.json &
srun -n 1 -c 32 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_base/2026-03-27/_4da4aeeb/time_steps/trial_6_e56687fd/pipeline_args.json &
srun -n 1 -c 32 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_base/2026-03-27/_4da4aeeb/time_steps/trial_7_e8aa3442/pipeline_args.json &
srun -n 1 -c 32 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_base/2026-03-27/_4da4aeeb/time_steps/trial_8_7ca990fa/pipeline_args.json &
srun -n 1 -c 32 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_base/2026-03-27/_4da4aeeb/time_steps/trial_9_552d7b4a/pipeline_args.json &

# Wait for all background srun tasks
wait

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "All cases finished."
echo "Wall time: $((ELAPSED / 60))m $((ELAPSED % 60))s"
