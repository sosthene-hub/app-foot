import streamlit as st
from scraper import GlobalScraper
from analytics import calculate_global_strengths, predict_match_matrix, analyze_all_markets
import pandas as pd

st.set_page_config(page_title="FootValue Pro IA", layout="wide")

def display_form(form_str):
    if not form_str: return "N/A"
    return form_str.replace('W', '✅').replace('D', '➖').replace('L', '❌')

st.title("⚽ FootValue Pro (Analyse Avancée)")

if 'df_stats' not in st.session_state: st.session_state.df_stats = None
if 'api_key' not in st.session_state: st.session_state.api_key = ""

with st.sidebar:
    st.header("🔑 Configuration")
    api_key = st.text_input("Clé API-Sports", type="password")
    if api_key: st.session_state.api_key = api_key

if st.session_state.api_key:
    scraper = GlobalScraper(st.session_state.api_key)
    countries = scraper.get_countries()
    if countries:
        c_names = [c['name'] for c in countries]
        col1, col2, col3 = st.columns(3)
        with col1: sel_country = st.selectbox("Pays", c_names, index=c_names.index('France') if 'France' in c_names else 0)
        leagues = scraper.get_leagues(sel_country)
        if leagues:
            league_map = {l['league']['name']: l['league']['id'] for l in leagues}
            with col2: sel_div = st.selectbox("Division", list(league_map.keys()))
            with col3: sel_season = st.selectbox("Saison", [2024, 2023])
            
            if st.button("🚀 CHARGER LES DONNÉES"):
                st.session_state.df_stats = scraper.get_standings(league_map[sel_div], sel_season)
                st.session_state.current_league_id = league_map[sel_div]
                st.session_state.current_season = sel_season

if st.session_state.df_stats is not None:
    df = st.session_state.df_stats
    teams = sorted(df['Team'].unique())
    
    st.divider()
    col_m, col_o = st.columns([2, 1])
    
    with col_m:
        st.subheader("📊 Match & Compo")
        c_h, c_a = st.columns(2)
        home = c_h.selectbox("🏠 Domicile", teams)
        away = c_a.selectbox("🚀 Extérieur", teams, index=1 if len(teams)>1 else 0)
        
        # Récupération des IDs d'équipes
        id_h = df[df['Team'] == home]['ID'].values[0]
        id_a = df[df['Team'] == away]['ID'].values[0]
        
        # Analyse des absents
        with st.spinner("Analyse des compositions..."):
            key_h = scraper.get_key_players(st.session_state.current_league_id, st.session_state.current_season, id_h)
            all_inj_h = scraper.get_absentees(st.session_state.current_league_id, st.session_state.current_season, id_h)
            abs_h = [p for p in all_inj_h if p in key_h]
            
            key_a = scraper.get_key_players(st.session_state.current_league_id, st.session_state.current_season, id_a)
            all_inj_a = scraper.get_absentees(st.session_state.current_league_id, st.session_state.current_season, id_a)
            abs_a = [p for p in all_inj_a if p in key_a]

        c_h.write(f"**Absents Clés :** {', '.join(abs_h) if abs_h else 'Aucun'}")
        c_a.write(f"**Absents Clés :** {', '.join(abs_a) if abs_a else 'Aucun'}")

    with col_o:
        st.subheader("⚖️ Cotes")
        c1 = st.number_input("Cote 1", value=2.0)
        cN = st.number_input("Cote N", value=3.0)
        c2 = st.number_input("Cote 2", value=3.0)
        cOver = st.number_input("Cote Over 2.5", value=1.85)
        cBTTS = st.number_input("Cote BTTS (Oui)", value=1.75)

    if st.button("🔍 ANALYSER AVEC IA COMPOSITION"):
        strengths, avg_h, avg_a = calculate_global_strengths(df)
        matrix = predict_match_matrix(home, away, strengths, avg_h, avg_a, abs_h, abs_a)
        results = analyze_all_markets(matrix, {'1': c1, 'N': cN, '2': c2, 'Over 2.5': cOver, 'BTTS (Oui)': cBTTS})
        
        results['IA Proba (%)'] = (results['Prob_IA'] * 100).round(1)
        st.dataframe(results[['Market', 'Cote', 'IA Proba (%)', 'Value (%)']], use_container_width=True)
