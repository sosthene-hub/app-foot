import pandas as pd
import requests

# Catalogue Europe Gratuit (Sans API)
FREE_LEAGUES = {
    "🇫🇷 France - L1": "F1", "🇫🇷 France - L2": "F2",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - P1": "E0", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - D2": "E1",
    "🇪🇸 Espagne - L1": "SP1", "🇪🇸 Espagne - L2": "SP2",
    "🇮🇹 Italie - A": "I1", "🇮🇹 Italie - B": "I2",
    "🇩🇪 Allemagne - L1": "D1", "🇩🇪 Allemagne - L2": "D2",
    "🇵🇹 Portugal - L1": "P1", "🇳🇱 Pays-Bas - L1": "N1",
    "🇧🇪 Belgique - L1": "B1"
}

def fetch_free_data(league_code):
    url = f"https://www.football-data.co.uk/mmz4281/2425/{league_code}.csv"
    try:
        df = pd.read_csv(url)
        # On simule le format pour analytics.py
        df = df.dropna(subset=['FTHG', 'FTAG'])
        stats = []
        for team in df['HomeTeam'].unique():
            h_matches = df[df['HomeTeam'] == team]
            a_matches = df[df['AwayTeam'] == team]
            stats.append({
                'Team': team,
                'GP_H': len(h_matches), 'GF_H': h_matches['FTHG'].sum(), 'GA_H': h_matches['FTAG'].sum(),
                'GP_A': len(a_matches), 'GF_A': a_matches['FTAG'].sum(), 'GA_A': a_matches['FTHG'].sum()
            })
        return pd.DataFrame(stats)
    except: return None

class GlobalScraper:
    def __init__(self, api_key):
        self.headers = {'x-rapidapi-key': api_key, 'x-rapidapi-host': "v3.football.api-sports.io"}
        self.base_url = "https://v3.football.api-sports.io/"

    def get_countries(self):
        try:
            r = requests.get(self.base_url + "countries", headers=self.headers, timeout=5)
            return r.json()['response'] if r.status_code == 200 else []
        except: return []

    def get_standings(self, league_id):
        try:
            r = requests.get(self.base_url + "standings", headers=self.headers, params={'league': league_id, 'season': 2024}, timeout=5)
            data = r.json()['response'][0]['league']['standings'][0]
            stats = []
            for team in data:
                stats.append({
                    'Team': team['team']['name'],
                    'GP_H': team['home']['played'], 'GF_H': team['home']['goals']['for'], 'GA_H': team['home']['goals']['against'],
                    'GP_A': team['away']['played'], 'GF_A': team['away']['goals']['for'], 'GA_A': team['away']['against']
                })
            return pd.DataFrame(stats)
        except: return None
