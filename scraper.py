import pandas as pd
import requests

FREE_LEAGUES = {
    "🇫🇷 France - L1": "F1", "🇫🇷 France - L2": "F2",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - P1": "E0", "🇪🇸 Espagne - L1": "SP1",
    "🇮🇹 Italie - A": "I1", "🇩🇪 Allemagne - L1": "D1"
}

def fetch_free_data(league_code):
    url = f"https://www.football-data.co.uk/mmz4281/2425/{league_code}.csv"
    try:
        df = pd.read_csv(url)
        df = df.dropna(subset=['FTHG', 'FTAG'])
        stats = []
        for team in df['HomeTeam'].unique():
            h_m = df[df['HomeTeam'] == team]
            a_m = df[df['AwayTeam'] == team]
            stats.append({
                'Team': team,
                'GP_H': len(h_m), 'GF_H': h_m['FTHG'].sum(), 'GA_H': h_m['FTAG'].sum(),
                'GP_A': len(a_m), 'GF_A': a_m['FTAG'].sum(), 'GA_A': a_m['FTHG'].sum()
            })
        return pd.DataFrame(stats)
    except:
        return None

class GlobalScraper:
    def __init__(self, api_key):
        self.headers = {'x-apisports-key': api_key.strip()}
        self.base_url = "https://v3.football.api-sports.io/"

    def get_countries(self):
        try:
            r = requests.get(self.base_url + "countries", headers=self.headers, timeout=10)
            return sorted(r.json().get('response', []), key=lambda x: x['name'])
        except:
            return []

    def get_leagues(self, country_name):
        try:
            r = requests.get(self.base_url + "leagues", headers=self.headers, params={'country': country_name}, timeout=10)
            return r.json().get('response', [])
        except:
            return []

    def get_standings(self, league_id, season):
        try:
            params = {'league': int(league_id), 'season': int(season)}
            r = requests.get(self.base_url + "standings", headers=self.headers, params=params, timeout=10)
            data = r.json()
            
            # Diagnostic : On vérifie si l'API a renvoyé une erreur
            if data.get('errors'):
                return f"Erreur API: {data['errors']}"

            response = data.get('response', [])
            if not response:
                return "Aucune donnée trouvée dans la réponse API."

            # Extraction sécurisée du classement
            league_obj = response[0].get('league', {})
            standings_list = league_obj.get('standings', [])
            
            if not standings_list:
                return "Le classement (standings) est vide pour cette ligue/saison."

            # Le classement est souvent une liste de listes [[team1, team2...]]
            table = standings_list[0]
            stats = []
            for item in table:
                stats.append({
                    'Team': item['team']['name'],
                    'GP_H': item['home']['played'],
                    'GF_H': item['home']['goals']['for'],
                    'GA_H': item['home']['goals']['against'],
                    'GP_A': item['away']['played'],
                    'GF_A': item['away']['goals']['for'],
                    'GA_A': item['away']['against']
                })
            return pd.DataFrame(stats)
        except Exception as e:
            return f"Erreur technique : {str(e)}"
