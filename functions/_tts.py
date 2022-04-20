import asyncio
import config
import nextcord
from gtts import gTTS

async def tts(text):
    voice_channel = config.VariableDict['voice_channel']
    if voice_channel == None: return
    if config.VariableDict['muted']: return

    request = gTTS(text, slow=True)
    request.save('cache/audio/tts_file.mp3')

    if not voice_channel.is_playing():
        voice_channel.play(nextcord.FFmpegPCMAudio(executable="C:/ffmpeg/bin/ffmpeg.exe", source="C:/Users/leonz/Code/Python/Spelltimer/cache/audio/tts_file.mp3"))
        while voice_channel.is_playing():
            await asyncio.sleep(0.1)
