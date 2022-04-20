import re
import cv2
import functools
import pyautogui
import pytesseract
import numpy as np
from PIL import Image

import config
from functions import _riot
from functions._tts import tts

# Settings
print_chat = False
save_images = False
from_example = False

game_time_mod = 2
gametime_by_level = [65, 125, 155, 185, 245, 335, 395, 485, 605, 695, 815, 965, 1085, 1235, 1415, 1535, 1685, 10000]

replace_misc = { "|": "1", "’": "'", "Hexflash": "Flash", "Smite": "" }
replace_champs = { "KogMaw": "Kog'Maw" }

chatwindow_x_start = 80
chatwindow_x_end = 600
chatwindow_y_start = 830
chatwindow_y_end = 1030

name_color_range = ([0, 0, 80], [100, 100, 255])
spell_color_range = ([0, 70, 120], [20, 180, 255])
status_color_range = ([90, 150, 100], [190, 255, 200])

class OCR():
    async def UpdateEnemyChampions(self, enemy_champions):
        for eventtype in GetEvents():
            for event in eventtype:
                if not event['champion'] in enemy_champions:
                    enemy_champions.append(event['champion'])
        return enemy_champions

    async def UpdateTimerData(self, TimerData):
        (alive_events, level_events, summoner_spell_events, ult_events) = GetEvents()

        await UpdateLevels(TimerData, level_events)
        await UpdateSummonerSpells(TimerData, summoner_spell_events)
        await UpdateUltimates(TimerData, ult_events)
        await UpdateTimers(TimerData)

# Helper Functions
def GetEvents():
    filtered_image = TakeAndFilterScreenshot()

    try: 
        chat = pytesseract.image_to_string(filtered_image, timeout=1)
        if print_chat: print('Chat:', chat)
    except: return ([], [], [], [])

    eventtypes = ParseEventtypes(chat)
    return eventtypes

def TakeAndFilterScreenshot():
    if from_example: image = Image.open('cache/debug/images/example.png')
    else: image = pyautogui.screenshot()
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)[chatwindow_y_start:chatwindow_y_end, chatwindow_x_start:chatwindow_x_end]

    enemy_names = cv2.inRange(image, np.array(name_color_range[0]), np.array(name_color_range[1]))
    enemy_spells = cv2.inRange(image, np.array(spell_color_range[0]), np.array(spell_color_range[1]))
    enemy_status = cv2.inRange(image, np.array(status_color_range[0]), np.array(status_color_range[1]))
    filtered_image = cv2.bitwise_or(cv2.bitwise_or(enemy_names, enemy_spells), enemy_status)
    filtered_image = functools.reduce((lambda a,b : cv2.bitwise_or(a, b)), [enemy_names, enemy_spells],  enemy_status)

    if save_images:
        cv2.imwrite('cache/debug/images/image.png', image)
        cv2.imwrite('cache/debug/images/enemy_name.png', enemy_names)
        cv2.imwrite('cache/debug/images/enemy_spell.png', enemy_spells)
        cv2.imwrite('cache/debug/images/enemy_status.png', enemy_status)
        cv2.imwrite('cache/debug/images/filtered_image.png', filtered_image)

    return filtered_image

def ParseEventtypes(chat):
    chat = replace(chat, replace_misc)
    chat = replace(chat, replace_champs)

    LeagueData = GetLeagueData()
    alive_events, level_events, summoner_spell_events, ult_events = [], [], [], []
    for line in chat.splitlines():
        match = re.match(LeagueData['alive_match'], line)
        if match:
            alive_events.append(match.groupdict())
            continue
        match = re.match(LeagueData['level_match'], line)
        if match:
            level_events.append((match.groupdict()))
            continue
        match = re.match(LeagueData['summoner_spell_match'], line)
        if match:
            summoner_spell_events.append(match.groupdict())
            continue
        match = re.match(LeagueData['ult_match'], line)
        if match:
            ult_events.append(match.groupdict())
            continue

    return (alive_events, level_events, summoner_spell_events, ult_events)

