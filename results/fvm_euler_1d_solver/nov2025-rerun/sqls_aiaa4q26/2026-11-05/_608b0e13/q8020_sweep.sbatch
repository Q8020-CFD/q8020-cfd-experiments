#!/bin/bash
#SBATCH -J q8020_sweep
#SBATCH -A ard189
#SBATCH -t 02:00:00
#SBATCH -N 2
#SBATCH -C nvme
#SBATCH -p batch
#SBATCH -o /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/slurm_%j.out
#SBATCH -e /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/slurm_%j.err

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
echo 'Broadcasting lustre_orion_ard189_scratch_ishangore_q8020_fvm_euler_1d_solver-sqls_.venv.tar.gz...'
sbcast -pf /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/lustre_orion_ard189_scratch_ishangore_q8020_fvm_euler_1d_solver-sqls_.venv.tar.gz /mnt/bb/${USER}/venv_0.tar.gz
if [ "$?" != "0" ]; then echo "ERROR: sbcast lustre_orion_ard189_scratch_ishangore_q8020_fvm_euler_1d_solver-sqls_.venv.tar.gz failed"; exit 1; fi
srun -N ${SLURM_NNODES} --ntasks-per-node 1 mkdir -p /mnt/bb/${USER}/venv_0
srun -N ${SLURM_NNODES} --ntasks-per-node 1 tar -xzf /mnt/bb/${USER}/venv_0.tar.gz -C /mnt/bb/${USER}/venv_0
srun -N ${SLURM_NNODES} --ntasks-per-node 1 sed -i "s|VIRTUAL_ENV=.*|VIRTUAL_ENV=\"/mnt/bb/${USER}/venv_0\"|" /mnt/bb/${USER}/venv_0/bin/activate
echo "Environments ready"

# --- Launch all cases in parallel ---
echo "Launching 71 cases..."
START_TIME=$(date +%s)

srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/5b6956ea/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/06ef7e83/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/5151d477/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/0c51ef3d/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/78f2e15e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/4bbfc5c4/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/7e0b1af7/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/671a04d6/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/7d2e4496/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/2cd3a768/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/e56dbe03/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/0cd13dd2/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/e7e8c243/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/15eaff48/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/e3c6168e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/f24845e5/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/6e4690b3/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/3527f110/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/0ac0f508/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/9559a5bc/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/babb0a3c/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/237a2dca/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/71330659/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/efc9ac21/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/4e1b1899/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/e28573fa/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/2c6265fd/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/bad46c96/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/fddff975/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/b194423a/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/7239eaf2/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/a9b3762a/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/e573496a/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/255b0fb0/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/6e2ef885/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/b30b47ba/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/59ce4f6a/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/59bde40d/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/bb1a0785/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/f138c573/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/5c61c5a4/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/446a7308/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/19f6761e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/b98a4533/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/c994f407/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/d4740277/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/b179bd97/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/3c5a9034/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/c3b01135/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/c1fe1db7/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/afd1cdab/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/b0fc1684/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/653fc6da/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/e3759f7a/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/c9d715d6/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/184b0a21/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/9f3ee40c/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/7cfbbe47/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/f69a89a2/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/9c8f8a03/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/12921db3/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/3b891bf3/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/d9629656/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/7d08a241/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/98238ff1/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/99e0d77e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/bc7b8970/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/2d5ca879/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/c312382e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/baf5b159/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-05/_608b0e13/a4773aa0/pipeline_args.json &

# Wait for all background srun tasks
wait

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "All cases finished."
echo "Wall time: $((ELAPSED / 60))m $((ELAPSED % 60))s"
