import config
import asyncio

from nextcord.ext import commands

from functions import _timer

class Timer(commands.Cog):
    @commands.command(usage=' , !start summoner_name')
    async def Start(self, ctx, *args):
        """Starts the timer"""
        await ctx.message.delete()

        if not config.VariableDict['timer_running']:
            await _timer.Timer().Initialize(ctx, args)
        else:
            await _timer.Timer().Restart(ctx, args)

    @commands.command(usage='')
    async def Stop(self, ctx):
        """Stops the timer"""
        await ctx.message.delete()   

        if config.VariableDict['timer_running']:
            await _timer.Timer().Stop()
        else: 
            await ctx.channel.send(f'No running timer found! {ctx.author.mention}', delete_after=10)

    @commands.command(usage='')
    async def S(self, ctx):
        """Starts the timer for 'Shiro Aoi'"""
        await ctx.message.delete()

        args = ['Shiro', 'Aoi']
        if not config.VariableDict['timer_running']:
            await _timer.Timer().Initialize(ctx, args)
        else:
            await _timer.Timer().Restart(ctx, args)
        
def setup(bot):
    bot.add_cog(Timer(bot))