def replace(text, replacements):
    text = re.sub('({})'.format('|'.join(map(re.escape, replacements.keys()))), lambda m: replacements[m.group()], text)
    return text

def GetLeagueData():
    summoner_spells         = _riot.DataDragon().GetSummonerSpells()
    champion_ults           = _riot.DataDragon().GetChampionUlts()

    champion_match          = "("  + (')|('.join(map((lambda x : re.escape(x)), list(champion_ults)))) + ")"
    summoner_spell_prematch = "("  + (')|('.join(map((lambda x : re.escape(x)), list(summoner_spells)))) + ")"

    alive_match             = re.compile("(?P<champion>(" + champion_match + "))( - Alive)")
    level_match             = re.compile("(?P<champion>(" + champion_match + "))( - Level )(?P<level>\d+)")
    summoner_spell_match    = re.compile("(?P<champion>(" + champion_match + ")) (?P<summoner_spell>(" + summoner_spell_prematch + "))")
    champion_ult_match      = re.compile("(?P<champion>(" + champion_match + ")) R")

    LeagueData = {
        'summoner_spells': summoner_spells,
        'champion_ults': champion_ults,
        'alive_match': alive_match,
        'level_match': level_match,
        'summoner_spell_match': summoner_spell_match,
        'ult_match': champion_ult_match
    }
    return LeagueData

async def UpdateLevels(TimerData, level_events):
    estimated_level = [i for i in range(len(gametime_by_level)) if gametime_by_level[i]+(game_time_mod*30) > TimerData['game_time']][0] + 1

    for champion in TimerData['champion_levels']:
        if TimerData['champion_levels'][champion] < estimated_level:
            TimerData['champion_levels'][champion] = estimated_level

    for event in level_events:
        TimerData['champion_levels'][event['champion']] = int(event['level'])

async def UpdateSummonerSpells(TimerData, summoner_spell_events):
    LeagueData = GetLeagueData()
    for event in summoner_spell_events:
        if not (event["champion"], event["summoner_spell"]) in TimerData['timers']:
            if event["summoner_spell"] == "Teleport":
                TimerData['timers'][event["champion"], event["summoner_spell"]] = 360 - config.SettingsDict['summoner_delay']
            elif event["summoner_spell"] == "Unleashed Teleport":
                TimerData['timers'][event["champion"], event["summoner_spell"]] = 240 - config.SettingsDict['summoner_delay']
            else:
                TimerData['timers'][event["champion"], event["summoner_spell"]] = LeagueData['summoner_spells'][event["summoner_spell"]][0] - config.SettingsDict['summoner_delay']
            await tts(f'{event["champion"]} used {event["summoner_spell"]}')

async def UpdateUltimates(TimerData, ult_events):
    LeagueData = GetLeagueData()
    for event in ult_events:
        if not (event["champion"], "R") in TimerData['timers']:
            if TimerData['champion_levels'][event["champion"]] < 11:
                cooldown = LeagueData['champion_ults'][event["champion"]][0] - config.SettingsDict['summoner_delay']
                if cooldown > 30: TimerData['timers'][(event["champion"], "R")] = cooldown
            elif TimerData['champion_levels'][event["champion"]] < 16:
                cooldown = LeagueData['champion_ults'][event["champion"]][1] - config.SettingsDict['summoner_delay']
                if cooldown > 30: TimerData['timers'][(event["champion"], "R")] = cooldown
            else:
                cooldown = LeagueData['champion_ults'][event["champion"]][2] - config.SettingsDict['summoner_delay']
                if cooldown > 30: TimerData['timers'][(event["champion"], "R")] = cooldown

async def UpdateTimers(TimerData):
    finished = list()
    for timer in TimerData['timers']:
        TimerData['timers'][timer] -= TimerData['delta_time']
        if TimerData['timers'][timer] < 0:
            finished.append(timer)

    for timer in finished:
        if timer[1] == "R": await tts(f'{timer[0]} Ultimate is back up!')
        else: await tts(f'{timer[0]} {timer[1]} is back up!')
        TimerData['timers'].pop(timer)


