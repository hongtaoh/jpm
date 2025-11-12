import pandas as pd 
import numpy as np 
from typing import List, Dict, Tuple, Optional
import copy 
import altair as alt 
from collections import defaultdict, namedtuple, Counter

def get_adni_filtered(raw:str, meta_data:List[str], select_biomarkers:List[str], diagnosis_list:List[str]) -> pd.DataFrame:
    """Get the filtered data. 
    meta_data = ['PTID', 'DX_bl', 'VISCODE', 'COLPROT']

    select_biomarkers = ['MMSE_bl', 'Ventricles_bl', 'WholeBrain_bl', 
                'MidTemp_bl', 'Fusiform_bl', 'Entorhinal_bl', 
                'Hippocampus_bl', 'ADAS13_bl', 'PTAU_bl', 
                'TAU_bl', 'ABETA_bl', 'RAVLT_immediate_bl', 'ICV_bl'
    ]

    diagnosis_list = ['CN', 'EMCI', 'LMCI', 'AD']
    """
    df = pd.read_csv(raw, usecols=meta_data + select_biomarkers, low_memory=False)
    # 2. Filter to baseline and known diagnoses
    df = df[df['VISCODE'] == 'bl']
    df = df[df['DX_bl'].isin(diagnosis_list)]

    # 3. Convert biomarker columns to numeric (handles garbage strings like '--')
    for col in select_biomarkers:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # 4. Drop rows with any NaN in biomarkers
    df = df.dropna(subset=select_biomarkers).reset_index(drop=True)
    df = df.drop_duplicates().reset_index(drop=True)
    print(len(df))
    if len(df.PTID.unique()) == len(df):
        print('No duplicates!')
    else:
        print('Data has duplicates!')
    
    # Print DX distribution
    counts = Counter(df['DX_bl'])
    total = sum(counts.values())

    for k, v in counts.items():
        perc = 100 * v / total
        print(f"{k}: {v} ({perc:.1f}%)")
    
    print('----------------------------------------------------')
    
    # Print Cohort distribution
    counts = Counter(df['COLPROT'])
    total = sum(counts.values())

    for k, v in counts.items():
        perc = 100 * v / total
        print(f"{k}: {v} ({perc:.1f}%)")

    return df 

def process_data(df:pd.DataFrame, ventricles_log:bool, tau_log:bool) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[int, str], List[str]]:
    """To get the required output for debm, ucl, and sa-ebm
    df: adni_filtered
    """
    df['PTID'] = range(len(df))
    # df['Diagnosis'] = ['MCI' if x in ['EMCI', 'LMCI'] else x for x in df.DX_bl]
    # df['Diagnosis'] = df.DX_bl
    df.columns = df.columns.str.replace('_bl', '', regex=False)
    df.columns = df.columns.str.replace('_BL', '', regex=False)
    df['Diagnosis'] = df.DX
    # ICV normalization because brain sizes vary a lot 
    df['VentricleNorm']  = df['Ventricles']  / df['ICV']
    df['HippocampusNorm'] = df['Hippocampus'] / df['ICV']
    df['WholeBrainNorm']  = df['WholeBrain']  / df['ICV']
    df['EntorhinalNorm']  = df['Entorhinal']  / df['ICV']
    df['FusiformNorm']    = df['Fusiform']    / df['ICV']
    df['MidTempNorm']     = df['MidTemp']     / df['ICV']
    if tau_log:
        df['TAU (log)'] = np.log10(df['TAU'])
        df['PTAU (log)'] = np.log10(df['PTAU'])
        df.drop(['TAU', 'PTAU'], axis=1, inplace=True)
    if ventricles_log:
        df['VentricleNorm (log)'] = np.log10(df['VentricleNorm'])
        df.drop(['VentricleNorm', 'Ventricles'], axis=1, inplace=True)
    participant_dx_dict = dict(zip(df.PTID, df.DX))
    df.drop([
        'VISCODE', 'COLPROT', 'DX', 'ICV', 'Ventricles', 
        'Hippocampus', 'WholeBrain', 'Entorhinal', 'Fusiform', 'MidTemp'
    ], axis=1, inplace=True)
    # for debm
    debm_output = df.copy()
    df.drop(['Diagnosis', 'PTID'], axis=1, inplace=True)
    # Ordered biomarkers, to match the ordering outputs later
    ordered_biomarkers = list(df.columns)
    df['diseased'] = [int(dx != 'CN') for dx in participant_dx_dict.values()]
    # for ucl
    data_matrix = copy.deepcopy(df.to_numpy())
    df['participant'] = range(len(df))
    df['diseased'] = [bool(x) for x in df.diseased]
    df_long = pd.melt(
        df,
        id_vars=['participant', 'diseased'],       # columns to keep fixed
        var_name='biomarker',              # name for former column names
        value_name='measurement'                 # name for the measured values
    )
    return debm_output, data_matrix, df_long, participant_dx_dict, ordered_biomarkers
    
