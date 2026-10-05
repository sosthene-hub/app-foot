import streamlit as st
from scraper import GlobalScraper, fetch_free_data, FREE_LEAGUES
from analytics import calculate_global_strengths, predict_match_matrix, analyze_all_markets

st.set_page_config(page_title="FootValue API-Sports", layout="centered")
st.title("⚽ FootValue Pro (API-Sports)")

# --- INITIALISATION ---
if 'df_stats' not in st.session_state:
    st.session_state.df_stats = None

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("🔑 Config API-Sports")
    api_key = st.text_input("Entre ta clé API-Sports", type="password")

if not api_key:
    st.info("💡 Veuillez entrer votre clé API-Sports dans la barre latérale.")
    sel_league = st.selectbox("Ou utilisez le mode Gratuit Europe", list(FREE_LEAGUES.keys()))
    if st.button("🔄 Charger Europe"):
        st.session_state.df_stats = fetch_free_data(FREE_LEAGUES[sel_league])
else:
    scraper = GlobalScraper(api_key)
    # Test de connexion immédiat
    countries = scraper.get_countries()
    
    if countries:
        st.success("✅ Connecté à API-Sports")
        c_names = [c['name'] for c in countries]
        col1, col2 = st.columns(2)
        with col1:
            default_country = 'France' if 'France' in c_names else c_names[0]
            sel_country = st.selectbox("Pays", c_names, index=c_names.index(default_country))
        
        leagues = scraper.get_leagues(sel_country)
        if leagues:
            league_map = {l['league']['name']: l['league']['id'] for l in leagues}
            with col2:
                sel_div = st.selectbox("Division", list(league_map.keys()))
            
            # Choix de la saison
            sel_season = st.selectbox("Saison", [2024, 2023], index=0, help="Si 2024 ne donne rien, essayez 2023")
            
            if st.button("🚀 Charger les Stats"):
                st.session_state.df_stats = scraper.get_standings(league_map[sel_div], season=sel_season)
                if st.session_state.df_stats is not None:
                    st.success(f"Données de {sel_div} ({sel_season}) chargées !")
                else:
                    st.error(f"Aucune donnée trouvée pour {sel_div} en {sel_season}. Essayez la saison 2023.")
    else:
        st.error("❌ La clé est refusée ou erreur de connexion. Vérifiez votre clé API-Sports.")

# --- ANALYSE ---
if st.session_state.df_stats is not None:
    df = st.session_state.df_stats
    teams = sorted(df['Team'].unique())
    
    st.divider()
    st.subheader("📊 Analyse de Match")
    h_col, a_col = st.columns(2)
    home = h_col.selectbox("🏠 Domicile", teams)
    away = a_col.selectbox("🚀 Extérieur", teams, index=1 if len(teams)>1 else 0)

    strengths, avg_h, avg_a = calculate_global_strengths(df)
    
    st.subheader("⚖️ Cotes Bookmaker")
    c1, c2, c3 = st.columns(3)
    o1, oN, o2 = c1.number_input("Cote 1", value=2.0), c2.number_input("Cote N", value=3.0), c3.number_input("Cote 2", value=3.0)
    
    c4, c5 = st.columns(2)
    oOver, oBTTS = c4.number_input("Cote Over 2.5", value=1.85), c5.number_input("Cote BTTS (Oui)", value=1.75)

    if st.button("🔍 ANALYSER LA VALUE"):
        try:
            matrix = predict_match_matrix(home, away, strengths, avg_h, avg_a)
            results = analyze_all_markets(matrix, {'1': o1, 'N': oN, '2': o2, 'Over 2.5': oOver, 'BTTS (Oui)': oBTTS})
            results['IA Proba (%)'] = (results['Prob_IA'] * 100).round(1)
            
            best_value = results.iloc[0]
            st.success(f"Conseil : {best_value['Market']} (ROI: {best_value['Value (%)']}%)")
            st.dataframe(results[['Market', 'Cote', 'IA Proba (%)', 'Value (%)']])
        except Exception as e:
            st.error(f"Erreur lors de l'analyse : {e}")
