# import
import os
import nextcord

from dotenv import load_dotenv
from nextcord.ext import commands

import config

# Initialize
load_dotenv()
token = os.getenv('nextcord_token')
prefix = config.SettingsDict['prefix']

intents = nextcord.Intents.default()
intents.members = True

description = '''
Summoner Spell Timer
'''

bot = commands.Bot(command_prefix=commands.when_mentioned_or(prefix), description=description, case_insensitive=True)
config.VariableDict['bot'] = bot

print('> Loading Commands')
for filename in os.listdir('./commands'):
    if filename.endswith('.py'):
        bot.load_extension(f'commands.{os.path.splitext(filename)[0]}')
        print(f'{os.path.splitext(filename)[0]} loaded')
print()


# main
@bot.event
async def on_ready():
    print(f'> Starting nextcord Bot = {bot.user}')
    print('-'*40)
    await bot.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.watching, name=f'{prefix}help'))

bot.run(token)
