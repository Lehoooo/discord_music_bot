# Written By Leho | leho.dev | github.com/lehoooo
import discord
from discord.ext import commands
import json
import sys

try:
    with open("config.json", "r") as configopen:
        config = json.load(configopen)

except Exception as e:
    print("Error Loading Config " + str(e))
    sys.exit(9)


class moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def invite(self, ctx):
        await ctx.send(config['invite'])




def setup(bot):
    bot.add_cog(moderation(bot))
