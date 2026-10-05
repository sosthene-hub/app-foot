import streamlit as st
from scraper import GlobalScraper, fetch_free_data, FREE_LEAGUES
from analytics import calculate_global_strengths, predict_match_matrix, analyze_all_markets
import pandas as pd

st.set_page_config(page_title="FootValue Pro", layout="wide")
st.title("⚽ FootValue Pro (Analyseur de Paris)")

if 'df_stats' not in st.session_state:
    st.session_state.df_stats = None

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("🔑 Connexion")
    api_key = st.text_input("Clé API-Sports", type="password")
    st.divider()
    st.info("Mode Gratuit (Europe 24/25)")
    sel_free = st.selectbox("Ligue", list(FREE_LEAGUES.keys()))
    if st.button("🔄 Charger Mode Gratuit"):
        st.session_state.df_stats = fetch_free_data(FREE_LEAGUES[sel_free])

if api_key:
    scraper = GlobalScraper(api_key)
    countries = scraper.get_countries()
    
    if countries:
        c_names = [c['name'] for c in countries]
        col1, col2, col3 = st.columns(3)
        with col1:
            default_country = 'France' if 'France' in c_names else c_names[0]
            sel_country = st.selectbox("Pays", c_names, index=c_names.index(default_country))
        
        leagues = scraper.get_leagues(sel_country)
        if leagues:
            league_map = {l['league']['name']: l['league']['id'] for l in leagues}
            with col2:
                sel_div = st.selectbox("Division", list(league_map.keys()))
            with col3:
                sel_season = st.selectbox("Saison", [2024, 2023, 2022])
            
            if st.button("🚀 CHARGER LES STATISTIQUES"):
                with st.spinner("Récupération des données API..."):
                    result = scraper.get_standings(league_map[sel_div], sel_season)
                    
                    if isinstance(result, pd.DataFrame):
                        st.session_state.df_stats = result
                        st.success(f"✅ {len(result)} équipes prêtes pour l'analyse !")
                    else:
                        st.error(f"{result}")
    else:
        st.sidebar.error("❌ Clé API invalide ou quota épuisé.")

# --- ZONE D'ANALYSE ---
if st.session_state.df_stats is not None:
    df = st.session_state.df_stats
    teams = sorted(df['Team'].unique())
    
    st.divider()
    c_match, c_odds = st.columns(2)
    
    with c_match:
        st.subheader("📊 Match")
        home = st.selectbox("🏠 Domicile", teams)
        away = st.selectbox("🚀 Extérieur", teams, index=1 if len(teams)>1 else 0)
    
    with c_odds:
        st.subheader("⚖️ Cotes Bookmaker")
        o1, oN, o2 = st.columns(3)
        c1 = o1.number_input("Cote 1", value=2.0, step=0.01)
        cN = oN.number_input("Cote N", value=3.0, step=0.01)
        c2 = o2.number_input("Cote 2", value=3.0, step=0.01)
        
        o_v, o_b = st.columns(2)
        cOver = o_v.number_input("Cote Over 2.5", value=1.85, step=0.01)
        cBTTS = o_b.number_input("Cote BTTS (Oui)", value=1.75, step=0.01)

    if st.button("🔍 ANALYSER LA VALUE"):
        try:
            # Calcul des forces
            strengths, avg_h, avg_a = calculate_global_strengths(df)
            
            # Prédiction
            matrix = predict_match_matrix(home, away, strengths, avg_h, avg_a)
            
            # Analyse des marchés
            results = analyze_all_markets(matrix, {'1': c1, 'N': cN, '2': c2, 'Over 2.5': cOver, 'BTTS (Oui)': cBTTS})
            
            results['IA Proba (%)'] = (results['Prob_IA'] * 100).round(1)
            
            st.write(f"### 🎯 Analyse : {home} vs {away}")
            
            # Affichage du meilleur choix
            best = results.sort_values('Value (%)', ascending=False).iloc[0]
            if best['Value (%)'] > 0:
                st.success(f"🔥 VALUE DÉTECTÉE : {best['Market']} à {best['Cote']} (ROI attendu : {best['Value (%)']}%)")
            else:
                st.warning("Aucune value nette détectée sur ces cotes.")
                
            st.dataframe(results[['Market', 'Cote', 'IA Proba (%)', 'Value (%)']], use_container_width=True)
            
        except Exception as e:
            st.error(f"Erreur d'analyse : {e}")
