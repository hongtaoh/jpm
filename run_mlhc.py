import sys 
import os 
sys.path.append(os.getcwd())

import json 
from pyjpm import run_mpebm, get_params_path
from pyjpm.mp_utils import get_unique_rows

import yaml
import re 
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

if __name__ == "__main__":
    # Get directories correct
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Current working directory: {base_dir}")

    params_file = get_params_path()

    with open(params_file) as f:
        params = json.load(f)

    biomarkers_str = np.array(sorted(params.keys()))
    biomarkers_int = np.arange(0, len(params))
    str2int = dict(zip(biomarkers_str, biomarkers_int))
    int2str = dict(zip(biomarkers_int, biomarkers_str))

    # Parameters
    config = load_config()
    print("Loaded config:")
    print(json.dumps(config, indent=4))

    N_MCMC=config['N_MCMC']
    N_SHUFFLE=config['N_SHUFFLE']
    BURN_IN=config['BURN_IN']
    THINNING=config['THINNING']
    MCMC_SEED = config['MCMC_SEED']

    rng = np.random.default_rng(config['MCMC_SEED'])

    for mp_data_dir in config['MP_DATA_DIR']:
        data_dir = os.path.join(base_dir, "data", mp_data_dir)
        OUTPUT_DIR=os.path.join(config['OUTPUT_DIR'], mp_data_dir)

        # Read parameters from command line arguments
        filename = sys.argv[1]
        J, R, E, M = extract_components(filename)
        print(f"Processing with {filename}")
        data_file = os.path.join(data_dir, f"{filename}.csv")
        if not os.path.isfile(data_file):
            print(f"Error: Data file {data_file} does not exist.")
            sys.exit(1)

        # Obtain ordering_array
        estimated_partial_rankings = []
        # final_theta_phi_list = []

        # Get true order and true stages dict
        with open(os.path.join(base_dir, f"true_order_and_stages_{mp_data_dir}.json"), "r") as f:
            true_order_and_stages = json.load(f)
        true_order_dict = true_order_and_stages[filename]['true_order']
        true_stages = true_order_and_stages[filename]['true_stages']
        partial_rankings = true_order_and_stages[filename]['ordering_array']
        n_partial_rankings = len(partial_rankings)

        for idx in range(n_partial_rankings):
            random_state = rng.integers(0, 2**32 - 1)
            # partial ranking data file path
            five_times_J = int(J)*config['TIMES_MORE']
            pr_data_file = os.path.join(data_dir, f"PR{idx}_m{M}_j{five_times_J}_r{R}_E{E}.csv")

            _, order_with_highest_ll = run_mpebm(
                data_file=pr_data_file,
                save_results=False,
                n_iter=N_MCMC * 2,
                n_shuffle=N_SHUFFLE,
                burn_in=BURN_IN,
                thinning=THINNING,
                seed = random_state
            )
            partial_ordering_str = [k for k, v in sorted(order_with_highest_ll.items(), key=lambda item: item[1])]
            partial_ordering = [str2int[bm] for bm in partial_ordering_str]
            estimated_partial_rankings.append(partial_ordering)
            
        # theta_phi_use = merge_mean_dicts(final_theta_phi_list)
        padded_partial_rankings = get_unique_rows(estimated_partial_rankings)

        ###################################################################################
        # Step1: MPEBM
        ###################################################################################
        for mp_method in config['TESTED_MP_METHODS']:
            random_state = rng.integers(0, 2**32 - 1)
            run_mpebm(
                save_results=True,
                partial_rankings=padded_partial_rankings,
                bm2int=str2int,
                mp_method=mp_method,
                data_file= data_file,
                output_dir=OUTPUT_DIR,
                output_folder=mp_method,
                n_iter=N_MCMC,
                n_shuffle=N_SHUFFLE,
                burn_in=BURN_IN,
                thinning=THINNING,
                true_order_dict=true_order_dict,
                true_stages = true_stages,
                seed = random_state,
                mallows_temperature = 1.0,
            )
        
        ###################################################################################
        # Step2: 
        ###################################################################################
        random_state = rng.integers(0, 2**32 - 1)
        run_mpebm(
            save_results=True,
            data_file= data_file,
            output_dir=OUTPUT_DIR,
            output_folder='saebm',
            n_iter=N_MCMC,
            n_shuffle=N_SHUFFLE,
            burn_in=BURN_IN,
            thinning=THINNING,
            true_order_dict=true_order_dict,
            true_stages = true_stages,
            seed = random_state
        )


    

    
    