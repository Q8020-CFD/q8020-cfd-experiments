#!/bin/bash
#SBATCH -J q8020_sweep
#SBATCH -A ard189
#SBATCH -t 24:00:00
#SBATCH -N 1
#SBATCH -C nvme
#SBATCH -p extended
#SBATCH -o /lustre/orion/ard189/scratch/ishangore/burgers_ab_shock_q8/2026-06-11/_ba24bd17/slurm_%j.out
#SBATCH -e /lustre/orion/ard189/scratch/ishangore/burgers_ab_shock_q8/2026-06-11/_ba24bd17/slurm_%j.err

echo "Job ID: $SLURM_JOB_ID"
echo "Nodes:  $SLURM_JOB_NUM_NODES"
echo "Cases:  4"
echo "Start:  $(date)"
echo ""

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

cd $SLURM_SUBMIT_DIR || exit 1

# --- Broadcast packed venvs to NVMe ---
echo 'Broadcasting autofs_nccs-svm1_home1_ishangore_q8020_q8020-mps-burgers_.venv.tar.gz...'
sbcast -pf /lustre/orion/ard189/scratch/ishangore/burgers_ab_shock_q8/2026-06-11/_ba24bd17/autofs_nccs-svm1_home1_ishangore_q8020_q8020-mps-burgers_.venv.tar.gz /mnt/bb/${USER}/venv_0.tar.gz
if [ "$?" != "0" ]; then echo "ERROR: sbcast autofs_nccs-svm1_home1_ishangore_q8020_q8020-mps-burgers_.venv.tar.gz failed"; exit 1; fi
srun -N ${SLURM_NNODES} --ntasks-per-node 1 mkdir -p /mnt/bb/${USER}/venv_0
srun -N ${SLURM_NNODES} --ntasks-per-node 1 tar -xzf /mnt/bb/${USER}/venv_0.tar.gz -C /mnt/bb/${USER}/venv_0
srun -N ${SLURM_NNODES} --ntasks-per-node 1 sed -i "s|VIRTUAL_ENV=.*|VIRTUAL_ENV=\"/mnt/bb/${USER}/venv_0\"|" /mnt/bb/${USER}/venv_0/bin/activate
echo "Environments ready"

# --- Launch all cases in parallel ---
echo "Launching 4 cases..."
START_TIME=$(date +%s)

srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/burgers_ab_shock_q8/2026-06-11/_ba24bd17/cb483bb5/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/burgers_ab_shock_q8/2026-06-11/_ba24bd17/9e8bcbc7/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/burgers_ab_shock_q8/2026-06-11/_ba24bd17/f290e3db/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/scratch/ishangore/burgers_ab_shock_q8/2026-06-11/_ba24bd17/6b1a1202/pipeline_args.json &

# Wait for all background srun tasks
wait

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "All cases finished."
echo "Wall time: $((ELAPSED / 60))m $((ELAPSED % 60))s"
