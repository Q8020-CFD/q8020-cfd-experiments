#!/bin/bash
#SBATCH -J q8020_sweep
#SBATCH -A ard189
#SBATCH -t 02:00:00
#SBATCH -N 20
#SBATCH -C nvme
#SBATCH -p batch
#SBATCH -o /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-10/_f1112a1f/slurm_%j.out
#SBATCH -e /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-10/_f1112a1f/slurm_%j.err

echo "Job ID: $SLURM_JOB_ID"
echo "Nodes:  $SLURM_JOB_NUM_NODES"
echo "Cases:  20"
echo "Start:  $(date)"
echo ""

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

cd $SLURM_SUBMIT_DIR || exit 1

# --- Broadcast packed venvs to NVMe ---
echo 'Broadcasting autofs_nccs-svm1_proj_ard189_agallojr_proj_src_q8020_fvm_euler_1d_solver_.venv.tar.gz...'
sbcast -pf /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-10/_f1112a1f/autofs_nccs-svm1_proj_ard189_agallojr_proj_src_q8020_fvm_euler_1d_solver_.venv.tar.gz /mnt/bb/${USER}/venv_0.tar.gz
if [ "$?" != "0" ]; then echo "ERROR: sbcast autofs_nccs-svm1_proj_ard189_agallojr_proj_src_q8020_fvm_euler_1d_solver_.venv.tar.gz failed"; exit 1; fi
srun -N ${SLURM_NNODES} --ntasks-per-node 1 mkdir -p /mnt/bb/${USER}/venv_0
srun -N ${SLURM_NNODES} --ntasks-per-node 1 tar -xzf /mnt/bb/${USER}/venv_0.tar.gz -C /mnt/bb/${USER}/venv_0
srun -N ${SLURM_NNODES} --ntasks-per-node 1 sed -i "s|VIRTUAL_ENV=.*|VIRTUAL_ENV=\"/mnt/bb/${USER}/venv_0\"|" /mnt/bb/${USER}/venv_0/bin/activate
echo 'Broadcasting autofs_nccs-svm1_proj_ard189_agallojr_proj_src_q8020_.venv.tar.gz...'
sbcast -pf /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-10/_f1112a1f/autofs_nccs-svm1_proj_ard189_agallojr_proj_src_q8020_.venv.tar.gz /mnt/bb/${USER}/venv_1.tar.gz
if [ "$?" != "0" ]; then echo "ERROR: sbcast autofs_nccs-svm1_proj_ard189_agallojr_proj_src_q8020_.venv.tar.gz failed"; exit 1; fi
srun -N ${SLURM_NNODES} --ntasks-per-node 1 mkdir -p /mnt/bb/${USER}/venv_1
srun -N ${SLURM_NNODES} --ntasks-per-node 1 tar -xzf /mnt/bb/${USER}/venv_1.tar.gz -C /mnt/bb/${USER}/venv_1
srun -N ${SLURM_NNODES} --ntasks-per-node 1 sed -i "s|VIRTUAL_ENV=.*|VIRTUAL_ENV=\"/mnt/bb/${USER}/venv_1\"|" /mnt/bb/${USER}/venv_1/bin/activate
echo "Environments ready"

# --- Launch all cases in parallel ---
echo "Launching 20 cases..."
START_TIME=$(date +%s)

srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-10/_f1112a1f/more_iters_0/trial_0_5c9bff98/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-10/_f1112a1f/more_iters_0/trial_1_ebaed51c/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-10/_f1112a1f/more_iters_0/trial_2_b8df2621/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-10/_f1112a1f/more_iters_0/trial_3_ae6ddcba/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-10/_f1112a1f/more_iters_0/trial_4_24f63710/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-10/_f1112a1f/more_iters_0/trial_5_b4fd5068/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-10/_f1112a1f/more_iters_0/trial_6_19606019/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-10/_f1112a1f/more_iters_0/trial_7_42201eb4/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-10/_f1112a1f/more_iters_0/trial_8_98102e3b/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-10/_f1112a1f/more_iters_0/trial_9_7334972d/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-10/_f1112a1f/more_iters_1/trial_0_fe2018a5/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-10/_f1112a1f/more_iters_1/trial_1_a869944c/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-10/_f1112a1f/more_iters_1/trial_2_db4c1cbe/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-10/_f1112a1f/more_iters_1/trial_3_5ac700b7/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-10/_f1112a1f/more_iters_1/trial_4_a1bb7968/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-10/_f1112a1f/more_iters_1/trial_5_717bf3de/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-10/_f1112a1f/more_iters_1/trial_6_fe9719bd/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-10/_f1112a1f/more_iters_1/trial_7_21f6d3a0/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-10/_f1112a1f/more_iters_1/trial_8_81c5faae/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-10/_f1112a1f/more_iters_1/trial_9_1fbf8ad0/pipeline_args.json &

# Wait for all background srun tasks
wait

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "All cases finished."
echo "Wall time: $((ELAPSED / 60))m $((ELAPSED % 60))s"
