# -*- coding: utf-8 -*-
# ------------- ИМПОРТ МОДУЛЕЙ

import logging  # Импортируем модуль логирования

import aiosqlite  # Импортируем модуль работы с базами SQLite
import discord  # Импортируем основной модуль
from discord.ext import commands  # Импортируем команды из модуля discord.ext
from discord_slash import SlashCommand, SlashContext  # Импортируем модуль команд с косой чертой (slash)
from discord_slash.utils.manage_commands import create_choice, create_option

import config  # Импортируем настройки приложения

# ------------- ИМПОРТ МОДУЛЕЙ // КОНЕЦ


# ------------- СОЗДАЁМ ПРИЛОЖЕНИЕ И НАЗЫВАЕМ ЕГО CLIENT
client = commands.Bot(description="Test bot", command_prefix=commands.when_mentioned_or(config.prefix),
                      case_insensitive=True, help_command=None)

# ------------- СОЗДАЁМ ОБРАБОТКУ КОМАНДЫ С КОСОЙ ЧЕРТОЙ ЧЕРЕЗ СОЗДАННОЕ ПРИЛОЖЕНИЕ
slash = SlashCommand(client, sync_commands=True)

# ------------- СОЗДАЁМ ОБРАБОТКУ КОМАНДЫ С КОСОЙ ЧЕРТОЙ ЧЕРЕЗ СОЗДАННОЕ ПРИЛОЖЕНИЕ // КОНЕЦ


# ------------- РЕГИСТРИРУЕМ СОБЫТИЯ ПРИЛОЖЕНИЯ
logging.basicConfig(level=logging.WARNING,
                    format='%(asctime)s - %(levelname)s - %(process)d:%(thread)d: %(module)s:%(lineno)d: %(message)s')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# ------------- РЕГИСТРИРУЕМ СОБЫТИЯ ПРИЛОЖЕНИЯ // КОНЕЦ


# ------------- КОРУТИНА ДЛЯ ПЕРЕСЫЛКИ СООБЩЕНИЯ НА ВСЕ СЕРВЕРА
async def send_to_servers(*args, **kwargs):
    """
    send message to all connected servers to config.globalchannel channel, arguments as for channel.send()
    :param args:
    :param kwargs:
    :return:
    """
    for guild in client.guilds:
        if channel := discord.utils.get(guild.text_channels, name=config.globalchannel):
            try:
                await channel.send(*args, **kwargs)
            except discord.Forbidden as e:
                logger.warning(f"Failed to send message to {guild.name}: discord.Forbidden\n{e}")
            except discord.HTTPException as e:
                logger.warning(f"Failed to send message to {guild.name}: discord.HTTPException\n{e}")
            except Exception as e:
                logger.warning(f"Failed to send message to {guild.name}: {e}")


# ------------- БЫСТЫРЫЙ СКРИПТ НА ОТПРАВКУ СООБЩЕНИЙ // КОНЕЦ


def guild_ids_for_slash():
    if config.environment_type == 'prod':
        return None
    else:
        return [guild.id for guild in client.guilds]


# ------------- ВЫВОДИМ ДАННЫЕ ПРИЛОЖЕНИЯ ПРИ ПОДКЛЮЧЕНИЕ В КОНСОЛЬ
@client.event
async def on_ready():
    client.sql_conn = await aiosqlite.connect('Wormhole.sqlite')
    await client.sql_conn.execute('create table if not exists black_list (userid integer not null unique, '
                                  'add_timestamp text default current_timestamp, reason text, banner_id integer);')

    # Показывает имя приложения, указанное на discordapp.com
    logger.info(f'APP Username: {client.user} ')
    logger.info(f'Using token {config.token[0:2]}...{config.token[-3:-1]}')
    logger.info(f'Current env type: {config.environment_type}')
    logger.info(f'Using global channel {config.globalchannel}')

    # Показывает ID приложения указанное на discordapp.com
    logger.info('APP Client ID: {0.user.id} '.format(client))
    logger.info(f'Link for connection: https://discord.com/api/oauth2/authorize?client_id={client.user.id}&'
                f'permissions=0&scope=bot%20applications.commands')

    # Выводит список серверов, к которым подключено приложение
    logger.info('Servers connected to: ' + ''.join('"' + guild.name + '"; ' for guild in client.guilds))

    # Изменяем статус приложения
    await client.change_presence(status=discord.Status.online, activity=discord.Game('Elite Dangerous'))

    # Отправляем сообщение в общий канал
    emStatusOn = discord.Embed(title='⚠ • ВНИМАНИЕ!', description='Приложение запущено', colour=0x90D400)
    emStatusOn.set_image(
        url="https://media.discordapp.net/attachments/682731260719661079/682731350922493952/ED1.gif")
    await send_to_servers(embed=emStatusOn, delete_after=13)
    # Отправляем сообщение


