# Written By Leho | leho.dev | github.com/lehoooo
import discord
from discord.ext import commands
from discord.ext import tasks
import requests
import os
from datetime import datetime
import json

bot = commands.Bot(command_prefix='>')
try:
    configopen = open("config.json", "r")
    config = json.load(configopen)
    configopen.close()
except Exception as e:
    print("Error Loading Config " + str(e))
    exit()


TOKEN = str(config['token'])

print("Starting")

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="🐲"))
    print("Logged in as: " + bot.user.name + "#" + bot.user.discriminator)
    print("Ready")
    bot.load_extension("cogs.moderation")
    bot.load_extension("cogs.music")

bot.run(TOKEN)