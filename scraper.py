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
                'GP_H': len(h_m), 
                'GF_H': h_m['FTHG'].sum(), 
                'GA_H': h_m['FTAG'].sum(),
                'GP_A': len(a_m), 
                'GF_A': a_m['FTAG'].sum(), 
                'GA_A': a_m['FTHG'].sum()
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
            
            if data.get('errors'):
                return f"Erreur API: {data['errors']}"

            response = data.get('response', [])
            if not response:
                return "L'API n'a renvoyé aucune réponse pour cette sélection."

            league_obj = response[0].get('league', {})
            standings_list = league_obj.get('standings', [])
            
            if not standings_list:
                return "Le classement est vide pour cette saison."

            # Le classement est dans le premier élément
            table = standings_list[0]
            stats = []
            
            for item in table:
                # Utilisation de .get() pour éviter l'erreur 'against'
                team_name = item.get('team', {}).get('name', 'Inconnu')
                
                home_data = item.get('home', {})
                away_data = item.get('away', {})
                
                home_goals = home_data.get('goals', {})
                away_goals = away_data.get('goals', {})
                
                stats.append({
                    'Team': team_name,
                    'GP_H': home_data.get('played', 0),
                    'GF_H': home_goals.get('for', 0),
                    'GA_H': home_goals.get('against', 0), # ICI ETAIT L'ERREUR
                    'GP_A': away_data.get('played', 0),
                    'GF_A': away_goals.get('for', 0),
                    'GA_A': away_goals.get('against', 0)  # ICI ETAIT L'ERREUR
                })
            
            df = pd.DataFrame(stats)
            # On retire les équipes qui n'ont pas encore joué pour éviter les divisions par zéro
            df = df[(df['GP_H'] + df['GP_A']) > 0]
            
            if df.empty:
                return "Toutes les équipes ont 0 match joué. Stats insuffisantes."
                
            return df
        except Exception as e:
            return f"Erreur technique : {str(e)}"
