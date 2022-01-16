# Файл config.py в котором хранится токен бота в формате TOKEN = "..."
import config

import asyncio
import discord
import time
import random
import os
from PIL import Image, ImageDraw, ImageFont

TOKEN = config.TOKEN
prefix = "!"

# Переменные для игры в крокодила:
# Переменная, в которой храниться ссылка на сообщение о старте игры в крокодила
start_tread_message = {}
# Переменная, в которой храниться ссылка на текущего ведущего, загадывающего слово в крокодиле
crocodile_winner = {}
# Переменная, в которой храниться ссылка на тред, в котором играют в крокодила
crocodile_game_tread = {}
# Переменная, в которой храниться scoreboard
scoreboard = {}
# Флаг о том, что игра в крокодила уже запущена
is_crocodile_run = {}
# Загаданное слово
crocodile_word = {}
# Флаг о том, что победитель уже найден (нужен чтобы не было бага)
winner_counter = {}
# Текущая награда за угаданное слово
reward = {}
# Счетчик, который нужен чтобы раз в n ходов печатать промежуточную таблицу лидеров
counter_print = {}

# Переменные для отслеживания хоста AmongUs:
# Хостер AmongUs
hoster = {}
# Флаг о том, что отслеживание хоста уже запущено
is_host_progress = {}
# Текущий статус в AmongUs
now_game_status = {}
# Этот параметр нужен чтобы отслеживать изменение статуса и обновлять его в embed
last_game_status = {}
# Ссылка на embed. Нужно чтобы потом его редактировать
host_message = {}
# Ссылка на сообщение, которым запущена команда. Нужно чтобы уведомлять о скором закрытии лобби
start_host_message = {}
# Этот флаг нужен, чтобы выводить уведомление о закрытии лобби только 1 раз и не спамить им
warning_message = {}
# Флаг о том, хостит ли сейчас хост своё лобби
is_hosting = {}
# Момент создания лобби
start_hosting = {}

intents = discord.Intents.all()
bot = discord.Client(intents=intents)


async def start_crocodile(guildid, sleep=120):
    global scoreboard
    global counter_print

    winner_counter[guildid] = 0  # Флаг сбрасывается
    reward[guildid] = 3  # Максимальная награда если угадать без подсказок за время sleep
    word = crocodile_word[guildid]  # Нужно чтобы через время sleep проверить не изменилось ли слово
    counter_print[guildid] -= 1

    # Если счетчик опустел, нужно напечатать scoreboard
    if counter_print[guildid] == 0:
        scorelist = []
        for us, sc in scoreboard[guildid].items():
            scorelist.append([sc, us])
        scorelist.sort(reverse=True)
        await crocodile_game_tread[guildid].send(content="Текущие результаты:", file=discord.File(print_scoreboard(scorelist)))
        counter_print[guildid] = 7

    # Функция засыпает на время sleep, потом просыпается и проверяет нужна ли подсказка если слово не угадали
    await asyncio.sleep(sleep)
    if word == crocodile_word[guildid]:
        await crocodile_game_tread[guildid].send(f"Слово из  **{len(crocodile_word[guildid])}**  букв")
        await first_hint(guildid)
    else:
        # слово угадали, ничего делать не нужно
        pass


async def first_hint(guildid, sleep=120):
    reward[guildid] = 2  # Награда уменьшается
    word = crocodile_word[guildid]  # Нужно чтобы через время sleep проверить не изменилось ли слово
    await asyncio.sleep(sleep)

    # Функция засыпает на время sleep, потом просыпается и проверяет нужна ли вторая подсказка
    if word == crocodile_word[guildid]:
        await crocodile_game_tread[guildid].send(f"Первая буква  **{crocodile_word[guildid][0].upper()}**")
        await second_hint(guildid)
    else:
        # слово угадали, ничего делать не нужно
        pass


async def second_hint(guildid, sleep=240):
    global scoreboard
    # Таймер до удаления треда, секунды
    sleep_to_delete = 3600

    reward[guildid] = 1  # Награда уменьшается до минимальной
    word = crocodile_word[guildid]  # Нужно чтобы через время sleep проверить не изменилось ли слово

    # Функция засыпает на время sleep, потом просыпается и проверяет нужна ли последняя подсказка
    await asyncio.sleep(sleep)
    if word == crocodile_word[guildid]:
        # Если слово не отгадали, команда игра ставится на паузу и ждёт нового ведущего, который запустит игру
        await crocodile_game_tread[guildid].send(f"Слово  **{crocodile_word[guildid]}**  никто не отгадал.\r\nМожно загадывать следующее слово командой **{prefix}крокодил**")
        await crocodile_game_tread[guildid].send(f"Если не начать новую игру, тред автоматически удалится через {sleep_to_delete/60} минут")

        # Данные обнуляются:
        is_crocodile_run[guildid] = 0
        crocodile_winner[guildid] = 0

        # Печатается текущий, пока ещё промежуточный scoreboard
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
        await tread_del(guildid, sleep_to_delete, word)
    else:
        # слово угадали, ничего делать не нужно
        pass


