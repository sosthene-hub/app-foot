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
            if not response: return None
            
            table = response[0].get('league', {}).get('standings', [])[0]
            stats = []
            for item in table:
                stats.append({
                    'Team': item['team']['name'],
                    'ID': item['team']['id'], # Garder l'ID pour les joueurs
                    'GP_H': item['home']['played'],
                    'GF_H': item['home']['goals']['for'],
                    'GA_H': item['home']['goals']['against'],
                    'GP_A': item['away']['played'],
                    'GF_A': item['away']['goals']['for'],
                    'GA_A': item['away']['against'],
                    'Form': item.get('form', "")
                })
            return pd.DataFrame(stats)
        except Exception as e: return str(e)

    def get_absentees(self, league_id, season, team_id):
        """Récupère les blessés et suspendus"""
        try:
            params = {'league': league_id, 'season': season, 'team': team_id}
            r = requests.get(self.base_url + "injuries", headers=self.headers, params=params, timeout=10)
            injuries = r.json().get('response', [])
            return [i['player']['name'] for i in injuries]
        except: return []

    def get_key_players(self, league_id, season, team_id):
        """Récupère les joueurs les plus importants (buteurs et temps de jeu)"""
        try:
            params = {'league': league_id, 'season': season, 'team': team_id}
            r = requests.get(self.base_url + "players", headers=self.headers, params=params, timeout=10)
            players = r.json().get('response', [])
            
            # Trier par buts puis par minutes
            sorted_players = sorted(players, key=lambda x: (x['statistics'][0]['goals']['total'] or 0), reverse=True)
            return [p['player']['name'] for p in sorted_players[:5]] # Top 5 joueurs
        except: return []
