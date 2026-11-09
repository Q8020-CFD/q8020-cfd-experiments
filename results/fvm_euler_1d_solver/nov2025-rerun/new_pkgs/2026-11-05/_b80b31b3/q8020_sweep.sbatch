#!/bin/bash
#SBATCH -J q8020_sweep
#SBATCH -A ard189
#SBATCH -t 08:00:00
#SBATCH -N 2
#SBATCH -C nvme
#SBATCH -p extended
#SBATCH -o /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/slurm_%j.out
#SBATCH -e /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/slurm_%j.err

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
echo 'Broadcasting lustre_orion_ard189_scratch_ishangore_q8020_fvm_euler_1d_solver-main-newpkgs_.venv.tar.gz...'
sbcast -pf /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/lustre_orion_ard189_scratch_ishangore_q8020_fvm_euler_1d_solver-main-newpkgs_.venv.tar.gz /mnt/bb/${USER}/venv_0.tar.gz
if [ "$?" != "0" ]; then echo "ERROR: sbcast lustre_orion_ard189_scratch_ishangore_q8020_fvm_euler_1d_solver-main-newpkgs_.venv.tar.gz failed"; exit 1; fi
srun -N ${SLURM_NNODES} --ntasks-per-node 1 mkdir -p /mnt/bb/${USER}/venv_0
srun -N ${SLURM_NNODES} --ntasks-per-node 1 tar -xzf /mnt/bb/${USER}/venv_0.tar.gz -C /mnt/bb/${USER}/venv_0
srun -N ${SLURM_NNODES} --ntasks-per-node 1 sed -i "s|VIRTUAL_ENV=.*|VIRTUAL_ENV=\"/mnt/bb/${USER}/venv_0\"|" /mnt/bb/${USER}/venv_0/bin/activate
echo "Environments ready"

# --- Launch all cases in parallel ---
echo "Launching 71 cases..."
START_TIME=$(date +%s)

srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/9f41c20d/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_0/trial_0_2444e384/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_0/trial_1_388ea269/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_0/trial_2_82c3e677/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_0/trial_3_249f0fde/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_0/trial_4_c36a50f1/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_0/trial_5_46c01926/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_0/trial_6_fdfb5fd1/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_0/trial_7_52767907/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_0/trial_8_649a8efa/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_0/trial_9_ba0a01b4/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_1/trial_0_dec3a272/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_1/trial_1_f82c0270/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_1/trial_2_a931e08f/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_1/trial_3_2d8a236d/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_1/trial_4_40e82fe7/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_1/trial_5_158c7100/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_1/trial_6_1e6b0740/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_1/trial_7_d3ca8b2f/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_1/trial_8_a5a2d430/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_1/trial_9_b32b6606/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_2/trial_0_fa2d259d/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_2/trial_1_d73f1e36/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_2/trial_2_d3181fc6/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_2/trial_3_ff3e0cb5/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_2/trial_4_892a44c6/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_2/trial_5_b50c1fee/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_2/trial_6_e78f3a83/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_2/trial_7_93fbde0e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_2/trial_8_1038c6b5/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_2/trial_9_4797e043/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_3/trial_0_13e3d668/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_3/trial_1_950fc43e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_3/trial_2_184717ad/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_3/trial_3_4ec214ab/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_3/trial_4_c59fc4a4/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_3/trial_5_312021aa/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_3/trial_6_50501f05/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_3/trial_7_ade58dd0/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_3/trial_8_7a8ec38b/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_3/trial_9_39a3e882/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_4/trial_0_dc405cdf/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_4/trial_1_3c43e912/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_4/trial_2_c535d75e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_4/trial_3_78b5e076/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_4/trial_4_e888a9e8/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_4/trial_5_4754288b/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_4/trial_6_139c52d9/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_4/trial_7_b9bbe308/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_4/trial_8_c7b26e32/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_4/trial_9_f0d3f3cf/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_5/trial_0_353a9916/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_5/trial_1_0e9f8d87/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_5/trial_2_ab374c69/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_5/trial_3_9b23be8f/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_5/trial_4_2e5a4143/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_5/trial_5_3f91dab6/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_5/trial_6_35693ab1/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_5/trial_7_ffbc9ef5/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_5/trial_8_990778c5/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_5/trial_9_c2b81fcc/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_6/trial_0_2456f71e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_6/trial_1_71fb3155/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_6/trial_2_47734353/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_6/trial_3_fce20cd9/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_6/trial_4_9f458ad7/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_6/trial_5_5ea27ea2/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_6/trial_6_ec2926e3/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_6/trial_7_896bf19f/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_6/trial_8_ed7b5735/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/2026-11-05/_b80b31b3/shots_6/trial_9_be626ea2/pipeline_args.json &

# Wait for all background srun tasks
wait

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "All cases finished."
echo "Wall time: $((ELAPSED / 60))m $((ELAPSED % 60))s"
