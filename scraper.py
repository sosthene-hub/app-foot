import pandas as pd
import requests

class GlobalScraper:
    def __init__(self, api_key):
        self.headers = {'x-apisports-key': api_key.strip()}
        self.base_url = "https://v3.football.api-sports.io/"

    def get_countries(self):
        try:
            r = requests.get(self.base_url + "countries", headers=self.headers, timeout=10)
            return sorted(r.json().get('response', []), key=lambda x: x['name'])
        except: return []

    def get_leagues(self, country_name):
        try:
            r = requests.get(self.base_url + "leagues", headers=self.headers, params={'country': country_name}, timeout=10)
            return r.json().get('response', [])
        except: return []

    def get_standings(self, league_id, season):
        try:
            params = {'league': int(league_id), 'season': int(season)}
            r = requests.get(self.base_url + "standings", headers=self.headers, params=params, timeout=10)
            data = r.json()
            response = data.get('response', [])
            if not response: return "Aucune donnée."
            table = response[0]['league']['standings'][0]
            stats = []
            for item in table:
                stats.append({
                    'Team': item['team']['name'], 'ID': item['team']['id'],
                    'GP_H': item['home']['played'], 'GF_H': item['home']['goals']['for'],
                    'GA_H': item['home']['goals']['against'], 'GP_A': item['away']['played'],
                    'GF_A': item['away']['goals']['for'], 'GA_A': item['away']['goals']['against'],
                    'Form': item.get('form', "")
                })
            return pd.DataFrame(stats)
        except: return "Erreur API."

    def get_absentees(self, league_id, season, team_id):
        try:
            params = {'league': league_id, 'season': season, 'team': team_id}
            r = requests.get(self.base_url + "injuries", headers=self.headers, params=params, timeout=10)
            # Utilisation de set() pour supprimer les doublons de noms
            names = {i['player']['name'] for i in r.json().get('response', [])}
            return sorted(list(names))
        except: return []

    def get_key_players(self, league_id, season, team_id):
        try:
            params = {'league': league_id, 'season': season, 'team': team_id}
            r = requests.get(self.base_url + "players", headers=self.headers, params=params, timeout=10)
            players = r.json().get('response', [])
            sorted_p = sorted(players, key=lambda x: (x['statistics'][0]['goals']['total'] or 0), reverse=True)
            return [p['player']['name'] for p in sorted_p[:8]] # Top 8 pour être large
        except: return []

def fetch_free_data(league_code):
    url = f"https://www.football-data.co.uk/mmz4281/2425/{league_code}.csv"
    try:
        df = pd.read_csv(url).dropna(subset=['FTHG', 'FTAG'])
        stats = []
        for team in df['HomeTeam'].unique():
            h, a = df[df['HomeTeam']==team], df[df['AwayTeam']==team]
            stats.append({'Team': team, 'ID': 0, 'GP_H': len(h), 'GF_H': h['FTHG'].sum(), 'GA_H': h['FTAG'].sum(),
                          'GP_A': len(a), 'GF_A': a['FTAG'].sum(), 'GA_A': a['FTHG'].sum(), 'Form': ""})
        return pd.DataFrame(stats)
    except: return None
