import sys 
import os 
sys.path.append(os.getcwd())
import json 
import yaml
import re 
from pyjpm import generate
import numpy as np 

def extract_components(filename):
    pattern = r'^j(\d+)_r([\d.]+)_E(.*?)_m(\d+)$'
    match = re.match(pattern, filename)
    if match:
        return match.groups()  # returns tuple (J, R, E, M)
    return None

def convert_np_types(obj):
    """Convert numpy types in a nested dictionary to Python standard types."""
    if isinstance(obj, dict):
        return {k: convert_np_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_np_types(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return convert_np_types(obj.tolist())
    else:
        return obj
    
if __name__ == "__main__":
    # Get directories correct
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Current working directory: {base_dir}")

    # Read parameters from command line arguments
    mp_method = sys.argv[1]
    print(f"Now generating with: {mp_method}")

    OUTPUT_DIR = os.path.join(base_dir, 'data')
    JSON_DIR = os.path.join(base_dir, 'json_files')

    # Get path to default parameters
    params_file = 'params.json'

    with open(params_file) as f:
        params = json.load(f)

    biomarkers_str = np.array(sorted(params.keys()))
    biomarkers_int = np.arange(0, len(params))
    int2str = dict(zip(biomarkers_int, biomarkers_str))

    config_path = os.path.join(base_dir, 'config.yaml')
    with open(config_path, "r") as f:
        config =  yaml.safe_load(f)
    print("Loaded config:")
    # print(json.dumps(config, indent=4))

    rng = np.random.default_rng(config['GEN_SEED'])

    ########################################################################
    # Generate data using the MP EBM framework
    ########################################################################
    all_dicts = []
    if 'Mallows' not in mp_method:
        DATA_DIR = os.path.join(OUTPUT_DIR, mp_method)
        for exp_name in config['EXPERIMENT_NAMES']:
            random_state = rng.integers(0, 2**32 - 1)
            true_order_and_stages_dicts = generate(
                    mixed_pathology=True,
                    experiment_name = exp_name,
                    params_file=params_file,
                    js = config['JS'], 
                    rs = config['RS'],
                    num_of_datasets_per_combination=config['N_VARIANTS'],
                    output_dir=DATA_DIR,
                    seed=random_state,
                    keep_all_cols = False,
                    fixed_biomarker_order = False, # to randomize things
                    mp_method=mp_method,
                    sample_count = config['MP_SAMPLE_COUNT_GEN'],
                    mcmc_iterations = config['MP_MCMC'],
                    low_num=config['LOW_NUM'], # lowest possible number of n_partial_rankings
                    high_num=config['HIGH_NUM'],
                    low_length=config['LOW_LENGTH'], # shortest possible partial ranking length
                    high_length=config['HIGH_LENGTH'], # longest possible partial ranking length
                    pl_best = False
                )
            all_dicts.append(true_order_and_stages_dicts)

        combined = {k: v for d in all_dicts for k, v in d.items()}
        combined = convert_np_types(combined)

        # Dump the JSON
        json_path = os.path.join(JSON_DIR, f"true_order_and_stages_{mp_method}.json")
        with open(json_path, "w") as f:
            json.dump(combined, f, indent=2)

        print("Aggregated ordering data completed!")
        """
        Generate partial rankings
        """
        for fname, fname_data in combined.items():
            J, R, E, M = extract_components(fname)
            ordering_array = fname_data['ordering_array']
            for idx, partial_ordering in enumerate(ordering_array):
                random_state = rng.integers(0, 2**32 - 1)
                # obtain the new partial params
                partial_params = {int2str[bm]: params[int2str[bm]] for bm in partial_ordering if bm in int2str}

                # partial_params = {}
                # for bm_int in partial_ordering:
                #     if bm_int in int2str:
                #         bm = int2str[bm_int]
                #         partial_params[bm] = params[bm]
                
                generate(
                    mixed_pathology=False,
                    experiment_name = E,
                    params=partial_params,
                    js = [int(J) * config['TIMES_MORE']], # J * 2
                    rs = [float(R)], # 
                    num_of_datasets_per_combination=1,
                    output_dir=DATA_DIR,
                    seed=random_state,
                    keep_all_cols = False,
                    fixed_biomarker_order=True,
                    # the ith partial ranking for fname
                    prefix=f"PR{idx}_m{M}"
                )
    else:
        for mallows_temperature in [1.0, 10.0]:
            all_dicts = []
            suffix_text = f'T{mallows_temperature}'
            DATA_DIR = os.path.join(OUTPUT_DIR, f"{mp_method}_T{mallows_temperature}")
            for exp_name in config['EXPERIMENT_NAMES']:
                random_state = rng.integers(0, 2**32 - 1)
                true_order_and_stages_dicts = generate(
                        mixed_pathology=True,
                        experiment_name = exp_name,
                        params_file=params_file,
                        js = config['JS'], 
                        rs = config['RS'],
                        num_of_datasets_per_combination=config['N_VARIANTS'],
                        output_dir=DATA_DIR,
                        seed=random_state,
                        keep_all_cols = False,
                        fixed_biomarker_order = True, # THIS SHOULD ALWASY BE TRUE, OTHERWISE ALL PARTICIPANTS WON'T HAVE THE SAME SEQUENCE SHARED 
                        mp_method=mp_method,
                        sample_count = config['MP_SAMPLE_COUNT_GEN'],
                        mcmc_iterations = config['MP_MCMC'],
                        low_num=config['LOW_NUM'], # lowest possible number of n_partial_rankings
                        high_num=config['HIGH_NUM'],
                        low_length=config['LOW_LENGTH'], # shortest possible partial ranking length
                        high_length=config['HIGH_LENGTH'], # longest possible partial ranking length
                        mallows_temperature = mallows_temperature
                    )
                all_dicts.append(true_order_and_stages_dicts)

            combined = {k: v for d in all_dicts for k, v in d.items()}
            combined = convert_np_types(combined)

            # Dump the JSON
            json_path = os.path.join(JSON_DIR, f"true_order_and_stages_{mp_method}_{suffix_text}.json")
            with open(json_path, "w") as f:
                json.dump(combined, f, indent=2)

            print("Aggregated ordering data completed!")
            """
            Generate partial rankings
            """
            
            for fname, fname_data in combined.items():
                J, R, E, M = extract_components(fname)
                ordering_array = fname_data['ordering_array']
                for idx, partial_ordering in enumerate(ordering_array):
                    random_state = rng.integers(0, 2**32 - 1)
                    # obtain the new partial params
                    partial_params = {int2str[bm]: params[int2str[bm]] for bm in partial_ordering if bm in int2str}
                    # partial_params = {}
                    # for bm_int in partial_ordering:
                    #     if bm_int in int2str:
                    #         bm = int2str[bm_int]
                    #         partial_params[bm] = params[bm]
                    
                    generate(
                        mixed_pathology=False,
                        experiment_name = E,
                        params=partial_params,
                        js = [int(J) * config['TIMES_MORE']], # J * 2
                        rs = [float(R)], # 
                        num_of_datasets_per_combination=1,
                        output_dir=DATA_DIR,
                        seed=random_state,
                        keep_all_cols = False,
                        fixed_biomarker_order=True,
                        # the ith partial ranking for fname
                        prefix=f"PR{idx}_m{M}"
                    )
    