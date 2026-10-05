import requests
import pandas as pd

class GlobalScraper:
    def __init__(self, api_key):
        self.headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': "v3.football.api-sports.io"
        }
        self.base_url = "https://v3.football.api-sports.io/"

    def get_countries(self):
        try:
            r = requests.get(self.base_url + "countries", headers=self.headers, timeout=10)
            return sorted(r.json()['response'], key=lambda x: x['name']) if r.status_code == 200 else []
        except: return []

    def get_leagues(self, country_name):
        try:
            r = requests.get(self.base_url + "leagues", headers=self.headers, params={'country': country_name}, timeout=10)
            return r.json()['response'] if r.status_code == 200 else []
        except: return []

    def get_standings(self, league_id):
        try:
            # On récupère la saison 2024 (ou 2025 selon le pays)
            r = requests.get(self.base_url + "standings", headers=self.headers, params={'league': league_id, 'season': 2024}, timeout=10)
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

# Garde aussi la fonction gratuite pour l'Europe en secours
def fetch_free_data(league_code):
    url = f"https://www.football-data.co.uk/mmz4281/2425/{league_code}.csv"
    try:
        df = pd.read_csv(url)
        df = df.dropna(subset=['FTHG', 'FTAG'])
        stats = []
        for team in df['HomeTeam'].unique():
            h = df[df['HomeTeam'] == team]
            a = df[df['AwayTeam'] == team]
            stats.append({
                'Team': team, 'GP_H': len(h), 'GF_H': h['FTHG'].sum(), 'GA_H': h['FTAG'].sum(),
                'GP_A': len(a), 'GF_A': a['FTAG'].sum(), 'GA_A': a['FTHG'].sum()
            })
        return pd.DataFrame(stats)
    except: return None
