import streamlit as st
import pandas as pd
from scraper import GlobalScraper, FREE_LEAGUES, fetch_free_data
from analytics import calculate_global_strengths, predict_match_matrix, analyze_all_markets

st.set_page_config(page_title="FootValue Pro", layout="centered")

# --- STYLE CSS PERSONNALISÉ ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 3.5em; background-color: #007bff; color: white; font-weight: bold; }
    [data-testid="stMetricValue"] { color: #2ecc71; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ FootValue Pro")

# --- GESTION DES DONNÉES ---
if 'df_stats' not in st.session_state:
    st.session_state.df_stats = None

mode = st.radio("Mode de données", ["Europe (Gratuit)", "Monde (Clé API)"], horizontal=True)

if mode == "Europe (Gratuit)":
    sel_league = st.selectbox("Choisir une ligue européenne", list(FREE_LEAGUES.keys()))
    if st.button("🔄 Charger les Stats Europe"):
        df_stats = fetch_free_data(FREE_LEAGUES[sel_league])
        if df_stats is not None:
            st.session_state.df_stats = df_stats
            st.success("Données Europe chargées !")
else:
    api_key = st.sidebar.text_input("Clé API-Football", type="password")
    if api_key: st.info("Mode Monde activé.")

# --- FONCTION DE COLORATION ---
def style_value(val):
    color = '#27ae60' if val > 0 else '#e74c3c' # Vert si positif, Rouge si négatif
    return f'color: {color}; font-weight: bold;'

# --- ANALYSE DU MATCH ---
if st.session_state.df_stats is not None:
    df = st.session_state.df_stats
    teams = sorted(df['Team'].unique())
    
    st.divider()
    col_h, col_a = st.columns(2)
    with col_h: home = st.selectbox("🏠 Domicile", teams)
    with col_a: away = st.selectbox("🚀 Extérieur", teams, index=1 if len(teams)>1 else 0)

    # Affichage des forces Attaque/Défense
    strengths, avg_h, avg_a = calculate_global_strengths(df)
    s_h = strengths.loc[home]
    s_a = strengths.loc[away]
    
    with st.expander("🛡️ Voir le duel des défenses"):
        c1, c2 = st.columns(2)
        c1.metric(f"Défense {home}", round(s_h['home_def'], 2), delta=None)
        c2.metric(f"Défense {away}", round(s_a['away_def'], 2), delta=None)
        st.caption("Plus le chiffre est BAS, plus la défense est SOLIDE.")

    st.subheader("⚖️ Cotes Bookmaker")
    c1, c2, c3 = st.columns(3)
    o1 = c1.number_input("Cote 1", value=2.0)
    oN = c2.number_input("Cote N", value=3.0)
    o2 = c3.number_input("Cote 2", value=3.0)
    
    c4, c5 = st.columns(2)
    oOver = c4.number_input("Cote Over 2.5", value=1.85)
    oBTTS = c5.number_input("Cote BTTS (Oui)", value=1.75)

    if st.button("🔍 ANALYSER LA VALUE"):
        try:
            matrix = predict_match_matrix(home, away, strengths, avg_h, avg_a)
            odds = {'1': o1, 'N': oN, '2': o2, 'Over 2.5': oOver, 'BTTS (Oui)': oBTTS}
            results = analyze_all_markets(matrix, odds)
            results['IA Proba (%)'] = (results['Prob_IA'] * 100).round(1)
            
            # Application des couleurs au tableau
            styled_results = results[['Market', 'Cote', 'IA Proba (%)', 'Value (%)']].style.map(
                style_value, subset=['Value (%)']
            )
            
            best = results.iloc[0]
            if best['Value (%)'] > 0:
                st.success(f"✅ CONSEIL RENTABLE : {best['Market']} (ROI: {best['Value (%)']}%)")
            else:
                st.warning("⚠️ AUCUNE VALUE : Le bookmaker a bien ajusté ses cotes.")
            
            st.dataframe(styled_results, use_container_width=True)
            
            for _, row in results.iterrows():
                with st.expander(f"{row['Market']} | Proba: {row['IA Proba (%)']}%"):
                    st.write(f"Cote minimale rentable : **{round(1/row['Prob_IA'], 2)}**")
        except Exception as e:
            st.error(f"Erreur : {e}")
else:
    st.info("Chargez une ligue pour commencer.")
