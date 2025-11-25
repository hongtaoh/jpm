# Reproducible codes for JPM

This repository contains codes for the ML4H (2025) submission of *Joint Progression Modeling (JPM): A Probabilistic Framework for Mixed-Pathology Progression*.

Note that the data generation and experiments are conducted on a high-performance computing platform (CHTC at the University of Wisconsin--Madison) due to the large number of jobs to run. You can, however, modify relevant files to run on personal computers.

Many plots of our paper are available on Observable: [@hongtaoh/jpm](https://observablehq.com/@hongtaoh/jpm).

## Notice

In this study (the original version submitted for review), we used slightly earlier version of [`pysaebm`](https://github.com/jpcca/pysaebm) to get the theta/phi parameters of 18 biomarkers from ADNI, and then generated the synthetic data. We later updated `pysaebm` by using soft rather than hard assignment in the conjugate priors algorithm. But we didn't update the synthetic data with the new theta/phi obtained from running the newer version of `pysaebm`. 

This is because 1) The update on the conjugate prior algorithm will barely alter the theta/phi results; 2) The results of JPM, i.e., the relative advantanges of it over `pysaebm` is not dependent on this small change in the theta/phi; 3) The version we submitted for review was based on the earlier version of `pysaebm`. 

We did use the latest `pysaebm` in our experiments in terms of benchmarking JPM's performance against it. 


## Cite this paper

```
@inproceedings{Hao2025JointProgression,
  author    = {Hongtao Hao and Joseph L. Austerweil},
  title     = {Joint Progression Modeling (JPM): A Probabilistic Framework for Mixed-Pathology Progression},
  booktitle = {Proceedings of the 5th Machine Learning for Health Symposium},
  volume    = {297},
  pages     = {??--??}, % Page numbers are not provided now, will add later. 
  year      = {2025},
  publisher = {PMLR},
}
```

## Installation and Setup

```sh
pip install pyjpm
```

Please refer to [https://github.com/hongtaoh/pyjpm](https://github.com/hongtaoh/pyjpm) for more information about the package. 

## How to generate synthetic data?

### Obtain theta/phi values of 18 biomarkers


Within `adni_norm_results`, there are the results of running EBM on the [ADNI](https://adni.loni.usc.edu/) data. The results are obtained by running `python3 run_adni.py`. It will use the `utils_adni.py` file.


In that folder, you can find `conjugate_priors` and `mle`. These two are slightly different algorithms, but the results are almost the same. We relied on the results of `conjugate_priors`.


The most important file is `conjugate_priors/results/adni_results.json`. These are the theta/phi parameters for the 18 biomarkers. We used them to generate synthetic data. This makes sure our synthetic data are as close to the real world as possible. The results are stored in `params.json`.


### How to get raw ADNI data?


In `run_adni.py`, you can see you need `ADNIMERGE.csv`. You can get it by [apply for data access through ADNI](https://adni.loni.usc.edu/data-samples/adni-data/#AccessData). They process requests within one week.


After you are granted the access, log in [https://ida.loni.usc.edu/login.jsp](https://ida.loni.usc.edu/login.jsp). Then go to [https://ida.loni.usc.edu/home/projectPage.jsp?project=ADNI](https://ida.loni.usc.edu/home/projectPage.jsp?project=ADNI). Click "Search & Download". In the dropdown menu, click "Study Files".


You'll see "Analysis Ready Cohort (ARC) Builder". In the search box, type "merge".


![ADNI](img/adni.png)


Download the following two files:


- ADNIMERGE-Key ADNI tables merged into one table [ADNI1,GO,2,3]


- ADNIMERGE-Key ADNI tables merged into one table - Dictionary [ADNI1,GO,2,3]

## How to obtain the NACC data

NACC data can be requested through https://naccdata.org.

Please refer to *Appendix J. NACC Data Preprocessing Pipeline* of our paper for details of which datasetes of NACC were included. 

### Generate synthetic data


Related files are `gen.sh`, `run_gen.py`, `run_gen.sh`, and `run_gen.sub`.


To generate synthetic data, run `bash gen.sh`. The resulting folder and files will be


- `logs_gen` folder
- `true_order_and_stages_BT.json`
- `true_order_and_stages_Mallows_Tau_T1.0.json`
- `true_order_and_stages_Mallows_Tau_T10.0.json`
- `true_order_and_stages_Pairwise.json`
- `true_order_and_stages_PL.json`
- `true_order_and_stages_Random.json`


## How to study calibration, separation and sharpness


In Section 4 of the paper, we studied calibration, separation and sharpness. In the following, I'll detail how we obtain simulation data and do the data analysis.

Related files are `run_meta.py`, `run_meta.sh`, and `run_meta.sub`.


Run `bash meta.sh` and the meta data in csv format will be saved into the folder of `metadata`. The log files will be saved into `logs_meta`.

The analysis notebook is `notebooks/2025-09-07-analyze-results.ipynb`.

## How to run synthetic experiments


Related files are `run_mlhc.py`, `run_mlhc.sh`, and `run_mlhc.sub`.


Run `bash run.sh` to run the experiments. All results will be saved to the folder of `algo_results`.


## How to analyze synthetic data results


Run `python3 save_csv.py`. You'll get all the results as `all_results.csv`.


For data analysis and visualizations, we used Observable: [@hongtaoh/jpm](https://observablehq.com/@hongtaoh/jpm)


## How to analyze the real-world NACC results

Please visit [https://github.com/hongtaoh/jpm_nacc](https://github.com/hongtaoh/jpm_nacc) for details. 


## Other files

- `config.yaml`: all hyper-parameters for our experiments.
- `gen_combo.py`: to generate filenames to be used in all `sh` files. The results will be `all_combinations.txt`. We also have `test_combinations.txt` for testing purposes.
- `failed_files.txt`, `missing_files.txt`, `na_combinations.txt` are the diagnostic files after running `python3 save_csv.py`.