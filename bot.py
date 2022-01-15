import config
import asyncio
import discord
import sqlite3

TOKEN = config.TOKEN
prefix = "!"

bot = discord.Client()

# Создается база данных для хранения данных по игре в крокодила по каждому серверу отдельно
conn = sqlite3.connect("Discord.db")
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS crocodile(
   guildid INT,
   is_crocodile_run INT,
   crocodile_word TEXT,
   chan_id INT);
""")
conn.commit()


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print('------')
    # Формирование пустой базы данных для хранения данных по игре в крокодила
    for guild in bot.guilds:
        values = (guild.id, 0, '', 0)
        cursor.execute(f"SELECT guildid FROM crocodile where guildid={guild.id}")
        if cursor.fetchone() == None:
            cursor.execute("INSERT INTO crocodile VALUES(?, ?, ?, ?);", values)
        else:
            cursor.execute(f'UPDATE crocodile SET is_crocodile_run = 0 where guildid={guild.id}')
            cursor.execute(f'UPDATE crocodile SET crocodile_word = "" where guildid={guild.id}')
            cursor.execute(f'UPDATE crocodile SET chan_id = 0 where guildid={guild.id}')
        conn.commit()


@bot.event
async def on_message(message):
    if message.content == prefix + "крокодил":
        for row in cursor.execute(f"SELECT is_crocodile_run, crocodile_word, chan_id FROM crocodile where guildid={message.guild.id}"):
            print(row[0])
            print(row[1])
            print(row[2])

bot.run(TOKEN)
