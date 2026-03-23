#!/bin/bash
#SBATCH -J q8020_sweep
#SBATCH -A ard189
#SBATCH -t 04:00:00
#SBATCH -N 1
#SBATCH -C nvme
#SBATCH -p batch
#SBATCH -o /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/slurm_%j.out
#SBATCH -e /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/slurm_%j.err

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

srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_0/trial_0_73a0c8ed/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_0/trial_1_65c3fc76/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_0/trial_2_f046942d/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_0/trial_3_a21c2f5d/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_0/trial_4_be68c663/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_0/trial_5_d875b2a0/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_0/trial_6_0c546af9/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_0/trial_7_d5a27584/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_0/trial_8_d1b91fdb/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_0/trial_9_187ff08d/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_1/trial_0_c8f36599/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_1/trial_1_8034d4c2/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_1/trial_2_7909af57/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_1/trial_3_07feaa44/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_1/trial_4_a7ee4419/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_1/trial_5_9eda8a52/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_1/trial_6_40842194/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_1/trial_7_43da1e86/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_1/trial_8_bebdadac/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_1/trial_9_49859766/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_2/trial_0_52882146/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_2/trial_1_48e7daca/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_2/trial_2_308bb002/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_2/trial_3_43330809/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_2/trial_4_931c9f71/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_2/trial_5_232b3c32/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_2/trial_6_8c3efcfb/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_2/trial_7_28fe1b66/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_2/trial_8_4ab6d584/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_2/trial_9_b30cee56/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_3/trial_0_ef5c7c8f/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_3/trial_1_5c95359e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_3/trial_2_491840fa/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_3/trial_3_69d1f171/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_3/trial_4_6e00f48b/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_3/trial_5_fc2504c0/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_3/trial_6_c8fa1c08/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_3/trial_7_97312708/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_3/trial_8_c18ac3c5/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_3/trial_9_2497675e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_4/trial_0_dcc0ffd6/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_4/trial_1_86b16cd0/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_4/trial_2_d35a66f4/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_4/trial_3_a0744b9c/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_4/trial_4_cacf7e03/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_4/trial_5_2d0f58e4/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_4/trial_6_495f6f2e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_4/trial_7_844ac851/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_4/trial_8_0d545ded/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/hhl_time_steps_with_trials_4_hr/2026-03-23/_c37f6f42/time_steps_4/trial_9_d80d8bd8/pipeline_args.json &

# Wait for all background srun tasks
wait

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "All cases finished."
echo "Wall time: $((ELAPSED / 60))m $((ELAPSED % 60))s"