# ------------- ВЫВОДИМ ДАННЫЕ ПРИЛОЖЕНИЯ ПРИ ПОДКЛЮЧЕНИЕ В КОНСОЛЬ // КОНЕЦ

@client.event
async def on_slash_command_error(ctx, error):
    logger.warning(
        f"An error occurred: {ctx.guild} / {ctx.author} / command: {ctx.name}; Error: {error}")
    if isinstance(error, discord.ext.commands.NotOwner):
        await ctx.send('Выполнение этой команды доступно только владельцу приложения', delete_after=13)
        return

    await ctx.send(str(error), delete_after=13)


# ------------- ОБРАБАТЫВАВАЕМ ОШБИКИ КОММАНД // КОНЕЦ


# Логирование слэш-команд
@client.event
async def on_slash_command(ctx):
    logger.info(f'Got slash command; {ctx.guild} / {ctx.author} / command: {ctx.name};'
                f' subcommand_name: {ctx.subcommand_name};'
                f' subcommand_group: {ctx.subcommand_group}; options: {ctx.data.get("options")}')


# ------------- ВЫВОДИМ СООБЩЕНИЯ ПОЛЬЗОВАТЕЛЕЙ В КОНСОЛЬ ПРИЛОЖЕНИЯ И ПЕРЕНАПРАВЛЯЕМ НА ДРУГИЕ СЕРВЕРА
@client.event
async def on_message(message):
    # Игнорируем сообщения, отправленные этим приложением
    if message.author.id == client.user.id:
        return

    # Логирует сообщения в консоль приложения
    logger.info('Message: {0.guild} / #{0.channel} / {0.author}: {0.content}'.format(message))

    # Игнорируем сообщения в ЛС
    if isinstance(message.channel, discord.DMChannel):
        return

    # Игнорируем сообщения, отправленные не в забриджованный канал
    if message.channel.name != config.globalchannel:
        return

    # Игнорируем сообщения, начинающиеся с префикса команд
    if message.content.startswith(config.prefix) or client.user.mentioned_in(message):
        return

    # Игнорируем сообщения, отправленные другими приложениями
    if message.author.bot:
        return

    # Игнорируем сообщения с упоминанием
    if message.mentions or message.mention_everyone:
        await message.delete()
        await message.channel.send(
            'Сообщения, с упоминанием всех активных и неактивных пользователей, не пропускаются в '
            'общий чат', delete_after=13)
        return

    # Игнорируем сообщения с символом @
    if "@" in message.content:
        await message.delete()
        await message.channel.send('` ⚠ • ВНИМАНИЕ! ` Упс! Что-то пошло не так'.format(message), delete_after=13)
        return

    # Игнорируем сообщения, отправленные пользователем из чёрного списка
    if (await (await client.sql_conn.execute(
            'select count(*) from black_list where userid = ?;', [message.author.id])).fetchone())[0] == 1:
        await message.delete()
        await message.channel.send(
            'Сообщение пользователей из чёрного списка не допускаются к пересылке\n Вам по прежнему доступно '
            'использование команд приложения',
            delete_after=13)
        return

    # Создаём сообщение
    emGlobalMessage = discord.Embed(description=f" **{message.author.name}**: {message.content}", colour=0x2F3136)
    emGlobalMessage.set_footer(icon_url=message.guild.icon_url,
                               text=f"Сервер: {message.guild.name} // ID пользователя: {message.author.id}")

    for attachment in message.attachments:
        if attachment.filename.endswith(('bmp', 'jpeg', 'jpg', 'png', 'gif')):
            emGlobalMessage.set_image(url=attachment.url)
        else:
            await message.delete()
            await message.channel.send('К пересылке допускаются только файлы с расширениями bmp, jpeg, jpg, png, gif',
                                       delete_after=13)
            return

    # Удаляем сообщение, отправленное пользователем
    await message.delete()

    # Отправляем сообщение
    await send_to_servers(embed=emGlobalMessage)


