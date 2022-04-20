import time
import config
import asyncio
import nextcord

from functions import _riot
from functions import _ocr


class Timer():
    async def Initialize(self, ctx, args):
        config.VariableDict['timer_running'] = True

        enemy_champions = await GetEnemyChampionsByRiot(ctx, args)
        if enemy_champions == 0: return
        elif enemy_champions == 1: enemy_champions = await GetEnemyChampionsByUser(ctx)

        await self.StartTimer(ctx, enemy_champions)

    async def StartTimer(self, ctx, enemy_champions):
        TimerData = {
            'timers': {},
            'enemy_champions': enemy_champions,
            'champion_levels': { c : 1 for c in enemy_champions},
            'game_time': 0,
            'previous_time': time.time(),
            'delta_time': 0
        }

        embed = EditEmbed(TimerData)
        message = await ctx.channel.send(embed)

        await self.LoopTimer(TimerData, message)

    
    async def LoopTimer(self, TimerData, message):
        while config.VariableDict['timer_running']:
            TimerData['delta_time'] = time.time() - TimerData['previous_time']
            TimerData['previous_time'] = time.time()
            TimerData['game_time'] += TimerData['delta_time']

            await _ocr.OCR().UpdateTimerData(TimerData)

            embed = EditEmbed(TimerData)
            await message.edit(embed)
            
            await asyncio.sleep(1)
        else: await message.delete()

    async def Restart(self, ctx, args):
        await self.Stop()
        await asyncio.sleep(2)
        await self.Initialize(ctx, args)
        
    async def Stop(self):
        config.VariableDict['timer_running'] = False

# Helper functions
async def GetEnemyChampionsByRiot(ctx, args):
    summoner_name = (' ').join(args).lower()
    if summoner_name != "": enemy_champion_ids = _riot.Riot().GetEnemies(summoner_name)
    else: enemy_champion_ids = 400

    if enemy_champion_ids == 429:
        await ctx.channel.send('Riot API not responding.', delete_after=5)
    if enemy_champion_ids == 404:
        await ctx.channel.send('No data found.', delete_after=5)
    if enemy_champion_ids in [429, 404, 408]:
        await Timer().Stop()
        return 0

    if enemy_champion_ids == 400 or enemy_champion_ids == []: return 1
    else:
        sorted_enemy_champion_ids = _riot.SortIDsAfterRole(enemy_champion_ids)
        sorted_enemy_champions = _riot.DataDragon().ConvertIDsToNames(sorted_enemy_champion_ids)
        return sorted_enemy_champions

async def GetEnemyChampionsByUser(ctx):
    enemy_champions = []
    message = await ctx.channel.send(f'Insert champs via scoreboard:\nDetected enemies: {enemy_champions}')
    while len(enemy_champions) < 5 and config.VariableDict['timer_running']:
        enemy_champions = await _ocr.OCR().UpdateEnemyChampions(enemy_champions)
        await message.edit(f'Insert champs via scoreboard:\nDetected enemies: {enemy_champions}')
        await asyncio.sleep(0.1)

    await message.delete()

    enemy_champion_ids = _riot.DataDragon().ConvertNamesToIDs(enemy_champions)
    sorted_enemy_champion_ids = _riot.SortIDsAfterRole(enemy_champion_ids)
    sorted_enemy_champions = _riot.DataDragon().ConvertIDsToNames(sorted_enemy_champion_ids)
    return sorted_enemy_champions

def EditEmbed(TimerData):
    bot = config.VariableDict['bot']
    lanes = ['top', 'jungle', 'mid', 'adc', 'sup']
    message = 'Estimated Game Time: ' + time.strftime("%M:%S", time.gmtime(TimerData['game_time'])) + "\n"

    for champion in TimerData['enemy_champions']:
        message += str(nextcord.utils.get(bot.emojis, name = lanes.pop(0))) + "**" + champion + " " + str(TimerData['champion_levels'][champion]) + ":**" + "\t"
        if (champion, "Flash") in TimerData['timers']:
           message += str(nextcord.utils.get(bot.emojis, name = "Flash")) + " " + str(int(TimerData['timers'][(champion, "Flash")])) + "\t"
        for (c, ability) in TimerData['timers']:
            if champion == c and ability != "R" and ability != "Flash":
               message += str(nextcord.utils.get(bot.emojis, name = ability))+ " " + str(int(TimerData['timers'][(champion, ability)])) + "\t"
        if (champion, "R") in TimerData['timers']:
            message += "**R** " + str(int(TimerData['timers'][(champion, "R")]))
        message += "\n"
    message += "_"

    return message
    