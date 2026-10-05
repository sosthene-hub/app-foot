import streamlit as st
from scraper import GlobalScraper, FREE_LEAGUES, fetch_free_data
from analytics import calculate_global_strengths, predict_match_matrix, analyze_all_markets

st.set_page_config(page_title="FootValue Pro", layout="centered")
st.title("⚽ FootValue Pro")

if 'df_stats' not in st.session_state:
    st.session_state.df_stats = None

mode = st.radio("Mode de données", ["Europe (Gratuit)", "Monde (Clé API)"], horizontal=True)

if mode == "Europe (Gratuit)":
    sel_league = st.selectbox("Choisir une ligue européenne", list(FREE_LEAGUES.keys()))
    if st.button("🔄 Charger les Stats Europe"):
        df_stats = fetch_free_data(FREE_LEAGUES[sel_league])
        if df_stats is not None:
            st.session_state.df_stats = df_stats
            st.success("Données Europe chargées !")

# --- ANALYSE DU MATCH ---
if st.session_state.df_stats is not None:
    df = st.session_state.df_stats
    teams = sorted(df['Team'].unique())
    
    st.divider()
    col_h, col_a = st.columns(2)
    with col_h: home = st.selectbox("🏠 Domicile", teams)
    with col_a: away = st.selectbox("🚀 Extérieur", teams, index=1 if len(teams)>1 else 0)

    # --- NOUVEAU : AFFICHAGE DES FORCES ATTAQUE/DÉFENSE ---
    strengths, avg_h, avg_a = calculate_global_strengths(df)
    s_h = strengths.loc[home]
    s_a = strengths.loc[away]

    st.subheader("🛡️ Duel des Forces")
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**{home}**")
        st.caption(f"Attaque : {round(s_h['home_atk'], 2)}")
        st.caption(f"Défense : {round(s_h['home_def'], 2)}")
    with c2:
        st.write(f"**{away}**")
        st.caption(f"Attaque : {round(s_a['away_atk'], 2)}")
        st.caption(f"Défense : {round(s_a['away_def'], 2)}")
    
    st.info("💡 Défense < 1.0 = Solide | Défense > 1.0 = Fragile")

    st.divider()
    st.subheader("⚖️ Cotes Bookmaker")
    c1, c2, c3 = st.columns(3)
    o1 = c1.number_input("Cote 1", value=2.0)
    oN = c2.number_input("Cote N", value=3.0)
    o2 = c3.number_input("Cote 2", value=3.0)
    
    c4, c5 = st.columns(2)
    oOver = c4.number_input("Cote Over 2.5", value=1.85)
    oBTTS = c5.number_input("Cote BTTS (Oui)", value=1.75)

    if st.button("🔍 ANALYSER LA VALUE"):
        try:
            matrix = predict_match_matrix(home, away, strengths, avg_h, avg_a)
            odds = {'1': o1, 'N': oN, '2': o2, 'Over 2.5': oOver, 'BTTS (Oui)': oBTTS}
            results = analyze_all_markets(matrix, odds)
            results['IA Proba (%)'] = (results['Prob_IA'] * 100).round(1)
            
            best = results.iloc[0]
            st.success(f"🤖 CONSEIL : {best['Market']} (ROI: {best['Value (%)']}%)")
            st.dataframe(results[['Market', 'Cote', 'IA Proba (%)', 'Value (%)']], use_container_width=True)
        except Exception as e:
            st.error(f"Erreur : {e}")
