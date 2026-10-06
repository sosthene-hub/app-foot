import streamlit as st
import pandas as pd
from scraper import GlobalScraper, fetch_free_data
from analytics import calculate_global_strengths, predict_match_matrix, analyze_all_markets

st.set_page_config(page_title="FootValue Pro IA", layout="wide")

if 'df_stats' not in st.session_state: st.session_state.df_stats = None
if 'api_key' not in st.session_state: st.session_state.api_key = ""

with st.sidebar:
    st.header("🔑 Configuration")
    api_key = st.text_input("Clé API-Sports", type="password")
    if api_key: st.session_state.api_key = api_key
    st.divider()
    if st.button("🔄 Mode Gratuit (Europe)"):
        st.session_state.df_stats = fetch_free_data("F1")
        st.session_state.current_league_id = 0

    if st.session_state.api_key:
        scraper = GlobalScraper(st.session_state.api_key)
        countries = scraper.get_countries()
        if countries:
            c_names = [c['name'] for c in countries]
            sel_country = st.selectbox("Pays", c_names, index=c_names.index('France') if 'France' in c_names else 0)
            leagues = scraper.get_leagues(sel_country)
            if leagues:
                league_map = {l['league']['name']: l['league']['id'] for l in leagues}
                sel_div = st.selectbox("Division", list(league_map.keys()))
                sel_season = st.selectbox("Saison", [2024, 2023])
                if st.button("🚀 CHARGER LES DONNÉES API"):
                    data = scraper.get_standings(league_map[sel_div], sel_season)
                    if isinstance(data, pd.DataFrame):
                        st.session_state.df_stats = data
                        st.session_state.current_league_id = league_map[sel_div]
                        st.session_state.current_season = sel_season
                        st.success("Données chargées !")

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
            with st.spinner("Analyse des absents..."):
                key_h = scr.get_key_players(st.session_state.current_league_id, st.session_state.current_season, id_h)
                inj_h = scr.get_absentees(st.session_state.current_league_id, st.session_state.current_season, id_h)
                abs_h = [p for p in inj_h if p in key_h]
                
                key_a = scr.get_key_players(st.session_state.current_league_id, st.session_state.current_season, id_a)
                inj_a = scr.get_absentees(st.session_state.current_league_id, st.session_state.current_season, id_a)
                abs_a = [p for p in inj_a if p in key_a]
        
        c_h.write(f"**Absents Clés :** {', '.join(abs_h) if abs_h else 'Aucun'}")
        c_a.write(f"**Absents Clés :** {', '.join(abs_a) if abs_a else 'Aucun'}")

    with col_o:
        st.subheader("⚖️ Cotes")
        c1 = st.number_input("Cote 1", 1.01, 50.0, 2.0)
        cN = st.number_input("Cote N", 1.01, 50.0, 3.0)
        c2 = st.number_input("Cote 2", 1.01, 50.0, 3.0)
        cOver = st.number_input("Cote Over 2.5", 1.01, 50.0, 1.85)
        cBTTS = st.number_input("Cote BTTS (Oui)", 1.01, 50.0, 1.75)

    if st.button("🔍 ANALYSER LA VALUE"):
        strengths, avg_h, avg_a = calculate_global_strengths(df)
        matrix = predict_match_matrix(home, away, strengths, avg_h, avg_a, abs_h, abs_a)
        res = analyze_all_markets(matrix, {'1':c1, 'N':cN, '2':c2, 'Over 2.5':cOver, 'BTTS (Oui)':cBTTS})
        res['IA Proba (%)'] = (res['Prob_IA'] * 100).round(1)
        st.dataframe(res[['Market', 'Cote', 'IA Proba (%)', 'Value (%)']], use_container_width=True)
