#!/bin/bash
#SBATCH -J q8020_sweep
#SBATCH -A ard189
#SBATCH -t 02:00:00
#SBATCH -N 16
#SBATCH -C nvme
#SBATCH -p batch
#SBATCH -o /ccs/home/ishangore/aer_rocm_mpi_ladder/2026-07-29/_6f55714e/slurm_%j.out
#SBATCH -e /ccs/home/ishangore/aer_rocm_mpi_ladder/2026-07-29/_6f55714e/slurm_%j.err

echo "Job ID: $SLURM_JOB_ID"
echo "Nodes:  $SLURM_JOB_NUM_NODES"
echo "Cases:  3"
echo "Start:  $(date)"
echo ""

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

cd $SLURM_SUBMIT_DIR || exit 1

# --- Broadcast packed venvs to NVMe ---
echo 'Broadcasting autofs_nccs-svm1_home1_ishangore_aer-rocm-env.tar.gz...'
sbcast -pf /ccs/home/ishangore/aer_rocm_mpi_ladder/2026-07-29/_6f55714e/autofs_nccs-svm1_home1_ishangore_aer-rocm-env.tar.gz /mnt/bb/${USER}/venv_0.tar.gz
if [ "$?" != "0" ]; then echo "ERROR: sbcast autofs_nccs-svm1_home1_ishangore_aer-rocm-env.tar.gz failed"; exit 1; fi
srun -N ${SLURM_NNODES} --ntasks-per-node 1 mkdir -p /mnt/bb/${USER}/venv_0
srun -N ${SLURM_NNODES} --ntasks-per-node 1 tar -xzf /mnt/bb/${USER}/venv_0.tar.gz -C /mnt/bb/${USER}/venv_0
srun -N ${SLURM_NNODES} --ntasks-per-node 1 sed -i "s|VIRTUAL_ENV=.*|VIRTUAL_ENV=\"/mnt/bb/${USER}/venv_0\"|" /mnt/bb/${USER}/venv_0/bin/activate
echo "Environments ready"

# --- Launch all cases in parallel ---
echo "Launching 3 cases..."
START_TIME=$(date +%s)

python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/aer_rocm_mpi_ladder/2026-07-29/_6f55714e/1ace4eb7/pipeline_args.json
python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/aer_rocm_mpi_ladder/2026-07-29/_6f55714e/62c91754/pipeline_args.json
python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/aer_rocm_mpi_ladder/2026-07-29/_6f55714e/04f24d85/pipeline_args.json

# Wait for all background srun tasks
wait

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "All cases finished."
echo "Wall time: $((ELAPSED / 60))m $((ELAPSED % 60))s"
