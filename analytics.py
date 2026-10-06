import numpy as np
from scipy.stats import poisson
import pandas as pd

def calculate_global_strengths(df):
    avg_gf_h = df['GF_H'].sum() / df['GP_H'].sum() if df['GP_H'].sum() > 0 else 1
    avg_gf_a = df['GF_A'].sum() / df['GP_A'].sum() if df['GP_A'].sum() > 0 else 1
    
    strengths = {}
    for _, row in df.iterrows():
        team = row['Team']
        gp_h, gp_a = row['GP_H'], row['GP_A']
        strengths[team] = {
            'off_h': (row['GF_H'] / gp_h) / avg_gf_h if gp_h > 0 else 1,
            'def_h': (row['GA_H'] / gp_h) / avg_gf_a if gp_h > 0 else 1,
            'off_a': (row['GF_A'] / gp_a) / avg_gf_a if gp_a > 0 else 1,
            'def_a': (row['GA_A'] / gp_a) / avg_gf_h if gp_a > 0 else 1
        }
    return strengths, avg_gf_h, avg_gf_a

def predict_match_matrix(home_team, away_team, strengths, avg_h, avg_a, abs_h, abs_a):
    s_h = strengths.get(home_team, {'off_h': 1, 'def_h': 1, 'off_a': 1, 'def_a': 1})
    s_a = strengths.get(away_team, {'off_h': 1, 'def_h': 1, 'off_a': 1, 'def_a': 1})
    
    lambda_h = s_h['off_h'] * s_a['def_a'] * avg_h
    lambda_a = s_a['off_a'] * s_h['def_h'] * avg_a
    
    # Impact des absents (Pénalité offensive)
    penalty_h = min(len(abs_h) * 0.12, 0.40) 
    penalty_a = min(len(abs_a) * 0.12, 0.40)
    
    matrix = np.outer(poisson.pmf(range(9), lambda_h * (1 - penalty_h)), 
                      poisson.pmf(range(9), lambda_a * (1 - penalty_a)))
    return matrix

def analyze_all_markets(matrix, user_odds):
    prob_1 = np.sum(np.tril(matrix, -1))
    prob_N = np.sum(np.diag(matrix))
    prob_2 = np.sum(np.triu(matrix, 1))
    prob_over25 = np.sum([matrix[i,j] for i in range(9) for j in range(9) if i+j > 2.5])
    prob_btts = np.sum(matrix[1:, 1:])
    
    data = [
        ('1', prob_1, user_odds['1']),
        ('N', prob_N, user_odds['N']),
        ('2', prob_2, user_odds['2']),
        ('Over 2.5', prob_over25, user_odds['Over 2.5']),
        ('BTTS (Oui)', prob_btts, user_odds['BTTS (Oui)'])
    ]
    
    results = []
    for market, prob, odd in data:
        value = (prob * odd) - 1
        results.append({'Market': market, 'Cote': odd, 'Prob_IA': prob, 'Value (%)': round(value * 100, 2)})
    return pd.DataFrame(results)
