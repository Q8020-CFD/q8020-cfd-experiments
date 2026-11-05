#!/bin/bash
#SBATCH -J q8020_sweep
#SBATCH -A ard189
#SBATCH -t 08:00:00
#SBATCH -N 2
#SBATCH -C nvme
#SBATCH -p extended
#SBATCH -o /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/slurm_%j.out
#SBATCH -e /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/slurm_%j.err

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
sbcast -pf /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/lustre_orion_ard189_scratch_ishangore_q8020_fvm_euler_1d_solver-main_.venv.tar.gz /mnt/bb/${USER}/venv_0.tar.gz
if [ "$?" != "0" ]; then echo "ERROR: sbcast lustre_orion_ard189_scratch_ishangore_q8020_fvm_euler_1d_solver-main_.venv.tar.gz failed"; exit 1; fi
srun -N ${SLURM_NNODES} --ntasks-per-node 1 mkdir -p /mnt/bb/${USER}/venv_0
srun -N ${SLURM_NNODES} --ntasks-per-node 1 tar -xzf /mnt/bb/${USER}/venv_0.tar.gz -C /mnt/bb/${USER}/venv_0
srun -N ${SLURM_NNODES} --ntasks-per-node 1 sed -i "s|VIRTUAL_ENV=.*|VIRTUAL_ENV=\"/mnt/bb/${USER}/venv_0\"|" /mnt/bb/${USER}/venv_0/bin/activate
echo "Environments ready"

# --- Launch all cases in parallel ---
echo "Launching 71 cases..."
START_TIME=$(date +%s)

srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/c5419763/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_0/trial_0_6dfcaa09/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_0/trial_1_c43d5e27/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_0/trial_2_cd6cc88d/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_0/trial_3_0066bc09/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_0/trial_4_5f9b0d17/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_0/trial_5_afa5748a/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_0/trial_6_e44c1704/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_0/trial_7_732dcdd5/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_0/trial_8_7c5a6923/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_0/trial_9_ee967671/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_1/trial_0_0ee23d9a/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_1/trial_1_1dc5647f/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_1/trial_2_1b6f663d/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_1/trial_3_2eeb77b0/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_1/trial_4_047008c1/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_1/trial_5_606239a6/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_1/trial_6_6fe7534b/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_1/trial_7_d3068ecb/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_1/trial_8_4ce7855c/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_1/trial_9_2dafac1d/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_2/trial_0_522b4784/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_2/trial_1_7f870390/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_2/trial_2_9186e622/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_2/trial_3_b89cc4e8/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_2/trial_4_ee49bba4/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_2/trial_5_43aa7237/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_2/trial_6_41d966aa/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_2/trial_7_a549c42c/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_2/trial_8_7363ed04/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_2/trial_9_c879090e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_3/trial_0_64557dfd/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_3/trial_1_774cec19/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_3/trial_2_149dc460/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_3/trial_3_c497ae94/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_3/trial_4_157dd6b3/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_3/trial_5_1a829b5a/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_3/trial_6_563bac0d/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_3/trial_7_2b5b9c3b/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_3/trial_8_c611b04f/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_3/trial_9_cf4eebca/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_4/trial_0_a0da932e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_4/trial_1_40e3ff5c/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_4/trial_2_9029f74e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_4/trial_3_0caf8b6d/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_4/trial_4_523ef9b6/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_4/trial_5_521d9b60/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_4/trial_6_745fcda6/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_4/trial_7_245d079c/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_4/trial_8_15b40d99/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_4/trial_9_4dd3df27/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_5/trial_0_fc04676c/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_5/trial_1_bdbe8756/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_5/trial_2_42f08cf0/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_5/trial_3_2069001d/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_5/trial_4_0420dd8b/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_5/trial_5_0b0955aa/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_5/trial_6_c46f89b6/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_5/trial_7_71c54a3f/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_5/trial_8_0895e55d/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_5/trial_9_a2357bf4/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_6/trial_0_d2b5226a/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_6/trial_1_dbc146dc/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_6/trial_2_3fd79c4a/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_6/trial_3_13d41409/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_6/trial_4_6bd1e610/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_6/trial_5_7e508eed/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_6/trial_6_e61ca1bb/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_6/trial_7_839ed8aa/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_6/trial_8_e0f16890/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/nov_pkgs/2026-11-04/_01fda1e3/shots_6/trial_9_a1d7e7a4/pipeline_args.json &

# Wait for all background srun tasks
wait

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "All cases finished."
echo "Wall time: $((ELAPSED / 60))m $((ELAPSED % 60))s"
