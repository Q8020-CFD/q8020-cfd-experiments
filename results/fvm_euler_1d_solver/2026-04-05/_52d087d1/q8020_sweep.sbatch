#!/bin/bash
#SBATCH -J q8020_sweep
#SBATCH -A ard189
#SBATCH -t 02:00:00
#SBATCH -N 50
#SBATCH -C nvme
#SBATCH -p batch
#SBATCH -o /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/slurm_%j.out
#SBATCH -e /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/slurm_%j.err

echo "Job ID: $SLURM_JOB_ID"
echo "Nodes:  $SLURM_JOB_NUM_NODES"
echo "Cases:  50"
echo "Start:  $(date)"
echo ""

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

cd $SLURM_SUBMIT_DIR || exit 1

# --- Broadcast packed venvs to NVMe ---
echo 'Broadcasting autofs_nccs-svm1_home1_agallojr_proj_src_q8020_fvm_euler_1d_solver_.venv.tar.gz...'
sbcast -pf /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/autofs_nccs-svm1_home1_agallojr_proj_src_q8020_fvm_euler_1d_solver_.venv.tar.gz /mnt/bb/${USER}/venv_0.tar.gz
if [ "$?" != "0" ]; then echo "ERROR: sbcast autofs_nccs-svm1_home1_agallojr_proj_src_q8020_fvm_euler_1d_solver_.venv.tar.gz failed"; exit 1; fi
srun -N ${SLURM_NNODES} --ntasks-per-node 1 mkdir -p /mnt/bb/${USER}/venv_0
srun -N ${SLURM_NNODES} --ntasks-per-node 1 tar -xzf /mnt/bb/${USER}/venv_0.tar.gz -C /mnt/bb/${USER}/venv_0
srun -N ${SLURM_NNODES} --ntasks-per-node 1 sed -i "s|VIRTUAL_ENV=.*|VIRTUAL_ENV=\"/mnt/bb/${USER}/venv_0\"|" /mnt/bb/${USER}/venv_0/bin/activate
echo 'Broadcasting autofs_nccs-svm1_home1_agallojr_proj_src_q8020_.venv.tar.gz...'
sbcast -pf /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/autofs_nccs-svm1_home1_agallojr_proj_src_q8020_.venv.tar.gz /mnt/bb/${USER}/venv_1.tar.gz
if [ "$?" != "0" ]; then echo "ERROR: sbcast autofs_nccs-svm1_home1_agallojr_proj_src_q8020_.venv.tar.gz failed"; exit 1; fi
srun -N ${SLURM_NNODES} --ntasks-per-node 1 mkdir -p /mnt/bb/${USER}/venv_1
srun -N ${SLURM_NNODES} --ntasks-per-node 1 tar -xzf /mnt/bb/${USER}/venv_1.tar.gz -C /mnt/bb/${USER}/venv_1
srun -N ${SLURM_NNODES} --ntasks-per-node 1 sed -i "s|VIRTUAL_ENV=.*|VIRTUAL_ENV=\"/mnt/bb/${USER}/venv_1\"|" /mnt/bb/${USER}/venv_1/bin/activate
echo "Environments ready"

# --- Launch all cases in parallel ---
echo "Launching 50 cases..."
START_TIME=$(date +%s)

srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_0/trial_0_5066b4fb/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_0/trial_1_8fff62ef/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_0/trial_2_a737f819/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_0/trial_3_6b478372/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_0/trial_4_54246c3c/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_0/trial_5_1193d015/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_0/trial_6_04ccd01a/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_0/trial_7_b95665fb/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_0/trial_8_97c060de/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_0/trial_9_f9c201fb/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_1/trial_0_84dc6b0d/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_1/trial_1_65e0ded0/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_1/trial_2_cafd455d/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_1/trial_3_5c33f3ad/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_1/trial_4_1a466ab3/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_1/trial_5_762a02b5/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_1/trial_6_260104de/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_1/trial_7_5965c52b/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_1/trial_8_4f34ed4b/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_1/trial_9_380d749d/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_2/trial_0_bce93f35/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_2/trial_1_8d42c6c7/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_2/trial_2_70b0277c/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_2/trial_3_bd37e26a/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_2/trial_4_4bf8208b/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_2/trial_5_b5447def/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_2/trial_6_be587499/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_2/trial_7_ebdb138c/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_2/trial_8_004f6f1b/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_2/trial_9_b9eff1eb/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_3/trial_0_d18dd36e/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_3/trial_1_2a5ddc42/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_3/trial_2_c550cf70/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_3/trial_3_6080342f/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_3/trial_4_eacc7d46/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_3/trial_5_b1e84f0a/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_3/trial_6_7c3262f3/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_3/trial_7_94ea70ce/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_3/trial_8_e749eadc/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_3/trial_9_6ecdb855/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_4/trial_0_b9da8a4e/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_4/trial_1_0a804fc3/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_4/trial_2_80703f65/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_4/trial_3_3576792c/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_4/trial_4_2c8c9dda/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_4/trial_5_883b9fa8/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_4/trial_6_d7fb3dc3/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_4/trial_7_203b7613/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_4/trial_8_8bbac5ae/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/time_steps_4/trial_9_e9e7683f/pipeline_args.json &

# Wait for all background srun tasks
wait

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "All cases finished."
echo "Wall time: $((ELAPSED / 60))m $((ELAPSED % 60))s"