def plot_staging(ml_stages:List[int], participant_dx_dict:Dict[int, str], algorithm:str):

    # DataFrame preparation
    df = pd.DataFrame({
        'Stage': ml_stages,
        'Diagnosis': list(participant_dx_dict.values())
    })
    diagnosis_order = ['CN', 'EMCI', 'LMCI', 'AD']
    stage_range = list(range(df['Stage'].min(), df['Stage'].max() + 1))

    # Count table with missing combinations filled
    count_df = df.groupby(['Stage', 'Diagnosis']).size().reset_index(name='Count')
    all_combinations = pd.MultiIndex.from_product([stage_range, diagnosis_order], names=['Stage', 'Diagnosis'])
    count_df = count_df.set_index(['Stage', 'Diagnosis']).reindex(all_combinations, fill_value=0).reset_index()

    # Calculate stage totals for reference
    stage_totals = count_df.groupby('Stage')['Count'].sum().reset_index()
    stage_totals = stage_totals.rename(columns={'Count': 'Total'})
    count_df = pd.merge(count_df, stage_totals, on='Stage')

    # Calculate percentage for tooltips while keeping absolute counts for display
    count_df['Percentage'] = count_df['Count'] / count_df['Total']

    # Paul Tol's colorblind-friendly palette (scientific standard)
    color_scale = alt.Scale(
        domain=['CN', 'EMCI', 'LMCI', 'AD'],
        range=['#4477AA', '#66CCEE', '#228833', '#EE6677']  # blue, cyan, green, red
    )

    # Define the base chart with improved typography and sizing
    base = alt.Chart(count_df).properties(
        width=500,
        height=300,
        title={
            'text': f'Distribution of Disease Stages by Diagnosis, {algorithm}',
            'anchor': 'middle',
            'fontWeight': 'normal',
            'fontSize': 14,
            'dy': -10
        }
    )

    # Main stacked bar chart with absolute counts
    bars = base.mark_bar().encode(
        x=alt.X('Stage:O', 
                title='',
                axis=alt.Axis(
                    labelFontSize=11,
                    titleFontSize=12,
                    titleFont='Arial',
                    titlePadding=15,
                    grid=False
                )
        ),
        y=alt.Y('Count:Q', 
                title='Number of Participants',  # Changed to reflect absolute counts
                axis=alt.Axis(
                    labelFontSize=11,
                    titleFontSize=12,
                    titleFont='Arial',
                    grid=True,
                    gridOpacity=0.4,
                    titlePadding=15
                )
        ),
        color=alt.Color('Diagnosis:N', 
                        scale=color_scale,
                        legend=alt.Legend(
                            title=None,
                            labelFontSize=11,
                            symbolSize=100,
                            orient='top',
                            direction='horizontal',
                            columns=4
                        )
        ),
        order=alt.Order('Diagnosis:N', sort='ascending'),
        tooltip=[
            alt.Tooltip('Stage:O', title='Stage'),
            alt.Tooltip('Diagnosis:N', title='Diagnosis'),
            alt.Tooltip('Count:Q', title='Count'),
            alt.Tooltip('Percentage:Q', title='Percentage', format='.1%')
        ]
    )

    # Add text labels showing total sample sizes
    text = base.mark_text(
        align='center',
        baseline='bottom',
        dy=-5,
        fontSize=9
    ).encode(
        x='Stage:O',
        y=alt.value(20),  # Fixed position at the top
        text=alt.Text('Total:Q', format=',d'),
        tooltip=[
            alt.Tooltip('Stage:O', title='Stage'),
            alt.Tooltip('Total:Q', title='Total Sample Size', format=',d')
        ]
    )

    # Combine the chart elements
    final_chart = (bars + text).configure_view(
        stroke='lightgray',
        strokeWidth=0.5
    ).configure_axis(
        titleFont='Arial',
        labelFont='Arial',
        grid=True,
        gridColor='lightgray',
        gridOpacity=0.3,
        domain=True,
        domainColor='black',
        domainWidth=0.5,
        labelColor='black',
        titleColor='black'
    ).properties(
        padding={'left': 10, 'top': 30, 'right': 10, 'bottom': 40}
    )

    return final_chart