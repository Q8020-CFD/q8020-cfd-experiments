#!/bin/bash
#SBATCH -J q8020_sweep
#SBATCH -A ard189
#SBATCH -t 02:00:00
#SBATCH -N 1
#SBATCH -C nvme
#SBATCH -p batch
#SBATCH -o /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_base/2026-03-26/_6a887db4/slurm_%j.out
#SBATCH -e /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_base/2026-03-26/_6a887db4/slurm_%j.err

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

srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_base/2026-03-26/_6a887db4/time_steps/trial_0_547b90d6/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_base/2026-03-26/_6a887db4/time_steps/trial_1_ab0c2727/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_base/2026-03-26/_6a887db4/time_steps/trial_2_e40d72fb/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_base/2026-03-26/_6a887db4/time_steps/trial_3_b96e732c/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_base/2026-03-26/_6a887db4/time_steps/trial_4_2b97cee0/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_base/2026-03-26/_6a887db4/time_steps/trial_5_7b055445/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_base/2026-03-26/_6a887db4/time_steps/trial_6_a0718aa7/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_base/2026-03-26/_6a887db4/time_steps/trial_7_8aab0f22/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_base/2026-03-26/_6a887db4/time_steps/trial_8_f6dec5d8/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_base/2026-03-26/_6a887db4/time_steps/trial_9_eefb5a62/pipeline_args.json &

# Wait for all background srun tasks
wait

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "All cases finished."
echo "Wall time: $((ELAPSED / 60))m $((ELAPSED % 60))s"
