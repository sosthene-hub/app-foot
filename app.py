import streamlit as st
from scraper import GlobalScraper, fetch_free_data, FREE_LEAGUES
from analytics import calculate_global_strengths, predict_match_matrix, analyze_all_markets

st.set_page_config(page_title="FootValue Pro", layout="centered")
st.title("⚽ FootValue Pro")

if 'df_stats' not in st.session_state:
    st.session_state.df_stats = None

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("🔑 Config API")
    api_key = st.text_input("Clé RapidAPI", type="password")

# --- CHOIX DU MODE ---
if not api_key:
    st.info("💡 Mode Europe Gratuit. Entre ta clé à gauche pour le mode Monde.")
    sel_league = st.selectbox("Championnat Europe", list(FREE_LEAGUES.keys()))
    if st.button("🔄 Charger Europe"):
        st.session_state.df_stats = fetch_free_data(FREE_LEAGUES[sel_league])
        st.success("Données Europe prêtes.")
else:
    scraper = GlobalScraper(api_key)
    countries = scraper.get_countries()
    if countries:
        c_names = [c['name'] for c in countries]
        col1, col2 = st.columns(2)
        with col1:
            sel_country = st.selectbox("Pays", c_names, index=c_names.index('France') if 'France' in c_names else 0)
        
        leagues = scraper.get_leagues(sel_country)
        if leagues:
            league_map = {l['league']['name']: l['league']['id'] for l in leagues}
            with col2:
                sel_div = st.selectbox("Division", list(league_map.keys()))
            
            if st.button("🚀 Charger Stats API"):
                st.session_state.df_stats = scraper.get_standings(league_map[sel_div])
                st.success("Données API Mondiales prêtes.")
    else:
        st.error("Clé API invalide ou inactive.")

# --- ANALYSE ---
if st.session_state.df_stats is not None:
    df = st.session_state.df_stats
    teams = sorted(df['Team'].unique())
    
    st.divider()
    h_col, a_col = st.columns(2)
    home = h_col.selectbox("🏠 Domicile", teams)
    away = a_col.selectbox("🚀 Extérieur", teams, index=1 if len(teams)>1 else 0)

    # Duel des forces
    strengths, avg_h, avg_a = calculate_global_strengths(df)
    
    st.subheader("⚖️ Cotes")
    c1, c2, c3 = st.columns(3)
    o1 = c1.number_input("1", value=2.0)
    oN = c2.number_input("N", value=3.0)
    o2 = c3.number_input("2", value=3.0)
    
    c4, c5 = st.columns(2)
    oOver = c4.number_input("Over 2.5", value=1.85)
    oBTTS = c5.number_input("BTTS", value=1.75)

    if st.button("🔍 ANALYSER"):
        try:
            matrix = predict_match_matrix(home, away, strengths, avg_h, avg_a)
            results = analyze_all_markets(matrix, {'1': o1, 'N': oN, '2': o2, 'Over 2.5': oOver, 'BTTS (Oui)': oBTTS})
            results['IA Proba (%)'] = (results['Prob_IA'] * 100).round(1)
            st.success(f"Conseil : {results.iloc[0]['Market']} (ROI: {results.iloc[0]['Value (%)']}%)")
            st.dataframe(results[['Market', 'Cote', 'IA Proba (%)', 'Value (%)']])
        except Exception as e:
            st.error(f"Erreur de calcul : {e}")
