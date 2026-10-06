import numpy as np
from scipy.stats import poisson
import pandas as pd

def calculate_global_strengths(df):
    avg_h = df['GF_H'].sum() / df['GP_H'].sum() if df['GP_H'].sum() > 0 else 1
    avg_a = df['GF_A'].sum() / df['GP_A'].sum() if df['GP_A'].sum() > 0 else 1
    strengths = {}
    for _, row in df.iterrows():
        team = row['Team']
        strengths[team] = {
            'off_h': (row['GF_H'] / row['GP_H']) / avg_h if row['GP_H'] > 0 else 1,
            'def_h': (row['GA_H'] / row['GP_H']) / avg_a if row['GP_H'] > 0 else 1,
            'off_a': (row['GF_A'] / row['GP_A']) / avg_a if row['GP_A'] > 0 else 1,
            'def_a': (row['GA_A'] / row['GP_A']) / avg_h if row['GP_A'] > 0 else 1
        }
    return strengths, avg_h, avg_a

def predict_match_matrix(home_team, away_team, strengths, avg_h, avg_a, abs_h, abs_a):
    s_h = strengths.get(home_team, {'off_h':1, 'def_h':1, 'off_a':1, 'def_a':1})
    s_a = strengths.get(away_team, {'off_h':1, 'def_h':1, 'off_a':1, 'def_a':1})
    # Pénalité si des absents clés sont détectés (API uniquement)
    l_h = s_h['off_h'] * s_a['def_a'] * avg_h * (1 - min(len(abs_h)*0.12, 0.4))
    l_a = s_a['off_a'] * s_h['def_h'] * avg_a * (1 - min(len(abs_a)*0.12, 0.4))
    return np.outer(poisson.pmf(range(9), l_h), poisson.pmf(range(9), l_a))

def analyze_all_markets(matrix, odds):
    p1, pN, p2 = np.sum(np.tril(matrix, -1)), np.sum(np.diag(matrix)), np.sum(np.triu(matrix, 1))
    po = np.sum([matrix[i,j] for i in range(9) for j in range(9) if i+j > 2.5])
    pb = np.sum(matrix[1:, 1:])
    data = [('1', p1, odds['1']), ('N', pN, odds['N']), ('2', p2, odds['2']), ('Over 2.5', po, odds['Over 2.5']), ('BTTS (Oui)', pb, odds['BTTS (Oui)'])]
    return pd.DataFrame([{'Market': m, 'Cote': c, 'Prob_IA': p, 'Value (%)': round((p*c-1)*100, 2)} for m, p, c in data])