async def tread_del(guildid, sleep, last_word):
    global scoreboard
    global is_crocodile_run

    await asyncio.sleep(sleep)
    # Если прошло время sleep и никто не играет, то тред удаляется
    # Одновременно делается проверка, если загаданное слово за время sleep поменялось, значит кто-тол запускал игру
    # и удаление треда уже не актуально. Нужно чтобы случайно не удалить тред.
    if is_crocodile_run[guildid] == 0 and crocodile_word[guildid] == last_word:
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
        counter_print[guildid] = 7
    else:
        # За время sleep игра продолжилась, удалять тред не нужно
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


async def game_iterator(host, guildid):
    game_time = 0
    while is_host_progress[guildid] == 1:
        # Проверяется играет ли хост в амонг
        try:
            now_game_status[guildid] = host.activities[-1].details
            if host.activities[-1].name != "Among Us":
                now_game_status[guildid] = ""
        except:
            now_game_status[guildid] = ""

        # Если не играет, то отслеживание прекращается через 10 секунд, все параметры обнуляются
        if now_game_status[guildid] == "":
            game_des = f"Не получается отследить статус лобби. Возможно хост вышел из игры."
            embed = discord.Embed(description=game_des, color=0xda00e7)
            embed.set_author(name=f"ඞ      Лобби {host.display_name}      ඞ")
            await host_message[guildid].edit(embed=embed)
            is_host_progress[guildid] = 0
            warning_message[guildid] = 0

            # Спит 10 секунд и завершает работу команды
            await asyncio.sleep(10)
            game_des = f"Работа команды завершена.\r\nДля повторного запуска нужно ввести команду !host"
            embed = discord.Embed(description=game_des, color=0xda00e7)
            embed.set_author(name=f"ඞ      Лобби {host.display_name}      ඞ")
            await host_message[guildid].edit(embed=embed)

        # Если с момента прошлой проверки статус не поменялся
        elif last_game_status[guildid] == now_game_status[guildid]:
            # Если в своем лобби, ножно првоерить как давно оно создано
            if is_hosting[guildid] == 1:
                # Проверяет как давно создано лобби
                game_time = round(time.time()) - start_hosting[guildid]
                game_des = f"{host.display_name} хостит лобби\r\n{sec_to_time(game_time)} | 10:30"
                embed = discord.Embed(description=game_des, color=0xda00e7)
                embed.set_author(name=f"ඞ      Лобби {host.display_name}      ඞ")
                await host_message[guildid].edit(embed=embed)
                # По опыту лобби закрывается в случайный момент, в среднем между 10:30 и 10:50
                if game_time > 570 and warning_message[guildid] == 0:
                    await start_host_message[guildid].reply("До закрытия лобби осталось меньше минуты!")
                    warning_message[guildid] = 1
            else:
                pass
        # Если предыдущий статус поменялся на "Hosting a game", значит хост создал лобби
        # нужно иницииривать переменные, запомнить время старта лобби
        elif now_game_status[guildid] == "Hosting a game":
            is_hosting[guildid] = 1
            start_hosting[guildid] = round(time.time())
            last_game_status[guildid] = now_game_status[guildid]

        # Если хост запустил игру из своего лобби, нужно обновить статус
        elif now_game_status[guildid] == "Playing" and last_game_status[guildid] == "Hosting a game":
            is_hosting[guildid] = 0
            game_des = f"{host.display_name} запустил игру"
            embed = discord.Embed(description=game_des, color=0xda00e7)
            embed.set_author(name=f"ඞ      Лобби {host.display_name}      ඞ")
            await host_message[guildid].edit(embed=embed)
            last_game_status[guildid] = now_game_status[guildid]
            warning_message[guildid] = 0

        # Если хост вышел из своего лобби и находится в меню
        elif now_game_status[guildid] != "Hosting a game" and last_game_status[guildid] == "Hosting a game":
            is_hosting[guildid] = 0
            game_des = f"{host.display_name} сейчас не хостит"
            embed = discord.Embed(description=game_des, color=0xda00e7)
            embed.set_author(name=f"ඞ      Лобби {host.display_name}      ඞ")
            await host_message[guildid].edit(embed=embed)
            last_game_status[guildid] = now_game_status[guildid]
            warning_message[guildid] = 0
        await asyncio.sleep(1)


