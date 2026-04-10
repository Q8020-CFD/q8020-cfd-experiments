#!/bin/bash
#SBATCH -J q8020_sweep
#SBATCH -A ard189
#SBATCH -t 02:00:00
#SBATCH -N 30
#SBATCH -C nvme
#SBATCH -p batch
#SBATCH -o /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/slurm_%j.out
#SBATCH -e /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/slurm_%j.err

echo "Job ID: $SLURM_JOB_ID"
echo "Nodes:  $SLURM_JOB_NUM_NODES"
echo "Cases:  30"
echo "Start:  $(date)"
echo ""

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

cd $SLURM_SUBMIT_DIR || exit 1

# --- Broadcast packed venvs to NVMe ---
echo 'Broadcasting autofs_nccs-svm1_proj_ard189_agallojr_proj_src_q8020_fvm_euler_1d_solver_.venv.tar.gz...'
sbcast -pf /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/autofs_nccs-svm1_proj_ard189_agallojr_proj_src_q8020_fvm_euler_1d_solver_.venv.tar.gz /mnt/bb/${USER}/venv_0.tar.gz
if [ "$?" != "0" ]; then echo "ERROR: sbcast autofs_nccs-svm1_proj_ard189_agallojr_proj_src_q8020_fvm_euler_1d_solver_.venv.tar.gz failed"; exit 1; fi
srun -N ${SLURM_NNODES} --ntasks-per-node 1 mkdir -p /mnt/bb/${USER}/venv_0
srun -N ${SLURM_NNODES} --ntasks-per-node 1 tar -xzf /mnt/bb/${USER}/venv_0.tar.gz -C /mnt/bb/${USER}/venv_0
srun -N ${SLURM_NNODES} --ntasks-per-node 1 sed -i "s|VIRTUAL_ENV=.*|VIRTUAL_ENV=\"/mnt/bb/${USER}/venv_0\"|" /mnt/bb/${USER}/venv_0/bin/activate
echo 'Broadcasting autofs_nccs-svm1_proj_ard189_agallojr_proj_src_q8020_.venv.tar.gz...'
sbcast -pf /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/autofs_nccs-svm1_proj_ard189_agallojr_proj_src_q8020_.venv.tar.gz /mnt/bb/${USER}/venv_1.tar.gz
if [ "$?" != "0" ]; then echo "ERROR: sbcast autofs_nccs-svm1_proj_ard189_agallojr_proj_src_q8020_.venv.tar.gz failed"; exit 1; fi
srun -N ${SLURM_NNODES} --ntasks-per-node 1 mkdir -p /mnt/bb/${USER}/venv_1
srun -N ${SLURM_NNODES} --ntasks-per-node 1 tar -xzf /mnt/bb/${USER}/venv_1.tar.gz -C /mnt/bb/${USER}/venv_1
srun -N ${SLURM_NNODES} --ntasks-per-node 1 sed -i "s|VIRTUAL_ENV=.*|VIRTUAL_ENV=\"/mnt/bb/${USER}/venv_1\"|" /mnt/bb/${USER}/venv_1/bin/activate
echo "Environments ready"

# --- Launch all cases in parallel ---
echo "Launching 30 cases..."
START_TIME=$(date +%s)

srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_0/trial_0_40373d9d/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_0/trial_1_078e27ce/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_0/trial_2_1b69ae14/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_0/trial_3_ba491dd0/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_0/trial_4_6b5b076d/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_0/trial_5_ef7fd401/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_0/trial_6_eceff102/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_0/trial_7_f9cf54fd/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_0/trial_8_7f3789ae/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_0/trial_9_6277fa33/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_1/trial_0_9cdf0f55/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_1/trial_1_5f0a63a7/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_1/trial_2_0b3b82ca/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_1/trial_3_b26ee708/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_1/trial_4_54f8c398/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_1/trial_5_879005c4/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_1/trial_6_dcf9d62f/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_1/trial_7_6125f5d0/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_1/trial_8_1db7490b/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_1/trial_9_48100086/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_2/trial_0_553b32ac/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_2/trial_1_e79067be/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_2/trial_2_4177571b/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_2/trial_3_c0ed9658/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_2/trial_4_12f8199d/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_2/trial_5_f6c435f2/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_2/trial_6_c1819e14/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_2/trial_7_a5806d07/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_2/trial_8_7b739958/pipeline_args.json &
srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-08/_85fd6d17/more_iters_2/trial_9_d348a548/pipeline_args.json &

# Wait for all background srun tasks
wait

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "All cases finished."
echo "Wall time: $((ELAPSED / 60))m $((ELAPSED % 60))s"