# ------------- ВЫВОДИМ СООБЩЕНИЯ ПОЛЬЗОВАТЕЛЕЙ В КОНСОЛЬ ПРИЛОЖЕНИЯ И ПЕРЕНАПРАВЛЯЕМ НА ДРУГИЕ СЕРВЕРА // КОНЕЦ


# ------------- КОМАНДА ПРОВЕРКА ПРИЛОЖЕНИЯ
@slash.slash(name="ping",
             description="Проверить состояние приложения",
             guild_ids=guild_ids_for_slash())
async def ping(ctx):
    # Создаём информационное сообщение
    emPing = discord.Embed(
        title='⚠ • ВНИМАНИЕ!',
        description=f'Latency {round(client.latency * 100, 1)} ms',
        colour=0x90D400)
    # Отправляем информационное сообщение и удаляем его через 13 секунд
    await ctx.send(embed=emPing, delete_after=13)


# ------------- КОМАНДА ПРОВЕРКА ПРИЛОЖЕНИЯ // КОНЕЦ


# ------------- КОМАНДА ПОМОЩИ
@slash.slash(name="help",
             description="Показать информацию о командах используемых приложением",
             guild_ids=guild_ids_for_slash())
async def help_(ctx):
    # Создаём информационное сообщение
    emHelp = discord.Embed(
        title='ПОМОЩЬ',
        description='```Некоторые из ниже указанных команд могут не работать или для их '
                    'использования могут требоваться определённые разрешения.```',
        colour=0x2F3136)
    emHelp.add_field(name='Список команд',
                     value='`ping` - Проверить состояние приложения.\n`help` - Показать информацию о командах '
                           'используемых приложением.\n`information` - Показать информацию о приложение.\n`clear` - '
                           'Удалить сто последних сообщений на канале.\n`bluadd` - Записать пользователя в чёрный '
                           'список.\n`bluremove` - Стереть пользователя из чёрного списка.\n`serverslist` - Показать '
                           'список серверов, к которым подключено приложение.\n`serversleave` - Отключить приложение '
                           'от указанного сервера.\n`setup` - Создать канала для приёма и передачи сообщений.')
    emHelp.add_field(name='Дополнительная информация',
                     value='Дополнительную информацию о приложение можно запросить командой `information`',
                     inline=False)
    # Отправляем информационное сообщение и удаляем его через 13 секунд
    await ctx.send(embed=emHelp, delete_after=60)


# ------------- КОММАНДА ПОМОЩИ // КОНЕЦ


# ------------- КОМАНДА ОТОБРАЖЕНИЯ ИНФОРМАЦИИ О ПРИЛОЖЕНИИ
@slash.slash(name="information",
             description="Показать информацию о приложение",
             guild_ids=guild_ids_for_slash())
