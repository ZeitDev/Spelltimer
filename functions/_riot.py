import os
import roleidentification as PredictRoles
from riotwatcher import LolWatcher, ApiError

watcher = LolWatcher(os.getenv('riot_token'))

class Riot():
    def GetEnemies(self, summoner_name):
        print(f'Riot Api request for {summoner_name}')

        summoner_id = GetSummonerID(summoner_name)
        if isinstance(summoner_id, int): return summoner_id
        spectator_data = GetSpectatorData(summoner_id)
        if isinstance(spectator_data, int): return spectator_data

        enemy_champion_ids = ParseEnemies(spectator_data, summoner_name)
        sorted_enemy_champion_ids = SortIDsAfterRole(enemy_champion_ids)
        
        return sorted_enemy_champion_ids


# Helper Functions
def GetSummonerID(summoner_name):
    try:
        response = watcher.summoner.by_name('euw1', summoner_name)
        return response['id']
    except ApiError as err:
        if err.response.status_code == 429:
            print('ERROR: Too many request. Retry in {} seconds.'.format(err.response.headers['Retry-After']))
            return 429
        elif err.response.status_code == 404:
            print('ERROR: unknown summoner name')
            return 404
        else:
            raise

def GetSpectatorData(summoner_id):
    try:
        return watcher.spectator.by_summoner('euw1', summoner_id)
    except ApiError as err:
        if err.response.status_code == 429:
            print('ERROR: Too many request. Retry in {} seconds.'.format(err.response.headers['Retry-After']))
            return 429
        if err.response.status_code == 404:
            print('ERROR: Data not found')
            return 404

def ParseEnemies(spectator_data, summoner_name):
    players = spectator_data['participants']
    team_id = [player for player in players if player["summonerName"].lower() == summoner_name][0]['teamId']
    opponent_id = 100 if team_id == 200 else 200

    enemy_players = list(filter(lambda champion_id: champion_id['teamId'] == opponent_id, players))
    enemy_champion_ids = [enemy_player['championId'] for enemy_player in enemy_players]

    return enemy_champion_ids
    
def SortIDsAfterRole(enemy_champion_ids):
    try:
        champion_role_data = PredictRoles.pull_data()
        champion_roles = PredictRoles.get_roles(champion_role_data, enemy_champion_ids)
        return [champion_roles['TOP'], champion_roles['JUNGLE'], champion_roles['MIDDLE'], champion_roles['BOTTOM'], champion_roles['UTILITY']]
    except Exception as e:
        print('Failed to predict roles:', e)
        return enemy_champion_ids

import urllib.request
import json
import os.path
import glob

class DataDragon():
    def __init__(self):
        with urllib.request.urlopen("https://ddragon.leagueoflegends.com/api/versions.json") as url:
            self.data = json.loads(url.read().decode())
            self.version = self.data[0]

    def GetChampionData(self):
        if not os.path.isfile("cache/database/champions" + self.version + ".json"):
            self.Update()
        with open("cache/database/champions" + self.version + ".json") as file:
            data = json.load(file)["data"]
        return data

    def GetChampionUlts(self):
        data = self.GetChampionData()
        ChampionUlts= dict()
        for champion in data:
            ChampionUlts[data[champion]["name"]] = data[champion]["spells"][3]["cooldown"]
        return ChampionUlts

    def GetSummonerSpells(self):
        if not os.path.isfile("cache/database/summonerspells" + self.version + ".json"):
            self.Update()
        with open("cache/database/summonerspells" + self.version + ".json") as file:
            data = json.load(file)["data"]
        SummonerSpells = dict()
        for summonerspell in data:
            SummonerSpells[data[summonerspell]["name"]] = data[summonerspell]["cooldown"]
        return SummonerSpells

    def Update(self):
        print("Updating league database for new patch")

        files = glob.glob('cache/database/*')
        for f in files:
            try:
                os.remove(f)
            except OSError as e:
                print("Error: %s : %s" % (f, e.strerror))

        cache = open("cache/database/champions" + self.version + ".json", "x")
        with urllib.request.urlopen("http://ddragon.leagueoflegends.com/cdn/" + self.version + "/data/en_US/championFull.json") as url:
            cache.write(url.read().decode())
        cache.close()

        cache = open("cache/database/summonerspells" + self.version + ".json", "x")
        with urllib.request.urlopen("http://ddragon.leagueoflegends.com/cdn/" + self.version + "/data/en_US/summoner.json") as url:
            cache.write(url.read().decode())
        cache.close()

        print("Updated league database successfully")

    def ConvertNamesToIDs(self, enemy_champions):
        data = self.GetChampionData()
        id_name_table = GetChampionIDNameTable(data)

        enemy_champion_ids = list()
        for champion in enemy_champions:
            id = list(id_name_table.keys())[list(id_name_table.values()).index(champion)]
            enemy_champion_ids.append(int(id))

        return enemy_champion_ids

    
    def ConvertIDsToNames(self, enemy_champion_ids):
        data = self.GetChampionData()
        id_name_table = GetChampionIDNameTable(data)

        enemy_champions = [id_name_table[str(id)] for id in enemy_champion_ids]

        return enemy_champions

# Helper Functions

def GetChampionIDNameTable(data):
    id_name_table = dict()
    for champion in data:
        id_name_table[data[champion]['key']] = data[champion]['name']
    return id_name_table









