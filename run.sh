condor_rm hhao9

python3 gen_combo.py

rm -rf error_logs/*
rm -rf logs/*

for dir1 in BT Random Mallows_Tau_T1 Mallows_Tau_T10 PL Pairwise; do 
    for dir in BT saebm Pairwise Mallows_Tau PL; do
        # Delete all files in subdirectories (depth ≥ 2)
        find "algo_results/$dir1/$dir" -mindepth 2 -type f -delete
    done 
done 

condor_submit /home/hhao9/mpebm/run_mlhc.sub