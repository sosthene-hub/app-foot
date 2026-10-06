import numpy as np
from scipy.stats import poisson
import pandas as pd

def calculate_form_factor(form_str):
    if not form_str or not isinstance(form_str, str): return 1.0
    recent_form = form_str[-5:]
    pts = sum([3 if c=='W' else 1 if c=='D' else 0 for c in recent_form])
    return 1 + (pts - 7.5) / 60 # Impact modéré de la forme

def calculate_global_strengths(df_stats):
    df = df_stats.copy()
    avg_gf_h = df['GF_H'].sum() / df['GP_H'].sum()
    avg_gf_a = df['GF_A'].sum() / df['GP_A'].sum()
    
    df['home_atk'] = (df['GF_H'] / df['GP_H']) / avg_gf_h
    df['home_def'] = (df['GA_H'] / df['GP_H']) / avg_gf_a
    df['away_atk'] = (df['GF_A'] / df['GP_A']) / avg_gf_a
    df['away_def'] = (df['GA_A'] / df['GP_A']) / avg_gf_h
    df['form_factor'] = df['Form'].apply(calculate_form_factor)
    
    return df.set_index('Team'), avg_gf_h, avg_gf_a

def predict_match_matrix(home_team, away_team, strengths, avg_h, avg_a, absentees_h, absentees_a, max_goals=9):
    st_h = strengths.loc[home_team]
    st_a = strengths.loc[away_team]
    
    # Calcul de l'impact des absents (Ex: -5% de force par joueur clé absent)
    # Dans une version pro, on distinguerait Attaquant/Défenseur
    impact_h = 1 - (len(absentees_h) * 0.05)
    impact_a = 1 - (len(absentees_a) * 0.05)
    
    home_expectancy = st_h['home_atk'] * st_a['away_def'] * avg_h * st_h['form_factor'] * max(0.7, impact_h)
    away_expectancy = st_a['away_atk'] * st_h['home_def'] * avg_a * st_a['form_factor'] * max(0.7, impact_a)
    
    home_probs = poisson.pmf(np.arange(max_goals), home_expectancy)
    away_probs = poisson.pmf(np.arange(max_goals), away_expectancy)
    
    return np.outer(home_probs, away_probs)

def analyze_all_markets(matrix, bookmaker_odds):
    prob_1 = np.sum(np.tril(matrix, -1).T)
    prob_N = np.sum(np.diagonal(matrix))
    prob_2 = np.sum(np.triu(matrix, 1).T)
    prob_over25 = 1 - (matrix[0,0] + matrix[0,1] + matrix[0,2] + matrix[1,0] + matrix[1,1] + matrix[2,0])
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
            res.update({'Cote': odd, 'Value (%)': round(value * 100, 2)})
            analysis.append(res)
    return pd.DataFrame(analysis).sort_values('Value (%)', ascending=False)
