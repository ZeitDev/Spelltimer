from nextcord.ext import commands

class General(commands.Cog):
    @commands.command(usage='')
    async def Hello(self, ctx):
        """Testing command"""
        await ctx.message.delete()

        await ctx.channel.send(f'Hello {ctx.author.display_name}!') 

def setup(bot):
    bot.add_cog(General(bot))