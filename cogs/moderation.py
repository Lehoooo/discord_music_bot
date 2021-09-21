# Written By Leho | leho.dev | github.com/lehoooo
import discord
from discord.ext import commands
import json

try:
    configopen = open("config.json", "r")
    config = json.load(configopen)
    configopen.close()
except Exception as e:
    print("Error Loading Config " + str(e))
    exit()


class moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def invite(self, ctx):
        await ctx.send(config['invite'])




def setup(bot):
    bot.add_cog(moderation(bot))
