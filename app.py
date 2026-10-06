import streamlit as st
import pandas as pd
from scraper import GlobalScraper, fetch_free_data, FREE_LEAGUES
from analytics import calculate_global_strengths, predict_match_matrix, analyze_all_markets

st.set_page_config(page_title="FootValue Pro IA", layout="wide")

st.markdown("<h1 style='text-align: center; color: #2E86C1;'>⚽ FootValue Pro (Analyseur Expert)</h1>", unsafe_allow_html=True)

if 'df_stats' not in st.session_state: st.session_state.df_stats = None
if 'api_key' not in st.session_state: st.session_state.api_key = ""

with st.sidebar:
    st.header("🔑 Configuration")
    api_key = st.text_input("Clé API-Sports (Optionnel)", type="password")
    if api_key: st.session_state.api_key = api_key
    
    st.divider()
    st.subheader("🌐 Mode Gratuit")
    free_league = st.selectbox("Choisir une ligue", list(FREE_LEAGUES.keys()))
    if st.button("🔄 Charger Ligue Gratuite"):
        st.session_state.df_stats = fetch_free_data(FREE_LEAGUES[free_league])
        st.session_state.current_league_id = 0
        st.success("Données CSV chargées")

    if st.session_state.api_key:
        st.divider()
        st.subheader("🚀 Mode API Premium")
        scraper = GlobalScraper(st.session_state.api_key)
        try:
            countries = scraper.get_countries()
            if countries:
                c_names = [c['name'] for c in countries]
                sel_country = st.selectbox("Pays", c_names, index=c_names.index('France') if 'France' in c_names else 0)
                leagues = scraper.get_leagues(sel_country)
                if leagues:
                    l_map = {l['league']['name']: l['league']['id'] for l in leagues}
                    sel_div = st.selectbox("Division", list(l_map.keys()))
                    sel_season = st.selectbox("Saison", [2024, 2023])
                    if st.button("🚀 CHARGER VIA API"):
                        data = scraper.get_standings(l_map[sel_div], sel_season)
                        if isinstance(data, pd.DataFrame):
                            st.session_state.df_stats = data
                            st.session_state.current_league_id = l_map[sel_div]
                            st.session_state.current_season = sel_season
                            st.success("Données API chargées")
        except:
            st.error("Erreur avec la clé API.")

if st.session_state.df_stats is not None:
    df = st.session_state.df_stats
    teams = sorted(df['Team'].unique())
    col_m, col_o = st.columns([2, 1])
    
    with col_m:
        st.subheader("📊 Match & Compo")
        c_h, c_a = st.columns(2)
        home = c_h.selectbox("🏠 Domicile", teams)
        away = c_a.selectbox("🚀 Extérieur", teams, index=1 if len(teams)>1 else 0)
        
        id_h = df[df['Team'] == home]['ID'].values[0]
        id_a = df[df['Team'] == away]['ID'].values[0]
        
        abs_h, abs_a = [], []
        if st.session_state.api_key and id_h != 0:
            scr = GlobalScraper(st.session_state.api_key)
            with st.spinner("Analyse API des blessés..."):
                k_h = scr.get_key_players(st.session_state.current_league_id, st.session_state.current_season, id_h)
                i_h = scr.get_absentees(st.session_state.current_league_id, st.session_state.current_season, id_h)
                abs_h = [p for p in i_h if p in k_h]
                k_a = scr.get_key_players(st.session_state.current_league_id, st.session_state.current_season, id_a)
                i_a = scr.get_absentees(st.session_state.current_league_id, st.session_state.current_season, id_a)
                abs_a = [p for p in i_a if p in k_a]
        
        c_h.info(f"**Absents :** {', '.join(abs_h) if abs_h else 'Aucun'}")
        c_a.info(f"**Absents :** {', '.join(abs_a) if abs_a else 'Aucun'}")

    with col_o:
        st.subheader("⚖️ Vos Cotes")
        c1 = st.number_input("Cote 1", 1.01, 50.0, 2.0)
        cN = st.number_input("Cote N", 1.01, 50.0, 3.0)
        c2 = st.number_input("Cote 2", 1.01, 50.0, 3.0)
        cO = st.number_input("Cote Over 2.5", 1.01, 50.0, 1.85)
        cB = st.number_input("Cote BTTS", 1.01, 50.0, 1.75)

    if st.button("🔍 ANALYSER LA VALUE"):
        strengths, avg_h, avg_a = calculate_global_strengths(df)
        matrix = predict_match_matrix(home, away, strengths, avg_h, avg_a, abs_h, abs_a)
        res = analyze_all_markets(matrix, {'1':c1, 'N':cN, '2':c2, 'Over 2.5':cO, 'BTTS (Oui)':cB})
        
        def color_val(v):
            if isinstance(v, (int, float)):
                return f"color: {'#27AE60' if v > 0 else '#E74C3C'}; font-weight: bold;"
            return ""

        st.dataframe(res.style.map(color_val, subset=['Value (%)']), use_container_width=True)
        
        if df['GP_H'].iloc[0] < 5:
            st.warning("⚠️ Prudence : Peu de matchs joués cette saison.")