async def information(ctx):
    # Создаём сообщение
    emInformation = discord.Embed(title='ИНФОРМАЦИЯ',
                                  description='Приложение создано для обмена текстовыми и файловыми сообщениями между '
                                              'серверами по игре [Elite Dangerous](https://www.elitedangerous.com/). '
                                              'В первую очередь приложение направлено помочь эскадронам с закрытыми '
                                              'серверами, обмениваться сообщениями с другими серверами и для тех '
                                              'серверов и пользователи которых предпочитают находится только на своём '
                                              'сервере по [Elite Dangerous](https://www.elitedangerous.com/). Для '
                                              'остальных же данное приложение может быть не так востребовано, '
                                              'но так как приложение не привязано к какому либо серверу, '
                                              'его можно использовать для серверов другой тематики.\n\nЕсли вы '
                                              'владеете одним из серверов по [Elite Dangerous]('
                                              'https://www.elitedangerous.com/) или связанной тематике и хотите '
                                              'подключить приложение к себе на сервер, воспользуйтесь данной ['
                                              'ссылкой]('
                                              'https://discordapp.com/oauth2/authorize?&client_id=826410895634333718'
                                              '&scope=bot&permissions=0), либо можете на основе исходного кода '
                                              'данного приложения сделать свою сеть обмена сообщениями например по '
                                              'торговле или другой игре.',
                                  colour=0x2F3136)
    emInformation.add_field(name='Разработчики ', value='• <@420130693696323585>\n• <@665018860587450388>')
    emInformation.add_field(name='Благодарности', value='• <@478527700710195203>')
    # emInformation.add_field(name='Список серверов', value="".join(guild.name + '\n' for guild in client.guilds))
    emInformation.set_footer(text=client.user.name)
    # Отправляем сообщение и удаляем его через 60 секунд
    await ctx.send(embed=emInformation, delete_after=60)


# ------------- КОМАНДА ОТОБРАЖЕНИЯ ИФОРМАЦИИ О ПРИЛОЖЕНИЕ // КОНЕЦ


# ------------- КОМАНДА ЗАПИСИ ПОЛЬЗОВАТЕЛЯ В ЧЁРНЫЙ СПИСОК
@commands.is_owner()
@slash.subcommand(
    base='blacklist',
    name='add',
    guild_ids=guild_ids_for_slash(),
    base_desc='Действия с чёрным списком',
    description='Внести пользователя в чёрный список приложения',
    options=[
        create_option(
            name='userid',
            description='userid to ban',
            option_type=6,
            required=True),
        create_option(
            name='reason',
            description='reason to ban',
            option_type=3,
            required=False
        )])
async def blacklist_add(ctx, userid, reason=None):
    is_userid_banned = bool((await (await client.sql_conn.execute('select count(*) from black_list where userid = ?;',
                                                                  [userid])).fetchone())[0])
    if is_userid_banned:
        await ctx.send('Этот пользователь уже есть в чёрном списке приложения', delete_after=13)
        return

    await client.sql_conn.execute('insert into black_list (userid, reason, banner_id)'
                                  ' values (?, ?, ?);', [userid, reason, ctx.author.id])
    await client.sql_conn.commit()

    # Создаём информационное сообщение
    emBlackListAdd = discord.Embed(
        title='⚠ • ВНИМАНИЕ!',
        description=f'Пользователь с ID {userid} занесён в чёрный список приложения',
        color=0xd40000)
    await ctx.send(embed=emBlackListAdd, delete_after=13)


# ------------- КОМАНДА ЗАПИСИ ПОЛЬЗОВАТЕЛЯ В ЧЁРНЫЙ СПИСОК // КОНЕЦ


# Показ содержимого чёрного списка
# TODO: Нормальное форматирование таблицы
@slash.subcommand(
    base='blacklist',
    name='show',
    guild_ids=guild_ids_for_slash(),
    base_desc='Действия с чёрным списком',
    description='Показать чёрный список'
)
async def blacklist_show(ctx):
    full_list = await client.sql_conn.execute('select userid, add_timestamp, reason, banner_id from black_list')
    table = ['userid    add_timestamp   reason  banner_id']
    for user in (await full_list.fetchall()):
        table.append('   '.join([str(item).center(5, ' ') for item in user]))
    table = "```" + '\n'.join(table) + "```"
    await ctx.send(table, delete_after=13)


# Удаление пользователя из чёрного списка
@commands.is_owner()
@slash.subcommand(
    base='blacklist',
    name='remove',
    guild_ids=guild_ids_for_slash(),
    base_desc='Действия с чёрным списком',
    description='Удалить пользователя из чёрного списка приложения',
    options=[
        create_option(
            name='userid',
            description='userid to unban',
            option_type=6,
            required=True)
    ])
