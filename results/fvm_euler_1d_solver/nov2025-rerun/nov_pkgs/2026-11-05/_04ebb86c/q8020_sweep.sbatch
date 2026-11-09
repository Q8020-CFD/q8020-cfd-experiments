#!/bin/bash
#SBATCH -J q8020_sweep
#SBATCH -A ard189
#SBATCH -t 02:00:00
#SBATCH -N 2
#SBATCH -C nvme
#SBATCH -p batch
#SBATCH -o /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/slurm_%j.out
#SBATCH -e /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/slurm_%j.err

echo "Job ID: $SLURM_JOB_ID"
echo "Nodes:  $SLURM_JOB_NUM_NODES"
echo "Cases:  71"
echo "Start:  $(date)"
echo ""

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

cd $SLURM_SUBMIT_DIR || exit 1

# --- Broadcast packed venvs to NVMe ---
echo 'Broadcasting lustre_orion_ard189_scratch_ishangore_q8020_fvm_euler_1d_solver-main_.venv.tar.gz...'
sbcast -pf /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/lustre_orion_ard189_scratch_ishangore_q8020_fvm_euler_1d_solver-main_.venv.tar.gz /mnt/bb/${USER}/venv_0.tar.gz
if [ "$?" != "0" ]; then echo "ERROR: sbcast lustre_orion_ard189_scratch_ishangore_q8020_fvm_euler_1d_solver-main_.venv.tar.gz failed"; exit 1; fi
srun -N ${SLURM_NNODES} --ntasks-per-node 1 mkdir -p /mnt/bb/${USER}/venv_0
srun -N ${SLURM_NNODES} --ntasks-per-node 1 tar -xzf /mnt/bb/${USER}/venv_0.tar.gz -C /mnt/bb/${USER}/venv_0
srun -N ${SLURM_NNODES} --ntasks-per-node 1 sed -i "s|VIRTUAL_ENV=.*|VIRTUAL_ENV=\"/mnt/bb/${USER}/venv_0\"|" /mnt/bb/${USER}/venv_0/bin/activate
echo "Environments ready"

# --- Launch all cases in parallel ---
echo "Launching 71 cases..."
START_TIME=$(date +%s)

srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/a02c3bc1/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_0/trial_0_6a95e185/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_0/trial_1_a6299448/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_0/trial_2_78f26700/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_0/trial_3_b8c7c6c1/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_0/trial_4_78487f5c/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_0/trial_5_262e544a/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_0/trial_6_209801d7/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_0/trial_7_5ff0232a/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_0/trial_8_36e91f72/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_0/trial_9_e41bf582/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_1/trial_0_b97d7390/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_1/trial_1_8bfe753a/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_1/trial_2_09851016/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_1/trial_3_a25f82ef/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_1/trial_4_7012fd62/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_1/trial_5_70b36736/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_1/trial_6_d008db40/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_1/trial_7_08c95bd7/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_1/trial_8_9fac9fc9/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_1/trial_9_ea29c230/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_2/trial_0_f8161638/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_2/trial_1_6a1bb308/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_2/trial_2_919f2b3e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_2/trial_3_86287a62/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_2/trial_4_25ae1b09/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_2/trial_5_486d1bd7/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_2/trial_6_15e08865/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_2/trial_7_39372bec/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_2/trial_8_083c7376/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_2/trial_9_7389c436/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_3/trial_0_4af8e7ad/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_3/trial_1_2067cc00/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_3/trial_2_852b8003/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_3/trial_3_db84894b/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_3/trial_4_0e83fed1/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_3/trial_5_a377d354/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_3/trial_6_959b3fcc/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_3/trial_7_605a22bf/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_3/trial_8_24ddd34c/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_3/trial_9_17cf7c1d/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_4/trial_0_77349d44/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_4/trial_1_ebe8fef0/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_4/trial_2_d8313683/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_4/trial_3_8d1047da/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_4/trial_4_f93fdb05/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_4/trial_5_518df366/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_4/trial_6_e0f13d8b/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_4/trial_7_1f293b96/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_4/trial_8_1532777f/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_4/trial_9_5b7838f3/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_5/trial_0_38757620/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_5/trial_1_02b6a7e6/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_5/trial_2_1c3b8eda/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_5/trial_3_73863a1a/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_5/trial_4_a6ea7ba9/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_5/trial_5_a90cc6fc/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_5/trial_6_b1415f47/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_5/trial_7_850d8aa3/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_5/trial_8_2c02905e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_5/trial_9_0b201946/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_6/trial_0_7e877118/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_6/trial_1_0abb410f/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_6/trial_2_07629744/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_6/trial_3_6a923414/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_6/trial_4_b1391914/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_6/trial_5_da7db70d/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_6/trial_6_cf7ab449/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_6/trial_7_7a4023be/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_6/trial_8_771a06c9/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-05/_04ebb86c/shots_6/trial_9_37954e19/pipeline_args.json &

# Wait for all background srun tasks
wait

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "All cases finished."
echo "Wall time: $((ELAPSED / 60))m $((ELAPSED % 60))s"
