#!/bin/bash
#SBATCH -J q8020_sweep
#SBATCH -A ard189
#SBATCH -t 02:00:00
#SBATCH -N 1
#SBATCH -C nvme
#SBATCH -p batch
#SBATCH -o /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/slurm_%j.out
#SBATCH -e /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/slurm_%j.err

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

srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_0/trial_0_133dfbc6/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_0/trial_1_a03c43df/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_0/trial_2_8617462e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_0/trial_3_035453cb/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_0/trial_4_76f36469/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_0/trial_5_78f01894/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_0/trial_6_b23d1049/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_0/trial_7_4af4c1c8/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_0/trial_8_827f1e00/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_0/trial_9_0eec983a/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_1/trial_0_2f6ee45b/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_1/trial_1_1231aca2/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_1/trial_2_c6dcab34/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_1/trial_3_f96d1986/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_1/trial_4_39459cbd/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_1/trial_5_f5d87115/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_1/trial_6_0029402c/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_1/trial_7_df5c4c82/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_1/trial_8_f70a2102/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_1/trial_9_0fefc74f/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_2/trial_0_f9a75f61/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_2/trial_1_43d41462/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_2/trial_2_488814d0/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_2/trial_3_5f19fe6b/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_2/trial_4_d9f31a79/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_2/trial_5_5cbcdebb/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_2/trial_6_12410b12/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_2/trial_7_8a4d88d5/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_2/trial_8_a259dc2f/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_2/trial_9_f266dbb9/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_3/trial_0_1cb35e4e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_3/trial_1_5b2104f8/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_3/trial_2_5e30c4a2/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_3/trial_3_556d4171/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_3/trial_4_4e8133ee/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_3/trial_5_20cda62b/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_3/trial_6_7f6b326a/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_3/trial_7_e5f93d3d/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_3/trial_8_516d435e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_3/trial_9_c3f8e15c/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_4/trial_0_bb19679d/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_4/trial_1_27376b23/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_4/trial_2_be5cb375/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_4/trial_3_d0b442f5/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_4/trial_4_6ba0b57a/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_4/trial_5_662ae6b3/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_4/trial_6_3c538cd6/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_4/trial_7_5b644f05/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_4/trial_8_1619b5e9/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/hhl_time_steps_with_trials_after_timeout_fix/2026-03-30/_045fe5db/time_steps_4/trial_9_1eb208fa/pipeline_args.json &

# Wait for all background srun tasks
wait

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "All cases finished."
echo "Wall time: $((ELAPSED / 60))m $((ELAPSED % 60))s"
