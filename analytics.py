import numpy as np
from scipy.stats import poisson
import pandas as pd

def calculate_global_strengths(df):
    """Calcule la force offensive et défensive de chaque équipe"""
    # Calcul des moyennes globales de la ligue
    total_gp_h = df['GP_H'].sum()
    total_gp_a = df['GP_A'].sum()
    
    if total_gp_h == 0 or total_gp_a == 0:
        return {}, 1.0, 1.0
        
    avg_gf_h = df['GF_H'].sum() / total_gp_h
    avg_gf_a = df['GF_A'].sum() / total_gp_a
    
    strengths = {}
    for _, row in df.iterrows():
        team = row['Team']
        # Calcul des ratios (Force)
        s_off_h = (row['GF_H'] / row['GP_H']) / avg_gf_h if row['GP_H'] > 0 else 1
        s_def_h = (row['GA_H'] / row['GP_H']) / avg_gf_a if row['GP_H'] > 0 else 1
        s_off_a = (row['GF_A'] / row['GP_A']) / avg_gf_a if row['GP_A'] > 0 else 1
        s_def_a = (row['GA_A'] / row['GP_A']) / avg_gf_h if row['GP_A'] > 0 else 1
        
        strengths[team] = {
            'off_h': s_off_h, 'def_h': s_def_h,
            'off_a': s_off_a, 'def_a': s_def_a
        }
    return strengths, avg_gf_h, avg_gf_a

def predict_match_matrix(home_team, away_team, strengths, avg_h, avg_a, abs_h, abs_a):
    """Génère la matrice de probabilités de scores (Loi de Poisson)"""
    # Récupération des forces
    s_h = strengths.get(home_team, {'off_h': 1, 'def_h': 1, 'off_a': 1, 'def_a': 1})
    s_a = strengths.get(away_team, {'off_h': 1, 'def_h': 1, 'off_a': 1, 'def_a': 1})
    
    # Calcul de Lambda (espérance de buts)
    lambda_h = s_h['off_h'] * s_a['def_a'] * avg_h
    lambda_a = s_a['off_a'] * s_h['def_h'] * avg_a
    
    # --- IMPACT DES ABSENTS ---
    # On réduit le potentiel offensif de 10% par joueur clé absent (max 30%)
    penalty_h = min(len(abs_h) * 0.10, 0.30)
    penalty_a = min(len(abs_a) * 0.10, 0.30)
    
    lambda_h *= (1 - penalty_h)
    lambda_a *= (1 - penalty_a)
    
    # Création de la matrice 9x9 (de 0 à 8 buts pour chaque équipe)
    matrix = np.outer(
        poisson.pmf(range(9), lambda_h),
        poisson.pmf(range(9), lambda_a)
    )
    return matrix

def analyze_all_markets(matrix, user_odds):
    """Calcule les probabilités finales et la value pour chaque pari"""
    prob_1 = np.sum(np.tril(matrix, -1)) # Somme triangle bas (1)
    prob_N = np.sum(np.diag(matrix))     # Somme diagonale (N)
    prob_2 = np.sum(np.triu(matrix, 1))  # Somme triangle haut (2)
    
    # Over 2.5 buts (Somme des scores où i + j > 2)
    prob_over25 = 0
    for i in range(9):
        for j in range(9):
            if i + j > 2.5:
                prob_over25 += matrix[i, j]
                
    # BTTS (Les deux marquent : score min 1-1)
    prob_btts = np.sum(matrix[1:, 1:])
    
    markets = [
        {'Market': '1', 'Prob_IA': prob_1, 'Cote': user_odds.get('1', 1.0)},
        {'Market': 'N', 'Prob_IA': prob_N, 'Cote': user_odds.get('N', 1.0)},
        {'Market': '2', 'Prob_IA': prob_2, 'Cote': user_odds.get('2', 1.0)},
        {'Market': 'Over 2.5', 'Prob_IA': prob_over25, 'Cote': user_odds.get('Over 2.5', 1.0)},
        {'Market': 'BTTS (Oui)', 'Prob_IA': prob_btts, 'Cote': user_odds.get('BTTS (Oui)', 1.0)}
    ]
    
    results = []
    for m in markets:
        # Formule de la Value : (Probabilité * Cote) - 1
        val = (m['Prob_IA'] * m['Cote']) - 1
        m['Value (%)'] = round(val * 100, 2)
        results.append(m)
        
    return pd.DataFrame(results)
