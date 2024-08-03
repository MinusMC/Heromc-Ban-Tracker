import requests
from bs4 import BeautifulSoup
import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio
import logging
from logging.config import dictConfig
import os
import json

clear = lambda: os.system('cls')
clear()

class CustomFormatter(logging.Formatter):
    """A Custom Formatter Class For Logging"""

    GREY = "\x1b[38;5;240m"
    YELLOW = "\x1b[0;33m"
    CYAN = "\x1b[1;94m"
    RED = "\x1b[1;31m"
    BRIGHT_RED = "\x1b[1;41m"
    RESET = "\x1b[0m"
    FORMAT = "[\x1b[0m%(asctime)s\x1b[0m] - [{}%(levelname)s{}] - %(message)s"

    FORMATS = {
        logging.DEBUG: FORMAT.format(GREY, RESET) + "(%(filename)s:%(lineno)d)",
        logging.INFO: FORMAT.format(CYAN, RESET),
        logging.WARNING: FORMAT.format(YELLOW, RESET),
        logging.ERROR: FORMAT.format(RED, RESET) + "(%(filename)s:%(lineno)d)",
        logging.CRITICAL: FORMAT.format(BRIGHT_RED, RESET) + "(%(filename)s:%(lineno)d)",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, "%d %b %Y %H:%M:%S")
        return formatter.format(record)

dictConfig({
    "version": 1,
    "disable_existing_loggers": True,
})
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)

# Constants
URL = "https://id.heromc.net/vi-pham/bans.php"
HEROMC_URL = "https://id.heromc.net/vi-pham/info.php?type=ban&id={}"
CONFIG_FILE = 'config.json'

def get_config():
    """Load configuration from config.json or create it if it doesn't exist."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        print("Configuration file not found. Creating a new one.")
        bot_token = input("Enter your bot token: ")
        channel_id = int(input("Enter your channel ID: "))
        guild_id = int(input("Enter your guild ID: "))
        refresh_time = int(input("Enter refresh time (in seconds): "))
        config = {
            "BOT_TOKEN": bot_token,
            "CHANNEL_ID": channel_id,
            "GUILD_ID": guild_id,
            "REFRESH_TIME": refresh_time
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return config

config = get_config()
BOT_TOKEN = config["BOT_TOKEN"]
CHANNEL_ID = config["CHANNEL_ID"]
GUILD_ID = config["GUILD_ID"]
REFRESH_TIME = config["REFRESH_TIME"]

def get_id(url):
    """Get the ID from the URL"""
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    links = soup.find_all('a', href=True)
    for link in links:
        if "info.php?type=ban&id=" in link['href']:
            id = link['href'].split('=')[-1]
            return int(id)
    return None

class BanChecker(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='None', intents=discord.Intents.all())
        self.channel = None
        self.guild = None
        self.id = get_id(URL)
        self.first_ban = True  # Flag to track if it's the first ban

    async def on_ready(self):
        logging.info(f'Logged as {self.user.name}')
        self.channel = self.get_channel(CHANNEL_ID)
        self.guild = self.get_guild(GUILD_ID)
        await self.channel.purge(limit=None)
        embed = discord.Embed(
            title="", 
            description="", 
            color=0x00ff00
        )
        embed.add_field(name='Status:', value='Started')
        starttime = int(datetime.now().timestamp())
        embed.add_field(name='Start time:', value=f'<t:{starttime}:R>')
        embed.add_field(name='Refresh every:', value=f'{REFRESH_TIME}s', inline=False)
        embed.set_thumbnail(url=self.guild.icon.url)
        await self.channel.send(embed=embed)
        await self.check_bans()

    async def check_bans(self):
        while True:
            try:
                response = requests.get(HEROMC_URL.format(self.id))
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    td_tags = soup.find_all('td')
                    user = None
                    staff = None
                    reason = None

                    for td in td_tags:
                        if td.text == 'Người chơi':
                            user = td.find_next_sibling('td').text.strip()
                        if td.text == 'Bị phạt bởi':
                            staff = td.find_next_sibling('td').text.strip()
                        if td.text == 'Lý do':
                            reason = td.find_next_sibling('td').text.strip()

                    if "Lỗi: ban không tìm thấy trong cơ sở dữ liệu." in soup.get_text():
                        pass
                    else:
                        if self.first_ban:  # Ignore the first ban
                            self.first_ban = False
                        else:
                            ban_timestamp = int(datetime.now().timestamp())
                            unban_timestamp = int((datetime.now() + timedelta(days=2)).timestamp())
                            embed = discord.Embed(
                                title=":robot: AntiCheat Ban Notification",
                                color=0xff0000 if "Console" in staff else 0x00ff00
                            )
                            embed.add_field(name='User:', value=user, inline=False)
                            embed.add_field(name='Reason:', value=reason, inline=False)
                            embed.add_field(name='Banned By:', value='Console' if "Console" in staff else staff, inline=False)
                            embed.add_field(name='Ban ID:', value=f'Ban #{self.id}', inline=False)
                            embed.add_field(name='Banned:', value=f'<t:{ban_timestamp}:R>', inline=False)
                            embed.add_field(name='Will get unban:', value=f'<t:{unban_timestamp}:R>', inline=False)
                            embed.add_field(name='Full info:', value=f'[Click Here](https://id.heromc.net/vi-pham/info.php?type=ban&id={self.id})', inline=False)
                            embed.set_thumbnail(url=self.guild.icon.url)
                            await self.channel.send(embed=embed)
                        self.id += 1
                else:
                    logging.error(f'Heromc: Error: {response.status_code}')
            except Exception as e:
                logging.error(e)
            await asyncio.sleep(REFRESH_TIME)

bot = BanChecker()
logging.info('Starting...')
bot.run(BOT_TOKEN)
