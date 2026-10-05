import numpy as np
from scipy.stats import poisson
import pandas as pd

def calculate_global_strengths(df_stats):
    # Calcul des moyennes de la ligue
    avg_gf_h = df_stats['GF_H'].sum() / df_stats['GP_H'].sum()
    avg_gf_a = df_stats['GF_A'].sum() / df_stats['GP_A'].sum()

    # Calcul des forces relatives
    df_stats['home_atk'] = (df_stats['GF_H'] / df_stats['GP_H']) / avg_gf_h
    df_stats['home_def'] = (df_stats['GA_H'] / df_stats['GP_H']) / avg_gf_a
    df_stats['away_atk'] = (df_stats['GF_A'] / df_stats['GP_A']) / avg_gf_a
    df_stats['away_def'] = (df_stats['GA_A'] / df_stats['GP_A']) / avg_gf_h
    
    return df_stats.set_index('Team'), avg_gf_h, avg_gf_a

def predict_match_matrix(home_team, away_team, strengths, avg_h, avg_a, max_goals=9):
    st_h = strengths.loc[home_team]
    st_a = strengths.loc[away_team]

    home_expectancy = st_h['home_atk'] * st_a['away_def'] * avg_h
    away_expectancy = st_a['away_atk'] * st_h['home_def'] * avg_a

    home_probs = poisson.pmf(np.arange(max_goals), home_expectancy)
    away_probs = poisson.pmf(np.arange(max_goals), away_expectancy)

    return np.outer(home_probs, away_probs)

def analyze_all_markets(matrix, bookmaker_odds):
    prob_1 = np.sum(np.tril(matrix, -1).T)
    prob_N = np.sum(np.diagonal(matrix))
    prob_2 = np.sum(np.triu(matrix, 1).T)
    
    prob_over25 = 1 - np.sum(matrix[0,0] + matrix[0,1] + matrix[0,2] + matrix[1,0] + matrix[1,1] + matrix[2,0])
    prob_btts = 1 - (np.sum(matrix[0, :]) + np.sum(matrix[:, 0]) - matrix[0,0])

    results = [
        {'Market': '1', 'Prob_IA': prob_1},
        {'Market': 'N', 'Prob_IA': prob_N},
        {'Market': '2', 'Prob_IA': prob_2},
        {'Market': 'Over 2.5', 'Prob_IA': prob_over25},
        {'Market': 'BTTS (Oui)', 'Prob_IA': prob_btts}
    ]

    analysis = []
    for res in results:
        if res['Market'] in bookmaker_odds:
            odd = bookmaker_odds[res['Market']]
            value = (res['Prob_IA'] * odd) - 1
            res['Cote'] = odd
            res['Value (%)'] = round(value * 100, 2)
            analysis.append(res)

    return pd.DataFrame(analysis).sort_values(by='Value (%)', ascending=False)
