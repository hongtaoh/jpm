import sys 
import os 
sys.path.append(os.getcwd())
import json 
import yaml
import re 
import pandas as pd
from pyjpm.mp_utils import PlackettLuce,  MCMC, compute_conflict2, get_average_tau
from scipy.stats import pearsonr, spearmanr
import numpy as np 

def extract_components(filename):
    pattern = r'^j(\d+)_r([\d.]+)_E(.*?)_m(\d+)$'
    match = re.match(pattern, filename)
    if match:
        return match.groups()  # returns tuple (J, R, E, M)
    return None

def load_config():
    current_dir = os.path.dirname(__file__)  # Get the directory of the current script
    config_path = os.path.join(current_dir, "config.yaml")
    
    with open(config_path, "r") as f:
        return yaml.safe_load(f)
    
def get_overlap_rate(padded_partial_ranks:np.ndarray) -> float:
    flat_data = padded_partial_ranks.flatten()
    filtered_data = flat_data[flat_data != -1]
    if filtered_data.size == 0:
        return 0.0
    unique_items, counts = np.unique(filtered_data, return_counts=True)
    repeated_items_count = np.sum(counts > 1)
    total_unique_items = len(unique_items)
    return repeated_items_count / total_unique_items

if __name__ == "__main__":
    # Get directories correct
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Current working directory: {base_dir}")

    # Read parameters from command line arguments
    filename = sys.argv[1]
    J, R, E, M = extract_components(filename)
    print(f"Processing with {filename}")

    # Parameters
    config = load_config()
    MP_SAMPLE_COUNT = config['MP_SAMPLE_COUNT']
    N_RANDOM_PERMS = config['N_RANDOM_PERMS']
    MP_MCMC = config['MP_MCMC']
    N_SHUFFLE = config['N_SHUFFLE']
    MP_METADATA_DIR = config['MP_METADATA_DIR']
    EXPERIMENTS = config['EXPERIMENT_NAMES']
    OUTPUT_DIR = os.path.join(base_dir, MP_METADATA_DIR)
    
    titles = [
        "Exp 1: S + Ordinal kj (DM) + X (Normal)",
        "Exp 2: S + Ordinal kj (DM) + X (Non-Normal)",
        "Exp 3: S + Ordinal kj (Uniform) + X (Normal)",
        "Exp 4: S + Ordinal kj (Uniform) + X (Non-Normal)",
        "Exp 8: S + Continuous kj (Uniform) + X (Sigmoid)",
        "Exp 9: S + Continuous kj (Skewed) + X (Sigmoid)",
        "Exp 5: S + Continuous kj (Uniform) + X (Normal)",
        "Exp 6: S + Continuous kj (Uniform) + X (Non-Normal)",
        "Exp 10: S + Continuous kj (Skewed) + X (Normal)",
        "Exp 7: S + Continuous kj (Skewed) + X (Non-Normal)",
        "Exp 11: xi (Normal) + Continuous kj (Skewed) + X (Sigmoid)",
        "Exp 12: xi (Normal) + Continuous kj (Skewed) + X (Normal)"
    ]

    exp_nums = [1,2,3,4,8,9,5,6,10,7,11,12]

    # Normalize mapping dictionaries
    CONVERT_E_DICT = {k: v for k, v in zip(EXPERIMENTS, titles)}
    GET_E_NUM = dict(zip(titles, exp_nums))

    E_pretty = CONVERT_E_DICT.get(E, E)
    E_Num = GET_E_NUM.get(E_pretty, 0)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    rng = np.random.default_rng(config['GEN_SEED'])
    all_data_framework = config['MP_DATA_DIR']
    all_data_framework = [x for x in all_data_framework if x != 'Random']

    ALL_DICTS = []
    for data_framework in all_data_framework:
        mp_method = data_framework if 'Mallows_Tau' not in data_framework else 'Mallows_Tau'
        mallows_temperature = 1 if data_framework == 'Mallows_Tau_T1' else 10
        json_file = os.path.join(base_dir, f"true_order_and_stages_{data_framework}.json")
        if not os.path.isfile(json_file):
            print(f"Error: JSON file {json_file} does not exist.")
            sys.exit(1)

        with open(json_file, "r") as f:
            true_order_and_stages = json.load(f)
        padded_partial_ranks = np.array(true_order_and_stages[filename]['ordering_array'])
        # n_partial_rankings = true_order_and_stages[filename]['n_partial_rankings']
        # unpadded_ordering_array = []
        # for order in padded_partial_ranks:
        #     unpadded_order = [x for x in order if x >= 0]
        #     unpadded_ordering_array.append(unpadded_order)
        # average_partial_ranking_length = sum(len(x) for x in unpadded_ordering_array)/len(padded_partial_ranks)

        conflict = compute_conflict2(padded_partial_ranks)
        overlap_rate = get_overlap_rate(padded_partial_ranks)

        if data_framework == 'PL':
            sampler = PlackettLuce(
                ordering_array=padded_partial_ranks, 
                rng=rng, 
                sample_count=MP_SAMPLE_COUNT, 
                pl_best=False,
                mcmc_iterations=MP_MCMC, 
                n_shuffle=N_SHUFFLE, 
                n_random_perms=N_RANDOM_PERMS,
            )
        else:
            sampler = MCMC(
                ordering_array=padded_partial_ranks,
                rng=rng, 
                method=mp_method, 
                mcmc_iterations=MP_MCMC, 
                n_shuffle=N_SHUFFLE, 
                n_random_perms=N_RANDOM_PERMS,
                sample_count=MP_SAMPLE_COUNT, 
                mallows_temperature=mallows_temperature
            )
        sampler.compute_alignment_and_determinism()
        # ground truth generated by the generator 
        sigma_gt = sampler.sampled_combined_orderings # ground truth orderings
        unique_elements = sampler.unique_elements
        curr_dic = {
            'data_framework': data_framework,
            'E_Num': E_Num,
            'conflict': conflict,
            'overlap_rate': overlap_rate,
            # 'n_pr': n_partial_rankings,
            # 'mean_len': average_partial_ranking_length,
            # 'calibration': sampler.spearman_rho,
            'separation': sampler.aggrank_dependence,
            'sharpness': sampler.aggrank_agreement
        }
        for inf_method in ['BT', 'PL', 'Pairwise', 'Mallows_Tau']:
            random_perms = np.array([rng.permutation(unique_elements) for _ in range(N_RANDOM_PERMS)])
            if inf_method == 'PL':
                inf_sampler = PlackettLuce(
                    ordering_array=padded_partial_ranks, 
                    rng=rng, 
                    sample_count=MP_SAMPLE_COUNT, 
                    pl_best=False,
                    mcmc_iterations=MP_MCMC, 
                    n_shuffle=N_SHUFFLE, 
                    n_random_perms=N_RANDOM_PERMS,
                )
            else:
                inf_sampler = MCMC(
                    ordering_array=padded_partial_ranks, 
                    rng=rng, 
                    method=inf_method, 
                    mcmc_iterations=MP_MCMC, 
                    sample_count=MP_SAMPLE_COUNT, 
                    n_shuffle=N_SHUFFLE, 
                    n_random_perms=N_RANDOM_PERMS,
                    mallows_temperature=mallows_temperature
                )
            # rho (E_inf (Rand perms), d(rand perms, sigm_gt))
            e_inf_randperms_arr = [inf_sampler.get_energy(x) for x in random_perms]
            tau_dists, _ = get_average_tau(random_perms, sigma_gt)
            spearman_rho, _ = spearmanr(e_inf_randperms_arr, tau_dists)
            # make a fresh copy per algo
            result_dic = curr_dic.copy()
            result_dic.update({
                'algo': inf_method,
                'spearman_rho': spearman_rho
            })
            ALL_DICTS.append(result_dic)
    df = pd.DataFrame(ALL_DICTS)
    params = {'J': int(J), 'R': float(R), 'E': E_pretty, 'M': int(M)}
    for name, value in params.items():
        df[name] = value
    df.to_csv(f"{OUTPUT_DIR}/{filename}.csv",index=False)
    # df.to_parquet(f"{OUTPUT_DIR}/{filename}.parquet", engine="pyarrow", index=False)

    