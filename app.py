import streamlit as st
from scraper import GlobalScraper, FREE_LEAGUES, fetch_free_data
from analytics import calculate_global_strengths, predict_match_matrix, analyze_all_markets

st.set_page_config(page_title="FootValue", layout="centered")

st.title("⚽ FootValue Pro")

# --- CHOIX DU MODE ---
mode = st.radio("Mode de données", ["Europe (Gratuit)", "Monde (Clé API requis)"], horizontal=True)

df_stats = None

if mode == "Europe (Gratuit)":
    sel_league = st.selectbox("Choisir une ligue européenne", list(FREE_LEAGUES.keys()))
    if st.button("🔄 Charger les Stats Europe"):
        df_stats = fetch_free_data(FREE_LEAGUES[sel_league])
        if df_stats is not None:
            st.session_state.df_stats = df_stats
            st.success("Données Europe chargées !")

else:
    api_key = st.sidebar.text_input("Clé API-Football", type="password")
    if not api_key:
        st.warning("Entre ta clé API à gauche.")
    else:
        scraper = GlobalScraper(api_key)
        # On simplifie pour le test
        st.info("Mode Monde activé. Si rien ne s'affiche, c'est que la clé est invalide.")
        # Ici on pourrait remettre le sélecteur de pays/ligue de l'étape précédente

# --- ANALYSE ---
if 'df_stats' in st.session_state:
    df = st.session_state.df_stats
    teams = sorted(df['Team'].unique())
    
    st.divider()
    col_h, col_a = st.columns(2)
    home = col_h.selectbox("🏠 Domicile", teams)
    away = col_a.selectbox("🚀 Extérieur", teams, index=1 if len(teams)>1 else 0)

    st.subheader("⚖️ Cotes Bookmaker")
    c1, c2, c3 = st.columns(3)
    o1 = c1.number_input("1", value=2.0)
    oN = c2.number_input("N", value=3.0)
    o2 = c3.number_input("2", value=3.0)

    if st.button("🔍 ANALYSER LA VALUE"):
        strengths, avg_h, avg_a = calculate_global_strengths(df)
        matrix = predict_match_matrix(home, away, strengths, avg_h, avg_a)
        results = analyze_all_markets(matrix, {'1': o1, 'N': oN, '2': o2})
        st.success(f"🤖 CONSEIL : {results.iloc[0]['Market']} (ROI: {results.iloc[0]['Value (%)']}%)")
        st.dataframe(results[['Market', 'Cote', 'Value (%)']])
