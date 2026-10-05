import streamlit as st
from scraper import GlobalScraper, fetch_free_data, FREE_LEAGUES
from analytics import calculate_global_strengths, predict_match_matrix, analyze_all_markets

st.set_page_config(page_title="FootValue API-Sports", layout="wide")
st.title("⚽ FootValue Pro (API-Sports)")

# --- INITIALISATION ---
if 'df_stats' not in st.session_state:
    st.session_state.df_stats = None

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("🔑 Configuration")
    api_key = st.text_input("Clé API-Sports", type="password")
    st.divider()
    st.info("Mode Gratuit (sans clé) :")
    sel_free = st.selectbox("Choisir une ligue Europe", list(FREE_LEAGUES.keys()))
    if st.button("🔄 Charger Mode Gratuit"):
        with st.spinner("Chargement..."):
            st.session_state.df_stats = fetch_free_data(FREE_LEAGUES[sel_free])
            if st.session_state.df_stats is not None:
                st.success("Données CSV chargées !")

if api_key:
    scraper = GlobalScraper(api_key)
    countries = scraper.get_countries()
    
    if countries:
        st.sidebar.success("✅ Connexion API OK")
        c_names = [c['name'] for c in countries]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            default_idx = c_names.index('France') if 'France' in c_names else 0
            sel_country = st.selectbox("Pays", c_names, index=default_idx)
        
        leagues = scraper.get_leagues(sel_country)
        if leagues:
            league_map = {l['league']['name']: l['league']['id'] for l in leagues}
            with col2:
                sel_div = st.selectbox("Division", list(league_map.keys()))
            
            with col3:
                sel_season = st.selectbox("Saison", [2024, 2023], index=0)
            
            if st.button("🚀 CHARGER LES STATISTIQUES"):
                with st.spinner("Récupération des données API..."):
                    data = scraper.get_standings(league_map[sel_div], sel_season)
                    if data is not None:
                        st.session_state.df_stats = data
                        st.success(f"Stats de {sel_div} ({sel_season}) récupérées !")
                    else:
                        st.error(f"L'API n'a pas renvoyé de données pour {sel_div} en {sel_season}. Essayez 2023.")
    else:
        st.sidebar.error("❌ Clé API invalide")

# --- ANALYSE ---
if st.session_state.df_stats is not None:
    df = st.session_state.df_stats
    teams = sorted(df['Team'].unique())
    
    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("📊 Configuration du match")
        h_col, a_col = st.columns(2)
        home = h_col.selectbox("🏠 Domicile", teams)
        away = a_col.selectbox("🚀 Extérieur", teams, index=1 if len(teams)>1 else 0)
        
        st.subheader("⚖️ Cotes Bookmaker")
        c1, c2, c3 = st.columns(3)
        o1 = c1.number_input("Cote 1", value=2.0)
        oN = c2.number_input("Cote N", value=3.0)
        o2 = c3.number_input("Cote 2", value=3.0)
        
        c4, c5 = st.columns(2)
        oOver = c4.number_input("Cote Over 2.5", value=1.85)
        oBTTS = c5.number_input("Cote BTTS (Oui)", value=1.75)

    with col_b:
        st.subheader("🎯 Prédiction IA")
        if st.button("🔍 ANALYSER LA VALUE"):
            try:
                strengths, avg_h, avg_a = calculate_global_strengths(df)
                matrix = predict_match_matrix(home, away, strengths, avg_h, avg_a)
                results = analyze_all_markets(matrix, {'1': o1, 'N': oN, '2': o2, 'Over 2.5': oOver, 'BTTS (Oui)': oBTTS})
                
                results['IA Proba (%)'] = (results['Prob_IA'] * 100).round(1)
                best = results.iloc[0]
                
                st.metric("Meilleur Conseil", best['Market'], f"ROI: {best['Value (%)']}%")
                st.dataframe(results[['Market', 'Cote', 'IA Proba (%)', 'Value (%)']], use_container_width=True)
            except Exception as e:
                st.error(f"Erreur d'analyse : {e}")
