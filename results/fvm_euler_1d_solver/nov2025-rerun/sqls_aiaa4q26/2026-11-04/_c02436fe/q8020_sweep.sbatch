#!/bin/bash
#SBATCH -J q8020_sweep
#SBATCH -A ard189
#SBATCH -t 08:00:00
#SBATCH -N 2
#SBATCH -C nvme
#SBATCH -p extended
#SBATCH -o /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/slurm_%j.out
#SBATCH -e /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/slurm_%j.err

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
sbcast -pf /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/lustre_orion_ard189_scratch_ishangore_q8020_fvm_euler_1d_solver-sqls_.venv.tar.gz /mnt/bb/${USER}/venv_0.tar.gz
if [ "$?" != "0" ]; then echo "ERROR: sbcast lustre_orion_ard189_scratch_ishangore_q8020_fvm_euler_1d_solver-sqls_.venv.tar.gz failed"; exit 1; fi
srun -N ${SLURM_NNODES} --ntasks-per-node 1 mkdir -p /mnt/bb/${USER}/venv_0
srun -N ${SLURM_NNODES} --ntasks-per-node 1 tar -xzf /mnt/bb/${USER}/venv_0.tar.gz -C /mnt/bb/${USER}/venv_0
srun -N ${SLURM_NNODES} --ntasks-per-node 1 sed -i "s|VIRTUAL_ENV=.*|VIRTUAL_ENV=\"/mnt/bb/${USER}/venv_0\"|" /mnt/bb/${USER}/venv_0/bin/activate
echo "Environments ready"

# --- Launch all cases in parallel ---
echo "Launching 71 cases..."
START_TIME=$(date +%s)

srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/be88f101/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/4f201cc3/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/b1e31114/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/0cb0d1a8/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/a3ce356f/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/926129f6/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/0b6319bc/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/ac38d162/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/ecc81339/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/86361fef/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/dda8ed83/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/6d7f4e6c/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/22c4c98e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/176529e0/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/4254f5df/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/c23eeead/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/654dcb6c/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/5a2d2bba/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/ec8cfa6f/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/61d4f919/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/9dc0f712/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/d3e98285/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/0eecab28/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/69ee266e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/ee48bc47/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/d6b28e43/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/3344c7ac/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/b8b9155d/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/e83ea68e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/73b76115/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/a176598b/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/47024b4f/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/ef9d257b/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/768c3e5f/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/e451f899/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/af8bd94c/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/d60e50d7/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/c9399c24/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/35538957/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/cf7cabe4/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/73b31b73/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/298fe9e1/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/6e37c3d8/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/2712d919/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/17d3520c/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/51d70242/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/ecba34d2/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/ddd2e18f/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/9559900f/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/6c0875c5/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/02251727/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/3cedd8b1/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/4e9c9f57/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/65352155/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/18302c94/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/96fd56d5/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/5e649f4d/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/ef2fde0f/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/15a0fab1/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/a5ae9d3e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/0ff736a1/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/55f59cdc/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/7ca76e14/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/ebbc87d8/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/c82405b1/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/40ce6999/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/97e1603e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/8ce374e8/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/4d2f3671/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/b441bd46/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/sqls/2026-11-04/_c02436fe/fe084a49/pipeline_args.json &

# Wait for all background srun tasks
wait

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "All cases finished."
echo "Wall time: $((ELAPSED / 60))m $((ELAPSED % 60))s"
