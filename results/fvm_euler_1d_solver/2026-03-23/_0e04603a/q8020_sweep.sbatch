#!/bin/bash
#SBATCH -J q8020_sweep
#SBATCH -A ard189
#SBATCH -t 02:00:00
#SBATCH -N 1
#SBATCH -C nvme
#SBATCH -p batch
#SBATCH -o /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/slurm_%j.out
#SBATCH -e /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/slurm_%j.err

echo "Job ID: $SLURM_JOB_ID"
echo "Nodes:  $SLURM_JOB_NUM_NODES"
echo "Cases:  50"
echo "Start:  $(date)"
echo ""

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

cd $SLURM_SUBMIT_DIR || exit 1

# No _slurm_conda_archive specified -- using default environment

# --- Launch all cases in parallel ---
echo "Launching 50 cases..."
START_TIME=$(date +%s)

srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_0/trial_0_ae6a2dd4/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_0/trial_1_72a9bd4c/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_0/trial_2_0a46deb9/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_0/trial_3_113ca106/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_0/trial_4_7d37e1a4/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_0/trial_5_b624dee0/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_0/trial_6_7b32cdc2/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_0/trial_7_d4ae0f27/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_0/trial_8_001f9749/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_0/trial_9_6f26a42e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_1/trial_0_27d3aeeb/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_1/trial_1_5e3c9068/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_1/trial_2_eee9bebe/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_1/trial_3_4256a67e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_1/trial_4_25520fff/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_1/trial_5_f95df3c6/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_1/trial_6_d3458644/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_1/trial_7_8c76a604/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_1/trial_8_16af355d/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_1/trial_9_a1834c34/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_2/trial_0_fd5d673d/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_2/trial_1_3de90231/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_2/trial_2_26ca4c17/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_2/trial_3_92e89f94/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_2/trial_4_3a313ca0/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_2/trial_5_e659fb74/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_2/trial_6_9b4ed704/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_2/trial_7_4029b861/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_2/trial_8_c4d41b5d/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_2/trial_9_7f0bb46a/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_3/trial_0_d9b351bd/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_3/trial_1_c0d87010/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_3/trial_2_0fd901a0/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_3/trial_3_f06dcc7c/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_3/trial_4_3f878563/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_3/trial_5_b123c9e9/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_3/trial_6_bdea61ed/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_3/trial_7_d582d8c2/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_3/trial_8_66b62896/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_3/trial_9_271aad8b/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_4/trial_0_0cb99b4b/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_4/trial_1_34d35f69/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_4/trial_2_2855ef08/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_4/trial_3_62ecffac/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_4/trial_4_5239c60c/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_4/trial_5_974834fd/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_4/trial_6_7b569404/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_4/trial_7_a9fe0b5c/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_4/trial_8_3499b59a/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials/2026-03-23/_0e04603a/time_steps_4/trial_9_dcacbb69/pipeline_args.json &

# Wait for all background srun tasks
wait

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "All cases finished."
echo "Wall time: $((ELAPSED / 60))m $((ELAPSED % 60))s"
