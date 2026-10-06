import pandas as pd
import requests
import streamlit as st

FREE_LEAGUES = {
    "🇫🇷 France - Ligue 1": "F1",
    "🇫🇷 France - Ligue 2": "F2",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - Premier League": "E0",
    "🇪🇸 Espagne - La Liga": "SP1",
    "🇮🇹 Italie - Serie A": "I1",
    "🇩🇪 Allemagne - Bundesliga": "D1",
    "🇧🇪 Belgique - Pro League": "B1",
    "🇳🇱 Pays-Bas - Eredivisie": "N1"
}

class GlobalScraper:
    def __init__(self, api_key):
        self.headers = {'x-apisports-key': api_key.strip()}
        self.base_url = "https://v3.football.api-sports.io/"

    @st.cache_data(ttl=86400) # Cache de 24h pour la liste des pays
    def get_countries(_self):
        try:
            r = requests.get(_self.base_url + "countries", headers=_self.headers, timeout=5)
            return sorted(r.json().get('response', []), key=lambda x: x['name'])
        except: return []

    @st.cache_data(ttl=86400) # Cache de 24h pour les ligues
    def get_leagues(_self, country_name):
        try:
            r = requests.get(_self.base_url + "leagues", headers=_self.headers, params={'country': country_name}, timeout=5)
            return r.json().get('response', [])
        except: return []

    @st.cache_data(ttl=3600) # Cache de 1h pour les classements
    def get_standings(_self, league_id, season):
        try:
            r = requests.get(_self.base_url + "standings", headers=_self.headers, params={'league': int(league_id), 'season': int(season)}, timeout=7)
            data = r.json()
            table = data['response'][0]['league']['standings'][0]
            stats = []
            for item in table:
                stats.append({
                    'Team': item['team']['name'], 'ID': item['team']['id'],
                    'GP_H': item['home']['played'], 'GF_H': item['home']['goals']['for'],
                    'GA_H': item['home']['goals']['against'], 'GP_A': item['away']['played'],
                    'GF_A': item['away']['goals']['for'], 'GA_A': item['away']['goals']['against']
                })
            return pd.DataFrame(stats)
        except: return "Erreur API."

    @st.cache_data(ttl=3600) # Cache de 1h pour les absents
    def get_absentees(_self, l_id, s, t_id):
        try:
            r = requests.get(_self.base_url + "injuries", headers=_self.headers, params={'league':l_id,'season':s,'team':t_id}, timeout=5)
            return sorted(list({i['player']['name'] for i in r.json().get('response', [])}))
        except: return []

    @st.cache_data(ttl=3600) # Cache de 1h pour les joueurs clés
    def get_key_players(_self, l_id, s, t_id):
        try:
            r = requests.get(_self.base_url + "players", headers=_self.headers, params={'league':l_id,'season':s,'team':t_id}, timeout=5)
            players = sorted(r.json().get('response', []), key=lambda x: (x['statistics'][0]['goals']['total'] or 0), reverse=True)
            return [p['player']['name'] for p in players[:8]]
        except: return []

@st.cache_data(ttl=3600)
def fetch_free_data(league_code):
    url = f"https://www.football-data.co.uk/mmz4281/2425/{league_code}.csv"
    try:
        df = pd.read_csv(url).dropna(subset=['FTHG', 'FTAG'])
        stats = []
        for team in df['HomeTeam'].unique():
            h, a = df[df['HomeTeam']==team], df[df['AwayTeam']==team]
            stats.append({'Team': team, 'ID': 0, 'GP_H': len(h), 'GF_H': h['FTHG'].sum(), 'GA_H': h['FTAG'].sum(),
                          'GP_A': len(a), 'GF_A': a['FTAG'].sum(), 'GA_A': a['FTHG'].sum()})
        return pd.DataFrame(stats)
    except: return None
