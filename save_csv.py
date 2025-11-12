import os
import json
import pandas as pd
import re
import yaml
import numpy as np 
from tqdm import tqdm
import shutil
from pyjpm import get_params_path
import pyjpm.mp_utils as mp_utils

EPSILON = 1e-12

def extract_components(filename):
    # filename without "_results.json"
    name = filename.replace('_results.json', '')
    pattern = r'^j(\d+)_r([\d.]+)_E(.*?)_m(\d+)$'
    match = re.match(pattern, name)
    if match:
        return match.groups()  # returns tuple (J, R, E, M)
    return None

def generate_expected_files(config, ALL_DATA_DIR, ALL_ALGOS):
    """Generate all expected (algo, filename) tuples based on config"""
    expected = []
    for data_dir in ALL_DATA_DIR:
        for algo in ALL_ALGOS:
            for J in config['JS']:
                for R in config['RS']:
                    for E in config['EXPERIMENT_NAMES']:
                        for M in range(config['N_VARIANTS']):
                            fname = f"j{J}_r{R}_E{E}_m{M}_results.json"
                            expected.append((data_dir, algo, fname))
    return set(expected)

def main():

    # params_file = get_params_path()
    params_file = 'params.json'

    with open(params_file) as f:
        params = json.load(f)

    biomarkers_str = np.array(sorted(params.keys()))
    biomarkers_int = np.arange(0, len(params))
    str2int = dict(zip(biomarkers_str, biomarkers_int))
    int2str = dict(zip(biomarkers_int, biomarkers_str))

    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    OUTPUT_DIR = config['OUTPUT_DIR']
    SEED = config['GEN_SEED']
    rng = np.random.default_rng(SEED)

    ALL_ALGOS = config['TESTED_MP_METHODS'] + ['saebm']
    ALL_DATA_DIR = config['MP_DATA_DIR']
    # ALL_DATA_DIR = ['Pairwise']
    JS = config['JS']
    RS = config['RS']
    EXPERIMENTS = config['EXPERIMENT_NAMES']
    N_VARIANTS = config['N_VARIANTS']

    # titles = [
    #     "Exp 1: S & Ordinal kj (DM) & X (Normal)",
    #     "Exp 2: S & Ordinal kj (DM) & X (Non-Normal)",
    #     "Exp 3: S & Ordinal kj (Uniform) & X (Normal)",
    #     "Exp 4: S & Ordinal kj (Uniform) & X (Non-Normal)",
    #     "Exp 8: S & Continuous kj (Uniform) & X (Sigmoid)",
    #     "Exp 9: S & Continuous kj (Skewed) & X (Sigmoid)",
    #     "Exp 5: S & Continuous kj (Uniform) & X (Normal)",
    #     "Exp 6: S & Continuous kj (Uniform) & X (Non-Normal)",
    #     "Exp 0: S & Continuous kj (Skewed) & X (Normal)",
    #     "Exp 7: S & Continuous kj (Skewed) & X (Non-Normal)",
    #     "Exp 10: xi (Normal) & Continuous kj (Skewed) & X (Sigmoid)",
    #     "Exp 11: xi (Normal) & Continuous kj (Skewed) & X (Normal)"
    # ]

    titles = [
        "Exp 1: S + Ordinal kj (DM) + X (Normal)",
        "Exp 2: S + Ordinal kj (DM) + X (Non-Normal)",
        "Exp 3: S + Ordinal kj (Uniform) + X (Normal)",
        "Exp 4: S + Ordinal kj (Uniform) + X (Non-Normal)",
        "Exp 8: S + Continuous kj (Uniform) + X (Sigmoid)",
        "Exp 9: S + Continuous kj (Skewed) + X (Sigmoid)",
        "Exp 5: S + Continuous kj (Uniform) + X (Normal)",
        "Exp 6: S + Continuous kj (Uniform) + X (Non-Normal)",
        "Exp 0: S + Continuous kj (Skewed) + X (Normal)",
        "Exp 7: S + Continuous kj (Skewed) + X (Non-Normal)",
        "Exp 10: xi (Normal) + Continuous kj (Skewed) + X (Sigmoid)",
        "Exp 11: xi (Normal) + Continuous kj (Skewed) + X (Normal)"
    ]

    exp_nums = [1,2,3,4,8,9,5,6,0,7,10,11]

    algos = config['TESTED_MP_METHODS'] + ['EBM']

    # exp_nums = range(1, len(titles) + 1)

    # Normalize mapping dictionaries
    CONVERT_E_DICT = {k: v for k, v in zip(EXPERIMENTS, titles)}
    CONVERT_ALGO_DICT = {k: v for k, v in zip(ALL_ALGOS, algos)}
    GET_E_NUM = dict(zip(titles, exp_nums))

    # Initialize tracking structures
    expected_files = generate_expected_files(
        config, ALL_DATA_DIR=ALL_DATA_DIR, ALL_ALGOS=ALL_ALGOS)
    found_files = set()
    missing_files = set()
    failed_files = []
    records = []

    for data_dir in tqdm(ALL_DATA_DIR, desc=f"Processing data_dirs"):
        print(f'Processing {data_dir}')
        with open(f"true_order_and_stages_{data_dir}.json", "r") as f:
            true_order_and_stages = json.load(f)
        # Process all algorithms
        for algo in ALL_ALGOS:
            algo_dir = os.path.join(OUTPUT_DIR, data_dir, algo, "results")

            if not os.path.exists(algo_dir):
                print(f"\nWarning: Missing directory for {data_dir}, {algo}")
                continue

            # Process all result files
            files = [f for f in os.listdir(algo_dir) if f.endswith('_results.json')]
            for fname in tqdm(files, desc=f"{algo}", leave=False):
                # obtain certainty and conflict 
                fname_data = true_order_and_stages[fname.replace("_results.json", '')]
                ordering_array = np.array(fname_data['ordering_array'])
                unpadded_ordering_array = []
                for order in ordering_array:
                    unpadded_order = [x for x in order if x >= 0]
                    unpadded_ordering_array.append(unpadded_order)
                average_partial_ranking_length = sum(len(x) for x in unpadded_ordering_array)/len(ordering_array)
                n_partial_rankings = fname_data["n_partial_rankings"]

                full_path = os.path.join(algo_dir, fname)

                # Track found files
                found_files.add((data_dir, algo, fname))

                # Parse filename components
                components = extract_components(fname)
                if not components:
                    failed_files.append((full_path, "Invalid filename format"))
                    continue

                J, R, E, M = components
                try:
                    J = int(J)
                    R = float(R)
                    M = int(M)
                except ValueError:
                    failed_files.append((full_path, "Invalid numeric format in filename"))
                    continue
                    
                # Validate against config
                if J not in JS:
                    failed_files.append((full_path, f"Invalid J value {J}"))
                    continue
                if R not in RS:
                    failed_files.append((full_path, f"Invalid R value {R}"))
                    continue
                if E not in EXPERIMENTS:
                    failed_files.append((full_path, f"Invalid experiment {E}"))
                    continue
                if not (0 <= M < N_VARIANTS):
                    failed_files.append((full_path, f"Invalid M value {M}"))
                    continue

                # Load and validate JSON content
                try:
                    with open(full_path, 'r') as f:
                        data = json.load(f)
                    
                    if 'kendalls_tau' not in data or 'mean_absolute_error' not in data:
                        failed_files.append((full_path, "Missing metrics in JSON"))
                        continue

                    algo_pretty = CONVERT_ALGO_DICT.get(algo, algo)  
                    E_pretty = CONVERT_E_DICT.get(E, E)
                    E_num = GET_E_NUM.get(E_pretty, 0)

                    if E_num == 0:
                        continue 

                    kendalls_tau = data['kendalls_tau']
                    mae_result = data['mean_absolute_error']

                    # # Calcuate energy
                    # highest_ll_order  = [k for k, v in sorted(data["order_with_highest_ll"].items(), key=lambda item: item[1])]
                    # highest_ll_order = np.array([str2int[bm] for bm in highest_ll_order])

                    # mallows_temperature = np.nan 
                    # mp_method = data_dir
                    # if data_dir == 'Random':
                    #     energy = np.nan
                    # if data_dir == 'Mallows_Tau_T1.0':
                    #     mallows_temperature = 1
                    #     mp_method = 'Mallows_Tau'
                    # if data_dir == 'Mallows_Tau_T10.0':
                    #     mallows_temperature = 10 
                    #     mp_method = 'Mallows_Tau'
                    # try:
                    #     if data_dir != 'Random':
                    #         if data_dir == 'PL':
                    #             sampler = mp_utils.PlackettLuce(ordering_array=ordering_array, rng=rng)
                    #         else:
                    #             sampler = mp_utils.MCMC(
                    #                 ordering_array=ordering_array, 
                    #                 method=mp_method, 
                    #                 rng=rng, 
                    #                 mallows_temperature=mallows_temperature
                    #             )
                    #         energy = sampler.get_energy(highest_ll_order)
                        
                    # except Exception as e:
                    #     print(f"{data_dir}")
                    #     print(f"An error occurred: {e}")
                        
                    records.append({
                        'data_framework': data_dir,
                        'J': J,
                        'R': R,
                        'E': E_pretty,
                        'M': M,
                        'algo': algo_pretty,
                        'E_Num': int(E_num),
                        'n_partial_rankings': n_partial_rankings,
                        # 'energy': energy,
                        'kendalls_tau': kendalls_tau,
                        'average_partial_ranking_length': average_partial_ranking_length,
                        'mae': mae_result,
                    })
                except json.JSONDecodeError:
                    failed_files.append((full_path, "Invalid JSON format"))
                except Exception as e:
                    failed_files.append((full_path, f"Unexpected error: {str(e)}"))
    
    # Calculate missing files
    missing_files = expected_files - found_files

    # Save results
    if records:
        df = pd.DataFrame(records)
        df = df.sort_values(by=['J', 'R', 'E', 'M', 'algo'])
        df.to_csv('all_results.csv', index=False)
        print(f"\nSaved {len(df)} valid records to all_results.csv")

    # Save diagnostics
    if missing_files:
        unique_missing_fnames = set([x[2].replace("_results.json", "") for x in missing_files])
        with open('missing_files.txt', 'w') as f:
            f.write("Data_Framework,Algorithm,Filename\n")
            for data_framework, algo, fname in sorted(missing_files):
                f.write(f"{data_framework},{algo},{fname}\n")
        print(f"Logged {len(missing_files)} missing files to missing_files.txt")

        # Save NA_COMBINATIONS.txt 
        with open('na_combinations.txt', 'w') as f:
            print(f'Number of unique missing fnames: {len(unique_missing_fnames)}')
            for fname in sorted(unique_missing_fnames):
                f.write(f"{fname}\n")
        print(f"Logged {len(unique_missing_fnames)} unique missing files to na_combinations.txt")

        # Copy err and out logs 
        # Create the error_logs directory if it doesn't exist
        os.makedirs('error_logs', exist_ok=True)
        
        ERR_LOGS = [f"eval_{x}.err" for x in unique_missing_fnames]
        OUT_LOGS = [f"eval_{x}.out" for x in unique_missing_fnames]
        LOG_LOGS = [f"eval_{x}.log" for x in unique_missing_fnames]
        
        # Copy each file from logs to error_logs
        for filename in ERR_LOGS + OUT_LOGS + LOG_LOGS:
            source_path = os.path.join('logs', filename)
            dest_path = os.path.join('error_logs', filename)
            try:
                shutil.copy2(source_path, dest_path)
            except FileNotFoundError:
                print(f"File not found: {filename}")
            except Exception as e:
                print(f"Error copying {filename}: {e}")
        print("Done copying files to error_logs folder")     
        
    if failed_files:
        with open('failed_files.txt', 'w') as f:
            f.write("Path, Reason\n")
            for path, reason in failed_files:
                f.write(f"{path}, {reason}\n")
        print(f"Logged {len(failed_files)} failed files to failed_files.txt")

if __name__ == '__main__':
    main()