async def blacklist_remove(ctx, userid):
    is_userid_banned = bool((await (await client.sql_conn.execute('select count(*) from black_list where userid = ?;',
                                                                  [userid])).fetchone())[0])
    if not is_userid_banned:
        await ctx.send('Этот пользователь не находится чёрном списке приложения', delete_after=13)
        return

    await client.sql_conn.execute('delete from black_list where userid = ?', [userid])
    await client.sql_conn.commit()
    await ctx.send('Пользователь успешно удалён из чёрного списка', delete_after=13)


# ------------- КОМАНДА ВЫВОДА СПИСКА СЕРВЕРОВ
@slash.slash(name="server_leave",
             description="Покинуть сервер",
             guild_ids=guild_ids_for_slash())
# Команду может выполнить только владелец приложения
@commands.is_owner()
async def server_leave(ctx, id_to_leave: int):
    if guild_to_leave := client.get_guild(id_to_leave) is None:
        await ctx.send('Сервер с указанным ID не найден', delete_after=13)
        return
    await guild_to_leave.leave()
    await ctx.send('Сервер с указанным ID успешно покинут', delete_after=13)


# ------------- КОМАНДА ВЫВОДА СПИСКА СЕРВЕРОВ // КОНЕЦ


# Команду может выполнить только владелец приложения
# @commands.is_owner()
@slash.slash(name="servers_list",
             description="Вывести список серверов, где присутствует бот",
             guild_ids=guild_ids_for_slash())
async def servers_list(ctx):
    # Создаём сообщение
    emServers = discord.Embed(title='СПИСОК СЕРВЕРОВ',
                              description='Список серверов, к которым подключено приложение',
                              colour=0x2F3136)
    emServers.add_field(
        name='Список серверов',
        value="".join(guild.name + f' (ID:{guild.id})\n' for guild in client.guilds))
    emServers.set_footer(text=' ' + client.user.name + ' ')
    # Отправляем сообщение и удаляем его через 60 секунд
    await ctx.send(embed=emServers, delete_after=60)


# ------------- КОМАНДА ОТКЛЮЧЕНИЯ ПРИЛОЖЕНИЯ ОТ СЕРВЕРА

# ------------- КОМАНДА ОТКЛЮЧЕНИЯ ПРИЛОЖЕНИЯ ОТ СЕРВЕРА // КОНЕЦ


# ------------- КОМАНДА СОЗДАНИЯ КАНАЛА ДЛЯ ПРИЁМА И ОТПРАВКИ СООБЩЕНИЙ
@slash.slash(name="setup",
             description="Создать канала для приёма и передачи сообщений",
             guild_ids=guild_ids_for_slash())
# Команду может выполнить только пользователь, с ролью администратор
async def setup(ctx):
    if isinstance(ctx.author, discord.User):  # проверка, не в лс ли идёт команда
        await ctx.send('Использование этой команды допускается только на серверах, не в личных сообщениях',
                       delete_after=13)
        return

    if ctx.author.guild_permissions.administrator:  # проверка наличия админских прав на сервере у выполняющего
        guild = ctx.guild
        if discord.utils.get(guild.text_channels,
                             name=config.globalchannel) is None:  # проверка на наличие нужного канала # noqa:E501
            await guild.create_text_channel(name=config.globalchannel)
            await ctx.send(
                f'Канал {config.globalchannel} успешно создан и будет использоваться для пересылки сообщений',
                delete_after=13)
        else:
            await ctx.send(f'У вас уже есть подходящий канал: {config.globalchannel}', delete_after=13)
    else:
        await ctx.send('Для выполнения этой команды вам необходимо обладать правами администратора на этом сервере',
                       delete_after=13)


# ------------- КОМАНДА СОЗДАНИЯ КАНАЛА ДЛЯ ПРИЁМА И ОТПРАВКИ СООБЩЕНИЙ // КОНЕЦ


# Генерируемый токен при создание приложения на discordapp.com, необходимый для подключения к серверу. //
# Прописывается в config.py
client.run(config.token)

# ------------- СОЗДАЁМ ПРИЛОЖЕНИЕ И НАЗЫВАЕМ ЕГО CLIENT  // КОНЕЦ
