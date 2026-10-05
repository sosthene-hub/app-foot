import streamlit as st
from scraper import GlobalScraper, FREE_LEAGUES, fetch_free_data
from analytics import calculate_global_strengths, predict_match_matrix, analyze_all_markets

st.set_page_config(page_title="FootValue", layout="centered")

st.title("⚽ FootValue Pro")

# --- CHOIX DU MODE ---
mode = st.radio("Mode de données", ["Europe (Gratuit)", "Monde (Clé API)"], horizontal=True)

# Initialisation de la variable
if 'df_stats' not in st.session_state:
    st.session_state.df_stats = None

if mode == "Europe (Gratuit)":
    sel_league = st.selectbox("Choisir une ligue européenne", list(FREE_LEAGUES.keys()))
    if st.button("🔄 Charger les Stats Europe"):
        df_stats = fetch_free_data(FREE_LEAGUES[sel_league])
        if df_stats is not None:
            st.session_state.df_stats = df_stats
            st.success("Données Europe chargées !")
        else:
            st.error("Erreur lors du chargement des données.")

else:
    api_key = st.sidebar.text_input("Clé API-Football", type="password")
    if not api_key:
        st.warning("Entre ta clé API à gauche.")
    else:
        st.info("Mode Monde activé. Assure-toi que ta clé est valide.")
        # Le sélecteur de pays pour le mode API pourrait être ajouté ici

# --- ANALYSE DU MATCH (Correctement aligné) ---
if st.session_state.df_stats is not None:
    df = st.session_state.df_stats
    teams = sorted(df['Team'].unique())
    
    st.divider()
    col_h, col_a = st.columns(2)
    with col_h:
        home = st.selectbox("🏠 Domicile", teams)
    with col_a:
        away = st.selectbox("🚀 Extérieur", teams, index=1 if len(teams)>1 else 0)

    st.subheader("⚖️ Cotes Bookmaker")
    c1, c2, c3 = st.columns(3)
    with c1: o1 = st.number_input("Cote 1", value=2.0, step=0.01)
    with c2: oN = st.number_input("Cote N", value=3.0, step=0.01)
    with c3: o2 = st.number_input("Cote 2", value=3.0, step=0.01)

    if st.button("🔍 ANALYSER LA VALUE"):
        try:
            # Calculs
            strengths, avg_h, avg_a = calculate_global_strengths(df)
            matrix = predict_match_matrix(home, away, strengths, avg_h, avg_a)
            results = analyze_all_markets(matrix, {'1': o1, 'N': oN, '2': o2})
            
            # Ajout des probabilités en %
            results['IA Proba (%)'] = (results['Prob_IA'] * 100).round(1)
            
            # Affichage du Conseil
            best = results.iloc[0]
            st.success(f"🤖 CONSEIL : {best['Market']} (ROI: {best['Value (%)']}%)")
            
            # Tableau des résultats
            st.dataframe(results[['Market', 'Cote', 'IA Proba (%)', 'Value (%)']], use_container_width=True)
            
            # Détails par marché
            for _, row in results.iterrows():
                with st.expander(f"{row['Market']} | Proba: {row['IA Proba (%)']}%"):
                    st.write(f"Cote minimale rentable : **{round(1/row['Prob_IA'], 2)}**")
        except Exception as e:
            st.error(f"Erreur de calcul : {e}")
else:
    st.info("Veuillez charger les statistiques d'une ligue pour commencer l'analyse.")