def sec_to_time(seconds):
    hour = seconds // 3600
    minuts = (seconds // 60) % 60
    sec = seconds % 60
    if minuts < 10:
        minuts = f"0{minuts}"
    if sec < 10:
        sec = f"0{sec}"
    if hour == 0:
        return f"{minuts}:{sec}"
    else:
        return f"{hour}:{minuts}:{sec}"


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print('------')
    for guild in bot.guilds:
        # Инициируются переменные для каждлого сервера отдельно
        # Для крокодила:
        crocodile_game_tread[guild.id] = 0
        start_tread_message[guild.id] = 0
        crocodile_winner[guild.id] = 0
        scoreboard[guild.id] = {}
        is_crocodile_run[guild.id] = 0
        crocodile_word[guild.id] = ""
        winner_counter[guild.id] = 0
        reward[guild.id] = 0
        counter_print[guild.id] = 7
        # Для отслеживания хоста:
        hoster[guild.id] = 0
        is_host_progress[guild.id] = 0
        now_game_status[guild.id] = 0
        last_game_status[guild.id] = 0
        host_message[guild.id] = 0
        start_host_message[guild.id] = 0
        warning_message[guild.id] = 0
        is_hosting[guild.id] = 0
        start_hosting[guild.id] = 0


@bot.event
async def on_guild_join(server):
    # Инициируются переменные для нового сервера
    # Для крокодила:
    crocodile_game_tread[server.id] = 0
    start_tread_message[server.id] = 0
    crocodile_winner[server.id] = 0
    scoreboard[server.id] = {}
    is_crocodile_run[server.id] = 0
    crocodile_word[server.id] = ""
    winner_counter[server.id] = 0
    reward[server.id] = 0
    counter_print[server.id] = 7
    # Для отслеживания хоста:
    hoster[server.id] = 0
    is_host_progress[server.id] = 0
    now_game_status[server.id] = 0
    last_game_status[server.id] = 0
    host_message[server.id] = 0
    start_host_message[server.id] = 0
    warning_message[server.id] = 0
    is_hosting[server.id] = 0
    start_hosting[server.id] = 0

    # Обратная связь
    nullator = await bot.fetch_user(270956993890484225)
    await nullator.send(f"Бот добавлен на сервер {server.name}")


@bot.event
async def on_message(message):
    global is_crocodile_run
    global crocodile_word

    if message.author == bot.user:
        return

    # Проверка слова при игре в крокодил
    message_content = str(message.content).lower()

    # Реагирует только на текст в треде
    if is_crocodile_run[message.guild.id] == 1 and message.channel.id == crocodile_game_tread[message.guild.id].id:

        if is_crocodile_run[message.guild.id] == 1 and winner_counter[message.guild.id] == 0:
            # Ведущий не должен отгадывать слово
            if message.author == crocodile_winner[message.guild.id]:
                pass
            elif crocodile_word[message.guild.id].lower() == message_content:
                # Найден победитель
                winner_counter[message.guild.id] = 1
                crocodile_winner[message.guild.id] = message.author

                # Победителю начисляются очки. Если для него нет записи в scoreboard, ему просто начисляется reward
                if scoreboard[message.guild.id] == 0:
                    scoreboard[message.guild.id][message.author.display_name] = reward[message.guild.id]
                elif message.author.display_name in scoreboard[message.guild.id]:
                    scoreboard[message.guild.id][message.author.display_name] += reward[message.guild.id]
                else:  # Скорее всего это условие лишнее, оставил на всякий случай
                    scoreboard[message.guild.id][message.author.display_name] = reward[message.guild.id]
                await message.channel.send(f"**{message.author.mention}** угадал слово **{crocodile_word[message.guild.id]}** и загадывает новое слово")

                # Выбирается новое слово и игра запускается повторно с новым ведущим
                with open("crocodile.txt", encoding="utf-8") as f:
                    content = f.readlines()
                content = [x.strip() for x in content]
                word_index = random.randint(0, len(content)-1)
                crocodile_word[message.guild.id] = content[word_index]
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
                                          f"```css\r\n{crocodile_word[message.guild.id]}\r\n```")
                await start_crocodile(message.guild.id)
                pass
            else:
                # ничего не делать
                pass

    if message.content == prefix + "крокодил":
        # Если игра вкрокодила не запущена:
        if is_crocodile_run[message.guild.id] == 0:
            # Проверяется создан ли тред для игры в крокодила, при необходимости создается:
            if crocodile_game_tread[message.guild.id] == 0:
                tread = await message.channel.create_thread(name="Играем в крокодила", message=message)
                start_tread_message[message.guild.id] = message
                # Для того чтобы не было частых повторов слов, вместо простого рандомного выбора
                # сначала в случайном порядке перебираются все слова из базы, загаданные слова
                # перемещаютя в другой файл, когда слова в основном файле кончаются все сбрасывается
                with open("crocodile.txt", encoding="utf-8") as f:
                    content = f.readlines()
                content = [x.strip() for x in content]
                word_index = random.randint(0, len(content)-1)
                crocodile_word[message.guild.id] = content[word_index]
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
                is_crocodile_run[message.guild.id] = 1
                crocodile_game_tread[message.guild.id] = tread
                await tread.send(f"**Правила:**\r\n"
                                 f"{message.author.mention} получил в ЛС загаданное слово и стал ведущим игры.\r\n"
                                 f"Ведущий должен объяснить загаданное слово, а остальные игроки его отгадать.\r\n"
                                 f"При объяснении слов запрещено использовать однокоренные слова.\r\n"
                                 f"Отгадавший слово станет новым ведущим и получит от бота сообщение с новым словом.\r\n"
                                 f"За отгаданные слова начисляются очки, в конце будет подведён итог.")
                await message.author.send(f"Загадано слово:\r\n"
                                          f"```css\r\n{crocodile_word[message.guild.id]}\r\n```")
                await start_crocodile(message.guild.id)
            else:
                with open("crocodile.txt", encoding="utf-8") as f:
                    content = f.readlines()
                content = [x.strip() for x in content]
                word_index = random.randint(0, len(content) - 1)
                crocodile_word[message.guild.id] = content[word_index]
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
                is_crocodile_run[message.guild.id] = 1
                await crocodile_game_tread[message.guild.id].send(f"{message.author.mention} объясняет слово, остальные должны угадать")
                await message.author.send(f"Загадано слово:\r\n"
                                          f"```css\r\n{crocodile_word[message.guild.id]}\r\n```")
                await start_crocodile(message.guild.id)
        else:
            pass

    if message.content == prefix + "help":
        pass

    # Отслеживает хост AmongUs. Основная цель: знать когда хостер в лобби (чтобы зайти в игру)
    # и сколько времени осталось до закрытия лобби.
    if message.content == prefix + "хост" or message.content == prefix + "host":
        lst = message.content.split()
        # если ввести команду без параметров, то отслеживаешь своё лобби
        if len(lst) == 1:
            hoster[message.guild.id] = message.author

        # можно отслеживать чужое лобби
        if len(lst) == 2:
            user_id = lst[1]
            user_id = user_id[2:]
            if len(lst[1]) > 3:
                if user_id[0] == "!":
                    user_id = user_id[1:]
                user_id = user_id[:-1]
                if user_id[0] == "&":
                    user_id = user_id[1:]
            # без такго перебора не получается получить доступ к member
            for guild in bot.guilds:
                if guild.id == message.guild.id:
                    for member in guild.members:
                        if int(member.id) == int(user_id):
                            hoster[message.guild.id] = member
        # Проверяется запущено ли уже отслеживание хоста
        if is_host_progress[message.guild.id] == 1:
            await message.channel.send(f"Команда уже запущена. Бот не умеет следить одновременно за несколькими хостами.")
        # Проверяется статус игровой активности игрока в ДС
        elif hoster[message.guild.id].activity is None:
            await message.channel.send(f"Для работы команды нужно зайти в Among Us с ПК и включить в дискорде отображение статуса игровой активности")
        elif hoster[message.guild.id].activities[-1].name != "Among Us":
            await message.channel.send(f"Для работы команды нужно зайти в Among Us с ПК и включить в дискорде отображение статуса игровой активности")
        else:
            # Если все норально, запускается отслеживание
            is_host_progress[message.guild.id] = 1
            now_game_status[message.guild.id] = hoster[message.guild.id].activities[-1].details
            last_game_status[message.guild.id] = now_game_status[message.guild.id]
            if now_game_status[message.guild.id] == "Playing":
                game_des = f"{hoster[message.guild.id].display_name} находится в запущенной игре\r\nЖду когда он станет хостом"
            elif now_game_status[message.guild.id] == "Hosting a game":
                game_des = f"{hoster[message.guild.id].display_name} хостит игру\r\n" \
                           f"Недостаточно информации для ослеживания времени жизни лобби"
            else:
                game_des = f"{hoster[message.guild.id].display_name} находится в главном меню или чужом лобби\r\nЖду когда он станет хостом"
            embed = discord.Embed(description=game_des, color=0xda00e7)
            embed.set_author(name=f"ඞ      Лобби {hoster[message.guild.id].display_name}      ඞ")
            host_message[message.guild.id] = await message.channel.send(embed=embed)
            start_host_message[message.guild.id] = message
            await game_iterator(hoster[message.guild.id], message.guild.id)


bot.run(TOKEN)
