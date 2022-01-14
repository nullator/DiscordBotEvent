import config
import asyncio
import discord

TOKEN = config.TOKEN
prefix = "!"

bot = discord.Client()

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print()
    print('------')


@bot.event
async def on_message(message):
    if message.content == prefix + "крокодил":
        await message.channel.send("Hello Word")


bot.run(TOKEN)
