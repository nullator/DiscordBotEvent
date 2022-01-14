import config
import asyncio
import discord

TOKEN = config.TOKEN

bot = discord.Client()

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print()
    print('------')

bot.run(TOKEN)
