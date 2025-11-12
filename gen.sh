#!/bin/bash
set -euo pipefail

# ==============================================================================
# 🔄 Cleanup old outputs
# ==============================================================================
rm -rf data data.tar.gz 
rm -rf json_files
rm -f true_order_and_stages_BT.json \
      true_order_and_stages_Random.json \
      true_order_and_stages_Mallows_Tau_T1.json \
      true_order_and_stages_Mallows_Tau_T10.json \
      true_order_and_stages_Pairwise.json \
      true_order_and_stages_PL.json

rm -rf logs_gen/*

# ==============================================================================
# 🚀 Submit Condor job
# ==============================================================================
JOB_SUBMIT_OUT=$(condor_submit /home/hhao9/mpebm/run_gen.sub)
echo "$JOB_SUBMIT_OUT"

# Capture cluster/job ID
JOB_ID=$(echo "$JOB_SUBMIT_OUT" | awk '/submitted/ {print $6}')
echo "Submitted job with ID: $JOB_ID"

# ==============================================================================
# ⏳ Wait until Condor job finishes
# ==============================================================================
for logfile in /home/hhao9/mpebm/logs_gen/eval_*.log; do
    condor_wait "$logfile"
done

# ==============================================================================
# 📦 Post-processing after job finishes
# ==============================================================================
echo "Job $JOB_ID finished, packaging results..."

tar -czf data.tar.gz data
mv /home/hhao9/mpebm/data.tar.gz /staging/hhao9/mpebm_data.tar.gz
rm -rf data

mv json_files/* . && rmdir json_files

ls -lh /staging/hhao9/mpebm_data.tar.gz

# optional downstream run
bash run.sh
