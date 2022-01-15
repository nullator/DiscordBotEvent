# TODO добавить обработку сообщений в чате
# TODO добавить обработку параметров при добавлении бота но новый сервер

# Файл config.py в котором хранится токен бота в формате TOKEN = "..."
import config

import asyncio
import discord
import sqlite3
import random
import os
from PIL import Image, ImageDraw, ImageFont

TOKEN = config.TOKEN
prefix = "!"

# Переменная, в которой храниться ссылка на сообщение о старте игры в крокодила
start_tread_message = {}

# Переменная, в которой храниться ссылка на текущего ведущего, загадывающего слово в крокодиле
crocodile_winner = {}

# Переменная, в которой храниться ссылка на тред, в котором играют в крокодила
crocodile_game_tread = {}

# Переменная, в которой храниться scoreboard
scoreboard = {}

bot = discord.Client()

# Создается база данных для хранения данных по игре в крокодила по каждому серверу отдельно
conn = sqlite3.connect("Discord.db")
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS crocodile(
   guildid INT,
   is_crocodile_run INT,
   crocodile_word TEXT,
   winner_counter INT,
   reward INT,
   counter_print INT);
""")
conn.commit()


async def start_crocodile(guildid, sleep=12):
    global scoreboard
    # Флаг, который показывает что победителя нет. Без него иногда некорректно срабатывает определение победителя
    cursor.execute(f'UPDATE crocodile SET winner_counter=0 where guildid={guildid}')
    # Текущая награда за укаданное слово
    cursor.execute(f'UPDATE crocodile SET reward=3 where guildid={guildid}')
    conn.commit()
    for row in cursor.execute(f"SELECT crocodile_word, counter_print FROM crocodile where guildid={guildid}"):
        crocodile_word = row[0]
        counter_print = row[1]
        word = crocodile_word  # Нужно чтобы через время sleep проверить не изменилось ли слово

        # Счетчик определяющий когда печатать scoreboard
        counter_print -= 1
        cursor.execute(f'UPDATE crocodile SET counter_print={counter_print} where guildid={guildid}')

        # Если счетчик опустел, нужно напечатать scoreboard
        if counter_print == 0:
            scorelist = []
            for us, sc in scoreboard[guildid].items():
                scorelist.append([sc, us])
            scorelist.sort(reverse=True)
            await crocodile_game_tread[guildid].send(content="Текущие результаты:", file=discord.File(print_scoreboard(scorelist)))
            cursor.execute(f'UPDATE crocodile SET counter_print=7 where guildid={guildid}')
            conn.commit()
        # Функция засыпает на время sleep, потом просыпается и проверяет нужна ли подсказка если слово не угадали
        await asyncio.sleep(sleep)
        if word == crocodile_word:
            await crocodile_game_tread[guildid].send(f"Слово из  **{len(crocodile_word)}**  букв")
            await first_hint(guildid)
        else:
            # слово угадали, ничего делать не нужно
            pass


async def first_hint(guildid, sleep=12):
    # Награда уменьшается
    cursor.execute(f'UPDATE crocodile SET reward=2 where guildid={guildid}')
    conn.commit()
    for row in cursor.execute(f"SELECT crocodile_word FROM crocodile where guildid={guildid}"):
        crocodile_word = row[0]
        word = crocodile_word  # Нужно чтобы через время sleep проверить не изменилось ли слово
        await asyncio.sleep(sleep)
        # Функция засыпает на время sleep, потом просыпается и проверяет нужна ли вторая подсказка
        print(crocodile_word)
        print(crocodile_word[0])
        if word == crocodile_word:
            await crocodile_game_tread[guildid].send(f"Первая буква  **{crocodile_word[0].upper()}**")
            await second_hint(guildid)
        else:
            # слово угадали, ничего делать не нужно
            pass


async def second_hint(guildid, sleep=24):
    global scoreboard
    # Награда уменьшается
    cursor.execute(f'UPDATE crocodile SET reward=1 where guildid={guildid}')
    conn.commit()
    for row in cursor.execute(f"SELECT crocodile_word FROM crocodile where guildid={guildid}"):
        crocodile_word = row[0]
        word = crocodile_word  # Нужно чтобы через время sleep проверить не изменилось ли слово
        await asyncio.sleep(sleep)
        if word == crocodile_word:
            # Если не отгадали, команда игра ставится на паузу и ждёт нового ведущего, который запустит игру
            await crocodile_game_tread[guildid].send(f"Слово  **{crocodile_word}**  никто не отгадал.\r\nМожно загадывать следующее слово командой **{prefix}крокодил**")
            await crocodile_game_tread[guildid].send("Если не начать новую игру, чат автоматически удалится через 1 час")

            # Данные обнуляются:
            cursor.execute(f'UPDATE crocodile SET is_crocodile_run = 0 where guildid={guildid}')
            cursor.execute(f'UPDATE crocodile SET crocodile_word = "" where guildid={guildid}')
            conn.commit()
            crocodile_winner[guildid] = 0

            # Печатается текущий scoreboard
            scorelist = []
            try:
                for us, sc in scoreboard[guildid].items():
                    scorelist.append([sc, us])
                scorelist.sort(reverse=True)
                if len(scorelist) > 0:
                    await crocodile_game_tread[guildid].send(content="Текущие результаты:", file=discord.File(print_scoreboard(scorelist)))
            except:
                pass
            # Запускается таймер для удаления треда
            await tread_del(guildid)
        else:
            # слово угадали, ничего делать не нужно
            pass


async def tread_del(guildid, sleep=36):
    global scoreboard
    await asyncio.sleep(sleep)
    # Если прошло время sleep и никто не играет, то тред удаляется
    for row in cursor.execute(f"SELECT is_crocodile_run FROM crocodile where guildid={guildid}"):
        is_crocodile_run = row[0]
        if is_crocodile_run == 0:
            scorelist = []
            try:
                for us, sc in scoreboard[guildid].items():
                    scorelist.append([sc, us])
            except:
                pass
            scorelist.sort(reverse=True)
            if len(scorelist) > 0:
                await start_tread_message[guildid].reply(content="Поздравляю победителя!", file=discord.File(print_scoreboard(scorelist, True)))
            await crocodile_game_tread[guildid].delete()

            # Обнуляются данные
            crocodile_game_tread[guildid] = 0
            scoreboard[guildid] = {}
            cursor.execute(f'UPDATE crocodile SET counter_print=5 where guildid={guildid}')
        else:
            # слово угадали, ничего делать не нужно
            pass


def print_scoreboard(scoreboard, final=False):
    new_im = Image.new('RGBA', (320, len(scoreboard) * 24 + 40))
    crown = Image.open("img/crown.png")
    idraw = ImageDraw.Draw(new_im)
    font_1_2 = ImageFont.truetype("img/bahnschrift.ttf", size=18)
    font_1_1 = ImageFont.truetype("img/bahnschrift.ttf", size=16)
    idraw.rectangle((0, 0, 320, 34), fill='gray')
    idraw.text((12, 10), "Игрок", (250, 250, 250), font=font_1_2)
    idraw.text((260, 10), "Очки", (250, 250, 250), font=font_1_2)
    x_offset = 33
    y_offset = 12
    for i in range(0, len(scoreboard)):
        us = str(scoreboard[i][1])
        sc = str(scoreboard[i][0])
        print(len(us))
        if len(us) > 24:
            print(us)
            us = us[:21]
            us = us + "..."
            print(us)
        if i == 0:
            col = (255, 220, 0)
            if final:
                y_offset = 44
        elif i == 1:
            col = (195, 80, 195)
            y_offset = 12
        elif i == 2:
            col = (90, 100, 240)
            y_offset = 12
        else:
            col = (250, 250, 250)
            y_offset = 12
        idraw.text((y_offset, x_offset + 10), us, col, font=font_1_1)
        idraw.text((260, x_offset + 10), sc, col, font=font_1_1)
        idraw.line((0, x_offset + 29, 320, x_offset + 29), fill=(250, 250, 250), width=1)
        x_offset += 24
    y = len(scoreboard) * 24 + 40
    idraw.line((0, 0, 0, y), fill=(250, 250, 250), width=4)
    idraw.line((0, 0, 320, 0), fill=(250, 250, 250), width=4)
    idraw.line((0, 34, 320, 34), fill=(250, 250, 250), width=2)
    idraw.line((248, 0, 248, y), fill=(250, 250, 250), width=2)
    idraw.line((0, y - 2, 320, y - 2), fill=(250, 250, 250), width=4)
    idraw.line((318, 0, 318, y), fill=(250, 250, 250), width=4)
    filename = f'img/score.png'
    if final:
        new_im.paste(crown, (12, 39))
    new_im.save(filename)
    return filename


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print('------')
    # Формирование пустой базы данных для хранения данных по игре в крокодила
    for guild in bot.guilds:
        values = (guild.id, 0, '', 0, 0, 7)
        cursor.execute(f"SELECT guildid FROM crocodile where guildid={guild.id}")
        if cursor.fetchone() == None:
            cursor.execute("INSERT INTO crocodile VALUES(?, ?, ?, ?, ?, ?);", values)
        else:
            cursor.execute(f'UPDATE crocodile SET is_crocodile_run = 0 where guildid={guild.id}')
            cursor.execute(f'UPDATE crocodile SET crocodile_word = "" where guildid={guild.id}')
            cursor.execute(f'UPDATE crocodile SET winner_counter = 0 where guildid={guild.id}')
            cursor.execute(f'UPDATE crocodile SET reward = 0 where guildid={guild.id}')
            cursor.execute(f'UPDATE crocodile SET counter_print = 7 where guildid={guild.id}')
        conn.commit()

        # Инициируются переменные, не хранящиеся в БД
        crocodile_game_tread[guild.id] = 0
        start_tread_message[guild.id] = 0
        crocodile_winner[guild.id] = 0
        scoreboard[guild.id] = {}


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Проверка слова при игре в крокодил
    message_content = str(message.content).lower()

    # Реагирует только на текст в треде
    if crocodile_game_tread[message.guild.id] == 0:
        pass
    elif message.channel.id != crocodile_game_tread[message.guild.id].id:
        pass
    else:
        for row in cursor.execute(f"SELECT is_crocodile_run, winner_counter, crocodile_word, reward FROM crocodile where guildid={message.guild.id}"):
            is_crocodile_run = row[0]
            winner_counter = row[1]
            crocodile_word = row[2]
            reward = row[3]
            if is_crocodile_run == 1 and winner_counter == 0:
                # Ведущий не должен отгадывать слово
                # if message.author == crocodile_winner[message.guild.id]:
                #     pass
                if crocodile_word.lower() == message_content:
                    # Найден победитель
                    cursor.execute(f'UPDATE crocodile SET winner_counter = 1 where guildid={message.guild.id}')
                    conn.commit()
                    # if message.author.display_name in scoreboard[message.guild.id]:
                    #     scoreboard[message.guild.id][message.author.display_name] += 1
                    # else:
                    #     scoreboard[message.guild.id][message.author.display_name] = 1
                    crocodile_winner[message.guild.id] = message.author
                    if scoreboard[message.guild.id] == 0:
                        scoreboard[message.guild.id][message.author.display_name] = reward
                    elif message.author.display_name in scoreboard[message.guild.id]:
                        scoreboard[message.guild.id][message.author.display_name] += reward
                    else:
                        scoreboard[message.guild.id][message.author.display_name] = reward
                    await message.channel.send(f"**{message.author.mention}** угадал слово **{crocodile_word}** и загадывает новое слово")
                    with open("crocodile.txt", encoding="utf-8") as f:
                        content = f.readlines()
                    content = [x.strip() for x in content]
                    word_index = random.randint(0, len(content)-1)
                    crocodile_word = content[word_index]
                    cursor.execute(f'UPDATE crocodile SET crocodile_word = "{crocodile_word}" where guildid={message.guild.id}')
                    conn.commit()
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
                    await crocodile_winner[message.guild.id].send(f"Загадано слово:\r\n"
                                              f"```css\r\n{crocodile_word}\r\n```")
                    await start_crocodile(message.guild.id)
                    pass
                else:
                    # ничего не делать
                    pass

    if message.content == prefix + "крокодил":
        # Из базы данных загружаются данные по текущему серверу
        for row in cursor.execute(f"SELECT is_crocodile_run, crocodile_word FROM crocodile where guildid={message.guild.id}"):
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
                    cursor.execute(f'UPDATE crocodile SET crocodile_word = "{crocodile_word}" where guildid={message.guild.id}')
                    conn.commit()
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
                    cursor.execute(f'UPDATE crocodile SET is_crocodile_run = 1 where guildid={message.guild.id}')
                    conn.commit()
                    crocodile_game_tread[message.guild.id] = tread
                    await tread.send(f"**Правила:**\r\n"
                                     f"{message.author.mention} получил в ЛС загаданное слово и стал ведущим игры.\r\n"
                                     f"Ведущий должен объяснить загаданное слово, а остальные игроки его отгадать.\r\n"
                                     f"При объяснении слов запрещено использовать однокоренные слова.\r\n"
                                     f"Отгадавший слово станет новым ведущим и получит от бота сообщение с новым словом.\r\n"
                                     f"За отгаданные слова начисляются очки, в конце будет подведён итог.")
                    await message.author.send(f"Загадано слово:\r\n"
                                              f"```css\r\n{crocodile_word}\r\n```")
                    await start_crocodile(message.guild.id)
                else:
                    with open("crocodile.txt", encoding="utf-8") as f:
                        content = f.readlines()
                    content = [x.strip() for x in content]
                    word_index = random.randint(0, len(content) - 1)
                    crocodile_word = content[word_index]
                    cursor.execute(f'UPDATE crocodile SET crocodile_word = "{crocodile_word}" where guildid={message.guild.id}')
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
                    cursor.execute(f'UPDATE crocodile SET is_crocodile_run = 1 where guildid={message.guild.id}')
                    conn.commit()
                    await crocodile_game_tread[message.guild.id].send(f"{message.author.mention} объясняет слово, остальные должны угадать")
                    await message.author.send(f"Загадано слово:\r\n"
                                              f"```css\r\n{crocodile_word}\r\n```")
                    await start_crocodile(message.guild.id)

            else:
                pass


bot.run(TOKEN)
