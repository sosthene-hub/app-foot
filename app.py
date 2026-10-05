import streamlit as st
from scraper import GlobalScraper
from analytics import calculate_global_strengths, predict_match_matrix, analyze_all_markets

st.set_page_config(page_title="WorldValue IA", layout="centered")

# --- STYLE ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 3em; background-color: #007bff; color: white; font-weight: bold; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# Barre latérale
with st.sidebar:
    st.title("⚙️ Configuration")
    api_key = st.text_input("Entre ta clé RapidAPI", type="password")
    st.info("La clé ressemble à : 8745c3b...msh123...")

if not api_key:
    st.warning("⚠️ Entre ta clé API à gauche pour activer l'application.")
    st.stop()

scraper = GlobalScraper(api_key)

# 1. RÉCUPÉRATION DES PAYS
countries = scraper.get_countries()

if not countries:
    st.error("❌ Erreur de connexion : La clé API est invalide ou le quota est dépassé. Vérifie ta souscription gratuite sur RapidAPI.")
    st.stop()

st.title("⚽ WorldValue IA")

# 2. SÉLECTION PAYS ET LIGUE
c1, c2 = st.columns(2)
country_names = [c['name'] for c in countries]

with c1:
    sel_country = st.selectbox("Pays", country_names)

leagues = scraper.get_leagues(sel_country)
if leagues:
    league_map = {l['league']['name']: l['league']['id'] for l in leagues}
    with c2:
        sel_league = st.selectbox("Ligue", list(league_map.keys()))
    
    if st.button("🔄 Charger les Stats"):
        with st.spinner("Récupération du classement mondial..."):
            res_stats = scraper.get_standings(league_map[sel_league])
            if res_stats is not None:
                st.session_state.df_stats = res_stats
                st.success(f"Données de {sel_league} chargées !")
            else:
                st.error("Impossible de récupérer les statistiques pour cette ligue.")
else:
    st.warning("Aucune ligue trouvée pour ce pays.")

# 3. ANALYSE DU MATCH
if 'df_stats' in st.session_state and st.session_state.df_stats is not None:
    df = st.session_state.df_stats
    teams = sorted(df['Team'].unique())
    
    st.divider()
    col_h, col_a = st.columns(2)
    home = col_h.selectbox("🏠 Domicile", teams)
    away = col_a.selectbox("🚀 Extérieur", teams, index=1 if len(teams) > 1 else 0)

    st.subheader("⚖️ Cotes Bookmaker")
    c1, c2, c3 = st.columns(3)
    o1 = c1.number_input("Cote 1", value=2.0)
    oN = c2.number_input("Cote N", value=3.0)
    o2 = c3.number_input("Cote 2", value=3.0)

    if st.button("🔍 ANALYSER LA VALUE"):
        try:
            strengths, avg_h, avg_a = calculate_global_strengths(df)
            matrix = predict_match_matrix(home, away, strengths, avg_h, avg_a)
            results = analyze_all_markets(matrix, {'1': o1, 'N': oN, '2': o2})
            
            best = results.iloc[0]
            st.success(f"🤖 CONSEIL : {best['Market']} (ROI: {best['Value (%)']}%)")
            
            for _, row in results.iterrows():
                with st.expander(f"{row['Market']} | ROI: {row['Value (%)']}%"):
                    st.write(f"Confiance IA: {round(row['Prob_IA']*100, 1)}%")
                    st.write(f"Cote minimale rentable: {round(1/row['Prob_IA'], 2)}")
        except Exception as e:
            st.error(f"Erreur de calcul : {e}")
