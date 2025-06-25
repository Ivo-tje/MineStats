#!/bin/python
import discord
from discord.ext import commands, tasks
import json
import asyncio
import aiohttp
import logging
import re
import datetime
from mcstatus import JavaServer
from zabbix_utils import AsyncZabbixAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(name)s:%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Suppress discord library debug logging
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.INFO)

# Load configuration
with open('config.json') as config_file:
    config = json.load(config_file)

TOKEN = config['discord_token']
SERVER_ADDRESS = config['minecraft_server']
MC_CHANNEL_ID = int(config['minecraft_channel_id'])
ZBX_TOKEN = config['api_token']
ZBX_URL = config['zabbix_host']

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

def load_json_file(filename, default):
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return default

def save_json_file(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file)

previous_players = set(load_json_file('players.json', []))
latest_versions = load_json_file('versions.json', {"latest_release": "", "latest_snapshot": ""})

async def get_latest_minecraft_version():
    url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            latest_release = data["latest"]["release"]
            latest_snapshot = data["latest"]["snapshot"]
            return latest_release, latest_snapshot

async def lookup_mc_player(playername):
    url = f"https://api.mojang.com/users/profiles/minecraft/{playername}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            output = await response.json()
            return output

@bot.tree.command(name="stats", description="Show the players and their time in the game")
async def stats(interaction: discord.Interaction):
    api = AsyncZabbixAPI(ZBX_URL, validate_certs=False)
    api.session.verify = False
    await api.login(token=ZBX_TOKEN)
    tags = [{"tag": "game", "value": "minecraft"}, {"tag": "Item", "value": "play_time"}]
    output = ["itemid", "name"]

    items = await api.item.get(tags=tags, output=output)
    item_dict = {item['itemid']: item['name'] for item in items}

    all_history = []

    for itemid, name in item_dict.items():
        history = await api.history.get(itemids=[itemid], history=3, limit=1, sortfield="clock", sortorder="DESC")

        for entry in history:
            entry['value'] = int(entry['value']) / 1200
            entry['name'] = name

        all_history.extend(history)

    # Sort history valus
    sorted_history = sorted(all_history, key=lambda x: x['value'], reverse=True)
    message = ""
    for item in sorted_history:
        name = re.search(r'Minecraft Stats - (.*?) - custom', item['name'])
        if name:
            message += f"{name.group(1)} - %02dh %02dm\n" % (divmod(item['value'], 60))
    await interaction.response.send_message(message)
    await api.logout()

@bot.tree.command(name="version", description="Show latest minecraft versions")
async def version(interaction: discord.Interaction):
    latest_release, latest_snapshot = await get_latest_minecraft_version()
    latest_versions.update({
        "latest_release": latest_release,
        "latest_snapshot": latest_snapshot
    })
    save_json_file('versions.json', latest_versions)
    await interaction.response.send_message(f'The latest version is {latest_release}. The latest snapshot is {latest_snapshot}')

@bot.tree.command(name="player", description="Check is a minecraft user exists")
async def playerlookup(interaction: discord.Interaction, player: str):
    playerdata = await lookup_mc_player(player)
    if playerdata:
        logging.info(f'{playerdata}')
        if 'name' in playerdata:
            await interaction.response.send_message(f"{playerdata['name']} bestaat en heeft id: {playerdata['id']}")
        else:
            await interaction.response.send_message(f"{player} bestaat niet.")


@bot.tree.command(name="myip", description="How to find your IP address")
async def myip(interaction: discord.Interaction):
    await interaction.response.send_message(f"Visit http://ipv4.icanhazip.com")

@tasks.loop(hours=1)
async def check_for_updates(channel):
    latest_release, latest_snapshot = await get_latest_minecraft_version()
    logging.info(f'Running versioncheck, got: {latest_versions["latest_release"]} - {latest_versions["latest_snapshot"]}')
    if latest_release != latest_versions["latest_release"] or latest_snapshot != latest_versions["latest_snapshot"]:
        latest_versions.update({
            "latest_release": latest_release,
            "latest_snapshot": latest_snapshot
        })
        await channel.send(f'New Minecraft version available! Latest release: {latest_release}, Latest snapshot: {latest_snapshot}')
        save_json_file('versions.json', latest_versions)

@tasks.loop(seconds=10)
async def monitor_server(channel):
    global previous_players
    server = JavaServer.lookup(SERVER_ADDRESS)
    try:
        status = server.status()
        current_players = set(player.name for player in status.players.sample) if status.players.sample else set()
        joined_players = current_players - previous_players
        left_players = previous_players - current_players
        post = False

        message = ""

        for player in joined_players:
            message += f"🎮 **Player joined:** {player}\n"
            post = True

        for player in left_players:
            message += f"🚪 **Player left:** {player}\n"
            post = True

        if len(current_players) == 1:
            message += f"There is now {len(current_players)} player online.\n"
        else:
            message += f"There are now {len(current_players)} players online.\n"

        if post:
            await channel.send(message)
            logging.info(message)

        previous_players = current_players
        save_json_file('players.json', list(previous_players))

    except Exception as e:
        logging.error(f"Error monitoring server: {e}")

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()  # Force sync of commands
        logging.info(f"Synced {len(synced)} command(s).")
    except Exception as e:
        logging.info(f"Sync failed: {e}")
    logging.info(f'Logged in as {bot.user}')
    mc_channel = bot.get_channel(MC_CHANNEL_ID)
    if mc_channel:
        logging.info(f'starting minecraft update checker')
        check_for_updates.start(mc_channel)
        logging.info(f'starting minecraft player checker')
        monitor_server.start(mc_channel)
    else:
        logging.info(f"Couldn't start minecraft update checker")

bot.run(TOKEN)
