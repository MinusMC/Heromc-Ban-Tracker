import requests
from bs4 import BeautifulSoup
import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio
import logging
from logging.config import dictConfig
import json
import os

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

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

BOT_TOKEN = config['bot_token']
GUILD_ID = config['guild_id']
CHANNEL_ID = config['channel_id']
BOT_ENABLED = config['bot_enabled']
WEBHOOK_ENABLED = config['webhook_enabled']
WEBHOOK_URL = config['webhook_url']
REFRESH_TIME = config['refresh_time']

if BOT_ENABLED and WEBHOOK_ENABLED:
    logging.error('Both webhook and bot are enabled. Please enable only one.')
    exit(1)

if not BOT_ENABLED and not WEBHOOK_ENABLED:
    logging.error('Neither webhook nor bot is enabled. Please enable one.')
    exit(1)

# Constants
URL = "https://id.heromc.net/vi-pham/bans.php"
HEROMC_URL = "https://id.heromc.net/vi-pham/info.php?type=ban&id={}"

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
        logging.info(f'Logged in as {self.user.name}')
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

                    if "Lỗi: ban không tìm thấy trong cơ sở dữ liệu." not in soup.get_text():
                        if not self.first_ban:  # Ignore the first ban
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
                        self.first_ban = False
                        self.id += 1
                else:
                    logging.error(f'Heromc: Error: {response.status_code}')
            except Exception as e:
                logging.error(e)
            await asyncio.sleep(REFRESH_TIME)

async def send_webhook_notification(id):
    response = requests.get(HEROMC_URL.format(id))
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

        if "Lỗi: ban không tìm thấy trong cơ sở dữ liệu." not in soup.get_text():
            ban_timestamp = int(datetime.now().timestamp())
            unban_timestamp = int((datetime.now() + timedelta(days=2)).timestamp())
            data = {
                "embeds": [{
                    "title": ":robot: AntiCheat Ban Notification",
                    "color": 0xff0000 if "Console" in staff else 0x00ff00,
                    "fields": [
                        {"name": "User:", "value": user, "inline": False},
                        {"name": "Reason:", "value": reason, "inline": False},
                        {"name": "Banned By:", "value": "Console" if "Console" in staff else staff, "inline": False},
                        {"name": "Ban ID:", "value": f'Ban #{id}', "inline": False},
                        {"name": "Banned:", "value": f'<t:{ban_timestamp}:R>', "inline": False},
                        {"name": "Will get unban:", "value": f'<t:{unban_timestamp}:R>', "inline": False},
                        {"name": "Full info:", "value": f'[Click Here](https://id.heromc.net/vi-pham/info.php?type=ban&id={id})', "inline": False},
                    ],
                    "thumbnail": {"url": "https://id.heromc.net/static/images/logo.png"}
                }]
            }
            result = requests.post(WEBHOOK_URL, json=data)
            if result.status_code != 204:
                logging.error(f'Webhook error: {result.status_code}, {result.text}')

async def webhook_checker():
    id = get_id(URL)
    first_ban = True
    while True:
        try:
            if not first_ban:
                await send_webhook_notification(id)
            first_ban = False
            id += 1
        except Exception as e:
            logging.error(e)
        await asyncio.sleep(REFRESH_TIME)

if WEBHOOK_ENABLED:
    logging.info('Hí anh bạn, webhook đang được hoàn thiện, thử lại sau update mới')
    asyncio.run(webhook_checker())
elif BOT_ENABLED:
    bot = BanChecker()
    logging.info('Starting bot...')
    bot.run(BOT_TOKEN)
else:
    logging.error('Neither webhook nor bot is enabled. Please enable one.')
    exit(1)
