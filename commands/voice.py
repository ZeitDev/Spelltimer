import config
import asyncio

from nextcord.ext import commands
from functions._tts import tts


class Voice(commands.Cog):
    @commands.command()
    async def Join(self, ctx):
        """Bot joins the voice channel for summoner spell announcements"""
        await ctx.message.delete()

        if ctx.author.voice and config.VariableDict['voice_channel'] == None:
            voice_channel = ctx.author.voice.channel
            config.VariableDict['voice_channel'] = await voice_channel.connect()
            await tts('Hello')
        elif not ctx.author.voice:
            await ctx.channel.send(f'Please join a voice channel first {ctx.author.mention}!', delete_after=10)
        elif ctx.author.voice.channel != None:
            await ctx.channel.send(f'Already connected! {ctx.author.mention}', delete_after=10)

    @commands.command()
    async def Leave(self, ctx):
        """Bot leaves the voice channel"""
        await ctx.message.delete()

        if config.VariableDict['voice_channel'] != None:
            await tts('Bye')
            
            await asyncio.sleep(0.5)
            await ctx.voice_client.disconnect()
            config.VariableDict['voice_channel'] = None
        else:
            await ctx.channel.send(f'I am not connected to a voice channel! {ctx.author.mention}', delete_after=10)

    @commands.command()
    async def Mute(self, ctx):
        """Mutes the bot"""
        await ctx.message.delete()

        config.VariableDict['muted'] = True
        await ctx.channel.send(f'I am muted now! {ctx.author.mention}', delete_after=10)

    @commands.command()
    async def Unmute(self, ctx):
        """Unmutes the bot"""
        await ctx.message.delete()

        config.VariableDict['muted'] = False
        await ctx.channel.send(f'I am no longer muted! {ctx.author.mention}', delete_after=5)

def setup(bot):
    bot.add_cog(Voice(bot))