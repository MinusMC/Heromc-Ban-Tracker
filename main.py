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
import sqlite3

# Clear console and set console title
def setup_console():
    clear = lambda: os.system('cls' if os.name == 'nt' else 'clear')
    clear()
    if os.name == 'nt':  # Windows
        os.system('title HeromcBan Tracker by Idle và NgocDiep 2006')
    else:  # Unix-like (Linux/macOS)
        print("\033]0;HeromcBan Tracker\007")

setup_console()

# Custom logging formatter
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

# Configure logging
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
DB_FILE = 'ban_log.db'

# Load configuration
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
        prefix = input("Enter the command prefix: ")
        config = {
            "BOT_TOKEN": bot_token,
            "CHANNEL_ID": channel_id,
            "GUILD_ID": guild_id,
            "REFRESH_TIME": refresh_time,
            "PREFIX": prefix
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return config

config = get_config()
BOT_TOKEN = config["BOT_TOKEN"]
CHANNEL_ID = config["CHANNEL_ID"]
GUILD_ID = config["GUILD_ID"]
REFRESH_TIME = config["REFRESH_TIME"]
PREFIX = config["PREFIX"]

# Get the ID from the URL
def get_id(url):
    """Get the ID from the URL"""
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all('a', href=True)
        for link in links:
            if "info.php?type=ban&id=" in link['href']:
                return int(link['href'].split('=')[-1])
    else:
        logger.error(f'Failed to get ID from URL: {response.status_code}')
    return None

# Embed builder for ban notifications
def create_ban_embed(user, staff, reason, ban_id, guild_icon_url):
    ban_timestamp = int(datetime.now().timestamp())
    unban_timestamp = int((datetime.now() + timedelta(days=2)).timestamp())
    embed = discord.Embed(
        title=":robot: AntiCheat Ban Notification",
        color=0xff0000 if "Console" in staff else 0x00ff00
    )
    embed.add_field(name='User:', value=user, inline=False)
    embed.add_field(name='Reason:', value=reason, inline=False)
    embed.add_field(name='Banned By:', value='Console' if "Console" in staff else staff, inline=False)
    embed.add_field(name='Ban ID:', value=f'Ban #{ban_id}', inline=False)
    embed.add_field(name='Banned:', value=f'<t:{ban_timestamp}:R>', inline=False)
    embed.add_field(name='Will get unban:', value=f'<t:{unban_timestamp}:R>', inline=False)
    embed.add_field(name='Full info:', value=f'[Click Here](https://id.heromc.net/vi-pham/info.php?type=ban&id={ban_id})', inline=False)
    embed.set_thumbnail(url=guild_icon_url)
    return embed

# Initialize the database
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT,
                staff TEXT,
                reason TEXT,
                timestamp TEXT
            )
        ''')
        conn.commit()

# Discord bot class
class BanChecker(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=PREFIX, intents=discord.Intents.all(), help_command=None)
        self.channel = None
        self.guild = None
        self.id = get_id(URL)
        self.first_ban = True  # Flag to track if it's the first ban

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        self.channel = self.get_channel(CHANNEL_ID)
        self.guild = self.get_guild(GUILD_ID)
        await self.channel.purge(limit=None)
        
        # Send start message
        embed = discord.Embed(
            title="Heromc Ban Tracker",
            description="Monitoring for new bans...",
            color=0x00ff00
        )
        starttime = int(datetime.now().timestamp())
        embed.add_field(name='Start time:', value=f'<t:{starttime}:R>')
        embed.add_field(name='Refresh every:', value=f'{REFRESH_TIME}s', inline=False)
        embed.set_thumbnail(url=self.guild.icon.url)
        await self.channel.send(embed=embed)
        
        # Start checking bans
        await self.check_bans()

    async def check_bans(self):
        while True:
            try:
                response = requests.get(HEROMC_URL.format(self.id))
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    td_tags = soup.find_all('td')
                    user, staff, reason = None, None, None

                    for td in td_tags:
                        if td.text == 'Người chơi':
                            user = td.find_next_sibling('td').text.strip()
                        if td.text == 'Bị phạt bởi':
                            staff = td.find_next_sibling('td').text.strip()
                        if td.text == 'Lý do':
                            reason = td.find_next_sibling('td').text.strip()

                    if "Lỗi: ban không tìm thấy trong cơ sở dữ liệu." not in soup.get_text():
                        if not self.first_ban:  # Ignore the first ban
                            embed = create_ban_embed(user, staff, reason, self.id, self.guild.icon.url)
                            await self.channel.send(embed=embed)
                            # Save ban to database
                            with sqlite3.connect(DB_FILE) as conn:
                                cursor = conn.cursor()
                                cursor.execute('''
                                    INSERT INTO bans (user, staff, reason, timestamp)
                                    VALUES (?, ?, ?, ?)
                                ''', (user, staff, reason, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                                conn.commit()
                        else:
                            self.first_ban = False
                        self.id += 1
                else:
                    logger.error(f'Heromc: Error: {response.status_code}')
            except Exception as e:
                logger.error(f'An error occurred: {e}')
            await asyncio.sleep(REFRESH_TIME)

# Command for showing the ban log
@commands.command(name='banlog', help='Shows the ban log')
async def banlog(ctx, user: str = None):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        if user:
            cursor.execute('SELECT * FROM bans WHERE user = ?', (user,))
        else:
            cursor.execute('SELECT * FROM bans ORDER BY id DESC LIMIT 10')
        rows = cursor.fetchall()

    if rows:
        embed = discord.Embed(
            title=f"Ban Log{' for ' + user if user else ''}",
            color=0x00ff00
        )
        for row in rows:
            embed.add_field(name=f"Ban ID: {row[0]}",
                            value=f"User: {row[1]}\nBanned By: {row[2]}\nReason: {row[3]}\nTime: {row[4]}", inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"No bans found{' for ' + user if user else ''}.")

# Command for clearing the ban log
@commands.command(name='clearlog', help='Clears the ban log')
@commands.has_permissions(administrator=True)
async def clearlog(ctx):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM bans')
        conn.commit()
    await ctx.send("Ban log cleared.")

# Custom help command
@commands.command(name='help', help='Displays this help message')
async def custom_help(ctx):
    help_text = f"""
    **HeromcBan Tracker Commands:**
    - **{PREFIX}banlog [user]**: Shows the ban log.
    - **{PREFIX}clearlog**: Clears the ban log (Admin only).
    - **{PREFIX}help**: Displays this help message.
    """
    await ctx.send(help_text)

init_db()

bot = BanChecker()
bot.add_command(banlog)
bot.add_command(clearlog)
bot.add_command(custom_help)

logger.info('Starting...')
bot.run(BOT_TOKEN)
