    if st.button("🔍 ANALYSER LA VALUE"):
        strengths, avg_h, avg_a = calculate_global_strengths(df)
        matrix = predict_match_matrix(home, away, strengths, avg_h, avg_a, abs_h, abs_a)
        res = analyze_all_markets(matrix, {'1':c1, 'N':cN, '2':c2, 'Over 2.5':cO, 'BTTS (Oui)':cB})
        
        # Style de couleur (Vert si Value > 0, Rouge si Value < 0)
        def color_value(v):
            if isinstance(v, float) or isinstance(v, int):
                color = '#27AE60' if v > 0 else '#E74C3C'
                return f'color: {color}; font-weight: bold'
            return ''

        # Affichage du tableau propre
        st.table(res.style.map(color_value, subset=['Value (%)']))
        
        # Avertissement si peu de matchs joués
        if df['GP_H'].iloc[0] < 5:
            st.warning("⚠️ Attention : Peu de matchs joués cette saison. L'analyse peut être instable.")
