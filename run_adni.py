import sys 
import os 
sys.path.append(os.getcwd())

import os 
from pysaebm import run_ebm
import utils_adni
import yaml
import json 

meta_data = ['PTID', 'DX_bl', 'VISCODE', 'COLPROT']

'''
Cognition: MoCA (global), Trails B (executive), Digit Span (attention/WM), Logical Memory (episodic).

Function: FAQ (daily living skills).

Imaging: FDG-PET (metabolism, cross-disease marker).
'''

select_biomarkers = [
    'MMSE_bl', 'Ventricles_bl', 'WholeBrain_bl', 'MidTemp_bl', 
    'Fusiform_bl', 'Entorhinal_bl', 'Hippocampus_bl', 'ADAS13_bl', 
    'PTAU_bl', 'TAU_bl', 'ABETA_bl', 'RAVLT_immediate_bl', 
    'ICV_bl', 
    'CDRSB_bl', # Clinical Dementia Rating Sum of Boxes, standard staging measure across dementias, 0 missing.
    'MOCA_bl', # Montreal Cognitive Assessment, widely used in AD, vascular dementia, Parkinson’s disease, and FTD. More sensitive than MMSE. 
    'TRABSCOR_bl', # Trail Making Test B, executive function → especially relevant for vascular dementia and Parkinson’s-related cognitive decline. 
    'FAQ_bl', # Functional Activities Questionnaire, daily living function across all dementias. 
    'FDG_bl', # FDG-PET, hypometabolism is a hallmark across AD, FTD, DLB, Parkinson’s disease dementia. #
    'LDELTOTAL_BL', # Episodic memory, affected in AD, VaD, DLB, sometimes in FTD. Broadly used in trials outside AD as well. 
]

diagnosis_list = ['CN', 'EMCI', 'LMCI', 'AD']

raw = 'ADNIMERGE.csv'

def load_config():
    current_dir = os.path.dirname(__file__)  # Get the directory of the current script
    config_path = os.path.join(current_dir, "config.yaml")
    
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

if __name__ == "__main__":
    # Get directories correct
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Current working directory: {base_dir}")

    OUTPUT_DIR = os.path.join(base_dir, 'adni_norm_results')
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Parameters
    config = load_config()
    print("Loaded config:")
    print(json.dumps(config, indent=4))

    # Number of independent optimization attempts in greedy ascent
    N_MCMC=config['N_MCMC']
    # N_MCMC = 100
    N_SHUFFLE=config['N_SHUFFLE']
    BURN_IN=config['BURN_IN']
    # BURN_IN = 10
    THINNING=config['THINNING']
    MCMC_SEED = config['MCMC_SEED']

    raw = os.path.join(base_dir, raw)

    adni_filtered = utils_adni.get_adni_filtered(raw, meta_data, select_biomarkers, diagnosis_list)
    debm_output, data_matrix, df_long, participant_dx_dict, ordered_biomarkers = utils_adni.process_data(adni_filtered, ventricles_log=False, tau_log=False)
    df_long.to_csv('adni.csv', index=False)

    for algorithm in ['mle', 'conjugate_priors']:
        results = run_ebm(
            data_file=os.path.join(base_dir, 'adni.csv'),
            algorithm=algorithm,
            output_dir=OUTPUT_DIR,
            n_iter=20000,
            n_shuffle=2,
            burn_in=500,
            thinning=1,
            skip_heatmap=False,
            skip_traceplot=False,
            seed=42, ## 42 turns out to be the best
            save_results=True,
            save_details=True,
            save_theta_phi=True,
        )
