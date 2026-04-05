#!/bin/bash
#SBATCH -J q8020_sweep
#SBATCH -A ard189
#SBATCH -t 02:00:00
#SBATCH -N 10
#SBATCH -C nvme
#SBATCH -p batch
#SBATCH -o /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_fdf6c14e/slurm_%j.out
#SBATCH -e /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_fdf6c14e/slurm_%j.err

echo "Job ID: $SLURM_JOB_ID"
echo "Nodes:  $SLURM_JOB_NUM_NODES"
echo "Cases:  10"
echo "Start:  $(date)"
echo ""

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

cd $SLURM_SUBMIT_DIR || exit 1

# --- Broadcast packed venvs to NVMe ---
echo 'Broadcasting autofs_nccs-svm1_home1_agallojr_proj_src_q8020_fvm_euler_1d_solver_.venv.tar.gz...'
sbcast -pf /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_fdf6c14e/autofs_nccs-svm1_home1_agallojr_proj_src_q8020_fvm_euler_1d_solver_.venv.tar.gz /mnt/bb/${USER}/venv_0.tar.gz
if [ "$?" != "0" ]; then echo "ERROR: sbcast autofs_nccs-svm1_home1_agallojr_proj_src_q8020_fvm_euler_1d_solver_.venv.tar.gz failed"; exit 1; fi
srun -N ${SLURM_NNODES} --ntasks-per-node 1 mkdir -p /mnt/bb/${USER}/venv_0
srun -N ${SLURM_NNODES} --ntasks-per-node 1 tar -xzf /mnt/bb/${USER}/venv_0.tar.gz -C /mnt/bb/${USER}/venv_0
srun -N ${SLURM_NNODES} --ntasks-per-node 1 sed -i "s|VIRTUAL_ENV=.*|VIRTUAL_ENV=\"/mnt/bb/${USER}/venv_0\"|" /mnt/bb/${USER}/venv_0/bin/activate
echo 'Broadcasting autofs_nccs-svm1_home1_agallojr_proj_src_q8020_.venv.tar.gz...'
sbcast -pf /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_fdf6c14e/autofs_nccs-svm1_home1_agallojr_proj_src_q8020_.venv.tar.gz /mnt/bb/${USER}/venv_1.tar.gz
if [ "$?" != "0" ]; then echo "ERROR: sbcast autofs_nccs-svm1_home1_agallojr_proj_src_q8020_.venv.tar.gz failed"; exit 1; fi
srun -N ${SLURM_NNODES} --ntasks-per-node 1 mkdir -p /mnt/bb/${USER}/venv_1
srun -N ${SLURM_NNODES} --ntasks-per-node 1 tar -xzf /mnt/bb/${USER}/venv_1.tar.gz -C /mnt/bb/${USER}/venv_1
srun -N ${SLURM_NNODES} --ntasks-per-node 1 sed -i "s|VIRTUAL_ENV=.*|VIRTUAL_ENV=\"/mnt/bb/${USER}/venv_1\"|" /mnt/bb/${USER}/venv_1/bin/activate
echo "Environments ready"

# --- Launch all cases in parallel ---
echo "Launching 10 cases..."
START_TIME=$(date +%s)

srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_fdf6c14e/55d3fa0a/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_fdf6c14e/733f897f/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_fdf6c14e/fb44194e/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_fdf6c14e/8778ec47/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_fdf6c14e/bbb603f6/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_fdf6c14e/d6865824/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_fdf6c14e/ea7daa54/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_fdf6c14e/509844a5/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_fdf6c14e/debf68fe/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_fdf6c14e/09be71ef/pipeline_args.json &

# Wait for all background srun tasks
wait

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "All cases finished."
echo "Wall time: $((ELAPSED / 60))m $((ELAPSED % 60))s"
