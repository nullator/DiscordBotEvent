# TODO добавить обработку сообщений в чате
# TODO добавить обработку параметров при добавлении бота но новый сервер
# TODO добавить игровую механику
# TODO добавить формирование итогового scoreboard

# Файл config.py в котором хранится токен бота в формате TOKEN = "..."
import config

import asyncio
import discord
import sqlite3
import random
import os

TOKEN = config.TOKEN
prefix = "!"

# Глобальная переменная, в которой храниться ссылка на сообщение о старте игры в крокодила
start_tread_message = {}

# Глобальная переменная, в которой храниться ссылка на текущего ведущего, загадывающего слово в крокодиле
crocodile_winner = {}

# Глобальная переменная, в которой храниться ссылка на тред, в котором играют в крокодила
crocodile_game_tread = {}

bot = discord.Client()

# Создается база данных для хранения данных по игре в крокодила по каждому серверу отдельно
conn = sqlite3.connect("Discord.db")
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS crocodile(
   guildid INT,
   is_crocodile_run INT,
   crocodile_word TEXT);
""")
conn.commit()


async def start_crocodile(sleep = 120):
    pass


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print('------')
    # Формирование пустой базы данных для хранения данных по игре в крокодила
    for guild in bot.guilds:
        values = (guild.id, 0, '')
        cursor.execute(f"SELECT guildid FROM crocodile where guildid={guild.id}")
        if cursor.fetchone() == None:
            cursor.execute("INSERT INTO crocodile VALUES(?, ?, ?);", values)
        else:
            cursor.execute(f'UPDATE crocodile SET is_crocodile_run = 0 where guildid={guild.id}')
            cursor.execute(f'UPDATE crocodile SET crocodile_word = "" where guildid={guild.id}')
        conn.commit()

        # Инициируются переменные, не хранящиеся в БД
        crocodile_game_tread[guild.id] = 0
        start_tread_message[guild.id] = 0
        crocodile_winner[guild.id] = 0


@bot.event
async def on_message(message):
    if message.content == prefix + "крокодил":
        # Из базы данных загружаются данные по текущему серверу
        for row in cursor.execute(f"SELECT is_crocodile_run, crocodile_word, chan_id FROM crocodile where guildid={message.guild.id}"):
            is_crocodile_run = row[0]
            crocodile_word = row[1]
            # Если игра вкрокодила не запущена:
            if is_crocodile_run == 0:
                # Проверяется создан ли тред для игры в крокодила, при необходимости создается:
                if crocodile_game_tread[message.guild.id] == 0:
                    tread = await message.channel.create_thread(name="Играем в крокодила", message=message)
                    start_tread_message[message.guild.id] = message
                    # Для того чтобы не было слишком частых повторов, вместо простого рандомного выбора
                    # сначала в случайном порядке перебираются все слова из базы со словами, загаданные слова
                    # перемещаютя в другой файл, когда слова в основном файле кончаются все сбрасывается
                    with open("crocodile.txt", encoding="utf-8") as f:
                        content = f.readlines()
                    content = [x.strip() for x in content]
                    word_index = random.randint(0, len(content)-1)
                    crocodile_word = content[word_index]
                    with open('crocodile-dropped.txt', 'a', encoding="utf-8") as file:
                        file.write(content[word_index]+"\n")
                    content.pop(word_index)
                    with open("crocodile.txt", "w", encoding="utf-8") as file:
                        print(*content, file=file, sep="\n")
                    if len(content) == 0:
                        with open('crocodile.txt', 'tw', encoding='utf-8') as f:
                            pass
                        os.rename('crocodile.txt', 'crocodile.temp')
                        os.rename('crocodile-dropped.txt', 'crocodile.txt')
                        os.rename('crocodile.temp', 'crocodile-dropped.txt')
                    crocodile_winner[message.guild.id] = message.author
                    is_crocodile = 1
                    chan_id = tread
                    await tread.send(f"**Правила:**\r\n"
                                     f"{message.author.mention} получил в ЛС загаданное слово и стал ведущим игры.\r\n"
                                     f"Ведущий должен объяснить загаданное слово, а остальные игроки его отгадать.\r\n"
                                     f"При объяснении слов запрещено использовать однокоренные слова.\r\n"
                                     f"Отгадавший слово станет новым ведущим и получит от бота сообщение с новым словом.\r\n"
                                     f"За отгаданные слова начисляются очки, в конце будет подведён итог.")
                    await message.author.send(f"Загадано слово:\r\n"
                                              f"```css\r\n{crocodile_word}\r\n```")
                    await start_crocodile()
                else:
                    with open("crocodile.txt", encoding="utf-8") as f:
                        content = f.readlines()
                    content = [x.strip() for x in content]
                    word_index = random.randint(0, len(content) - 1)
                    crocodile_word = content[word_index]
                    with open('crocodile-dropped.txt', 'a', encoding="utf-8") as file:
                        file.write(content[word_index] + "\n")
                    content.pop(word_index)
                    with open("crocodile.txt", "w", encoding="utf-8") as file:
                        print(*content, file=file, sep="\n")
                    if len(content) == 0:
                        with open('crocodile.txt', 'tw', encoding='utf-8') as f:
                            pass
                        os.rename('crocodile.txt', 'crocodile.temp')
                        os.rename('crocodile-dropped.txt', 'crocodile.txt')
                        os.rename('crocodile.temp', 'crocodile-dropped.txt')
                    crocodile_winner[message.guild.id] = message.author
                    is_crocodile = 1
                    await crocodile_game_tread[message.guild.id].send(f"{message.author.mention} объясняет слово, остальные должны угадать")
                    await message.author.send(f"Загадано слово:\r\n"
                                              f"```css\r\n{crocodile_word}\r\n```")
                    await start_crocodile()

            else:
                pass


bot.run(TOKEN)
