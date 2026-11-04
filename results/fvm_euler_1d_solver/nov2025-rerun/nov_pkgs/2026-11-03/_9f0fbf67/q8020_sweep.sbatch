#!/bin/bash
#SBATCH -J q8020_sweep
#SBATCH -A ard189
#SBATCH -t 012:00:00
#SBATCH -N 2
#SBATCH -C nvme
#SBATCH -p extended
#SBATCH -o /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/slurm_%j.out
#SBATCH -e /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/slurm_%j.err

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
echo 'Broadcasting autofs_nccs-svm1_home1_ishangore_q8020_fvm_euler_1d_solver-main_.venv.tar.gz...'
sbcast -pf /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/autofs_nccs-svm1_home1_ishangore_q8020_fvm_euler_1d_solver-main_.venv.tar.gz /mnt/bb/${USER}/venv_0.tar.gz
if [ "$?" != "0" ]; then echo "ERROR: sbcast autofs_nccs-svm1_home1_ishangore_q8020_fvm_euler_1d_solver-main_.venv.tar.gz failed"; exit 1; fi
srun -N ${SLURM_NNODES} --ntasks-per-node 1 mkdir -p /mnt/bb/${USER}/venv_0
srun -N ${SLURM_NNODES} --ntasks-per-node 1 tar -xzf /mnt/bb/${USER}/venv_0.tar.gz -C /mnt/bb/${USER}/venv_0
srun -N ${SLURM_NNODES} --ntasks-per-node 1 sed -i "s|VIRTUAL_ENV=.*|VIRTUAL_ENV=\"/mnt/bb/${USER}/venv_0\"|" /mnt/bb/${USER}/venv_0/bin/activate
echo "Environments ready"

# --- Launch all cases in parallel ---
echo "Launching 71 cases..."
START_TIME=$(date +%s)

srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/719a35aa/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_0/trial_0_fa97c8e9/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_0/trial_1_eeefdeb8/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_0/trial_2_d3e6a5b4/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_0/trial_3_ec875285/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_0/trial_4_1b4b762a/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_0/trial_5_99690d4f/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_0/trial_6_0a51b739/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_0/trial_7_3587bb5a/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_0/trial_8_93e44124/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_0/trial_9_23b0fc61/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_1/trial_0_45867c48/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_1/trial_1_ba37f390/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_1/trial_2_a6a53eb0/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_1/trial_3_a2ea4389/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_1/trial_4_95bed03d/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_1/trial_5_9b2059d7/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_1/trial_6_d342cfdd/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_1/trial_7_1a715d94/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_1/trial_8_741cbf0c/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_1/trial_9_807b048a/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_2/trial_0_7711da5a/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_2/trial_1_28c7c073/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_2/trial_2_21cafbc3/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_2/trial_3_b5e16afe/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_2/trial_4_7c8c842e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_2/trial_5_fc451a73/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_2/trial_6_27378194/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_2/trial_7_4d1387a4/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_2/trial_8_03b2f7b7/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_2/trial_9_1efd2d66/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_3/trial_0_bc4c6e9b/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_3/trial_1_2bfdcc0e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_3/trial_2_4f836836/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_3/trial_3_bbecfcdc/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_3/trial_4_46615c8f/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_3/trial_5_d94c605c/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_3/trial_6_ed145e2c/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_3/trial_7_7f393eb2/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_3/trial_8_a77f14a2/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_3/trial_9_e3b28ed5/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_4/trial_0_53ab3ce3/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_4/trial_1_a3fe0f78/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_4/trial_2_8177c7b2/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_4/trial_3_71dcf076/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_4/trial_4_7ef3721e/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_4/trial_5_944cfdc7/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_4/trial_6_f16e4a37/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_4/trial_7_3bf3496a/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_4/trial_8_802cd4e9/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_4/trial_9_3fb4a868/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_5/trial_0_305a9295/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_5/trial_1_c826eecd/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_5/trial_2_05206535/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_5/trial_3_b751c636/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_5/trial_4_5021b645/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_5/trial_5_5caef407/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_5/trial_6_aff332cb/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_5/trial_7_d3a87f1b/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_5/trial_8_d66105ee/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_5/trial_9_5ac2355c/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_6/trial_0_5b3ecf81/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_6/trial_1_03d97ee2/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_6/trial_2_afd9999d/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_6/trial_3_42bb6667/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_6/trial_4_dd1e1ca8/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_6/trial_5_a50f8ecd/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_6/trial_6_c1e57f50/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_6/trial_7_0f2a0812/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_6/trial_8_ccdc50c4/pipeline_args.json &
srun -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker /ccs/home/ishangore/nov-rerun/2026-11-03/_9f0fbf67/shots_6/trial_9_76e22111/pipeline_args.json &

# Wait for all background srun tasks
wait

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "All cases finished."
echo "Wall time: $((ELAPSED / 60))m $((ELAPSED % 60))s"
