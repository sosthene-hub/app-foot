import requests
import pandas as pd

class GlobalScraper:
    def __init__(self, api_key):
        self.headers = {'x-rapidapi-key': api_key, 'x-rapidapi-host': "v3.football.api-sports.io"}
        self.base_url = "https://v3.football.api-sports.io/"

    def get_countries(self):
        r = requests.get(self.base_url + "countries", headers=self.headers)
        return sorted(r.json()['response'], key=lambda x: x['name']) if r.status_code == 200 else []

    def get_leagues(self, country_name):
        r = requests.get(self.base_url + "leagues", headers=self.headers, params={'country': country_name})
        return r.json()['response'] if r.status_code == 200 else []

    def get_standings(self, league_id, season=2024):
        r = requests.get(self.base_url + "standings", headers=self.headers, params={'league': league_id, 'season': season})
        if r.status_code == 200 and r.json()['response']:
            data = r.json()['response'][0]['league']['standings'][0]
            stats = []
            for team in data:
                stats.append({
                    'Team': team['team']['name'],
                    'GP_H': team['home']['played'], 'GF_H': team['home']['goals']['for'], 'GA_H': team['home']['goals']['against'],
                    'GP_A': team['away']['played'], 'GF_A': team['away']['goals']['for'], 'GA_A': team['away']['against']
                })
            return pd.DataFrame(stats)
        return None
