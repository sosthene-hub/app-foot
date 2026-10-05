import streamlit as st
from scraper import GlobalScraper, fetch_free_data, FREE_LEAGUES
from analytics import calculate_global_strengths, predict_match_matrix, analyze_all_markets

st.set_page_config(page_title="FootValue World", layout="centered")
st.title("🌎 FootValue World IA")

# --- BARRE LATÉRALE : CLÉ API ---
with st.sidebar:
    st.header("🔑 Accès API")
    api_key = st.text_input("Entre ta clé RapidAPI", type="password")
    if api_key:
        st.success("API Connectée")
    else:
        st.warning("Mode Europe Gratuit uniquement")

# --- SÉLECTION DES DONNÉES ---
df_stats = None

if not api_key:
    # Mode Gratuit Europe
    sel_league = st.selectbox("Championnat (Europe Gratuit)", list(FREE_LEAGUES.keys()))
    if st.button("🔄 Charger Europe"):
        st.session_state.df_stats = fetch_free_data(FREE_LEAGUES[sel_league])
else:
    # Mode API MONDE
    scraper = GlobalScraper(api_key)
    countries = scraper.get_countries()
    
    if countries:
        c_names = [c['name'] for c in countries]
        col1, col2 = st.columns(2)
        with col1:
            sel_country = st.selectbox("Pays", c_names, index=c_names.index('France') if 'France' in c_names else 0)
        
        leagues = scraper.get_leagues(sel_country)
        league_map = {l['league']['name']: l['league']['id'] for l in leagues}
        with col2:
            sel_div = st.selectbox("Division", list(league_map.keys()))
        
        if st.button("🚀 Charger Stats API"):
            with st.spinner("Récupération temps réel..."):
                st.session_state.df_stats = scraper.get_standings(league_map[sel_div])
    else:
        st.error("Clé API invalide ou inactive.")

# --- ANALYSE ---
if 'df_stats' in st.session_state and st.session_state.df_stats is not None:
    df = st.session_state.df_stats
    teams = sorted(df['Team'].unique())
    
    st.divider()
    col_h, col_a = st.columns(2)
    home = col_h.selectbox("🏠 Domicile", teams)
    away = col_a.selectbox("🚀 Extérieur", teams, index=1 if len(teams)>1 else 0)

    # Duel des forces
    strengths, avg_h, avg_a = calculate_global_strengths(df)
    s_h, s_a = strengths.loc[home], strengths.loc[away]
    with st.expander("🛡️ Voir les Défenses"):
        st.write(f"Défense {home}: **{round(s_h['home_def'], 2)}**")
        st.write(f"Défense {away}: **{round(s_a['away_def'], 2)}**")

    st.subheader("⚖️ Cotes Bookmaker")
    c1, c2, c3 = st.columns(3)
    o1 = c1.number_input("Cote 1", value=2.0)
    oN = c2.number_input("Cote N", value=3.0)
    o2 = c3.number_input("Cote 2", value=3.0)
    
    c4, c5 = st.columns(2)
    oOver = c4.number_input("Over 2.5", value=1.85)
    oBTTS = c5.number_input("BTTS", value=1.75)

    if st.button("🔍 ANALYSER"):
        matrix = predict_match_matrix(home, away, strengths, avg_h, avg_a)
        results = analyze_all_markets(matrix, {'1': o1, 'N': oN, '2': o2, 'Over 2.5': oOver, 'BTTS (Oui)': oBTTS})
        results['IA Proba (%)'] = (results['Prob_IA'] * 100).round(1)
        
        st.success(f"Conseil : {results.iloc[0]['Market']} (ROI: {results.iloc[0]['Value (%)']}%)")
        st.dataframe(results[['Market', 'Cote', 'IA Proba (%)', 'Value (%)']])
