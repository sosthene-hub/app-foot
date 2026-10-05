import streamlit as st
from scraper import GlobalScraper
from analytics import calculate_global_strengths, predict_match_matrix, analyze_all_markets

st.set_page_config(page_title="WorldValue IA", layout="centered")

st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 3em; background-color: #007bff; color: white; font-weight: bold; border-radius: 10px; }
    .stNumberInput>div>div>input { font-size: 1.2em; }
    </style>
    """, unsafe_allow_html=True)

# Barre latérale pour la configuration
with st.sidebar:
    st.title("⚙️ Config")
    api_key = st.text_input("Clé API-Football", type="password")
    st.info("Obtenez une clé gratuite sur RapidAPI")

if not api_key:
    st.warning("Veuillez entrer votre clé API dans le menu à gauche.")
    st.stop()

scraper = GlobalScraper(api_key)

# Écran Principal
st.title("⚽ WorldValue IA")

# 1. Sélection Ligue
c1, c2 = st.columns(2)
countries = scraper.get_countries()
country_names = [c['name'] for c in countries]
with c1: 
    sel_country = st.selectbox("Pays", country_names, index=country_names.index('France') if 'France' in country_names else 0)

leagues = scraper.get_leagues(sel_country)
league_map = {l['league']['name']: l['league']['id'] for l in leagues}
with c2:
    sel_league = st.selectbox("Ligue", list(league_map.keys()))

if st.button("🔄 Charger les Stats"):
    st.session_state.df_stats = scraper.get_standings(league_map[sel_league])
    st.success("Données Monde à jour !")

# 2. Analyse Match
if 'df_stats' in st.session_state and st.session_state.df_stats is not None:
    df = st.session_state.df_stats
    teams = sorted(df['Team'].unique())
    
    col_h, col_a = st.columns(2)
    home = col_h.selectbox("🏠 Domicile", teams)
    away = col_a.selectbox("🚀 Extérieur", teams, index=1)

    st.subheader("⚖️ Cotes Bookmaker")
    c1, c2, c3 = st.columns(3)
    o1 = c1.number_input("1", value=2.0)
    oN = c2.number_input("N", value=3.0)
    o2 = c3.number_input("2", value=3.0)

    if st.button("🔍 ANALYSER LA VALUE"):
        strengths, avg_h, avg_a = calculate_global_strengths(df)
        matrix = predict_match_matrix(home, away, strengths, avg_h, avg_a)
        results = analyze_all_markets(matrix, {'1': o1, 'N': oN, '2': o2})
        
        best = results.iloc[0]
        st.success(f"🤖 CONSEIL : {best['Market']} (ROI: {best['Value (%)']}%)")
        
        for _, row in results.iterrows():
            with st.expander(f"{row['Market']} | ROI: {row['Value (%)']}%"):
                st.write(f"Probabilité IA: {round(row['Prob_IA']*100, 1)}%")
                st.write(f"Cote minimale rentable: {round(1/row['Prob_IA'], 2)}")
