import aiohttp
import discord
from discord.ext import commands
import datetime
import logging
import colorama
from colorama import Fore, Style
import psycopg2
import uuid

DKEY = "akhgwbAIHGja89guh0723gy76823h498ghw480ughnjs4gh780s4hg7h83h427h2349h4j3968hh94n9bnus9un9ghb8sg08s"

db = psycopg2.connect(
    user='zrxw',
    password='zrxw',
    port='5432',
    host='localhost',
    database='loader_api'
)

def encode(script: str, key: str) -> str:
    encoded = []
    key_length = len(key)
    for i, char in enumerate(script):
        key_char = key[i % key_length]
        encoded_char = chr((ord(char) ^ ord(key_char)) + i % 256)
        encoded.append(encoded_char)
    return ''.join(encoded)

def decode(encoded: str, key: str) -> str:
    decoded = []
    key_length = len(key)
    for i, char in enumerate(encoded):
        key_char = key[i % key_length]
        decoded_char = chr((ord(char) - i % 256) ^ ord(key_char))
        decoded.append(decoded_char)
    return ''.join(decoded)


colorama.init(autoreset=True)

class CustomFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.LIGHTRED_EX,
        logging.CRITICAL: Fore.MAGENTA,
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelno, Fore.WHITE)
        log_fmt = f"{log_color}%(asctime)s [%(levelname)-8s] - %(message)s{Style.RESET_ALL}"
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

class FileFormatter(logging.Formatter):
    """Custom logging formatter without color for file logging."""

    def format(self, record):
        log_fmt = f"%(asctime)s [%(levelname)-8s] - %(message)s"
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

def setup_logger(name):
    logger = logging.getLogger(name)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(CustomFormatter())

    log_filename = f"log-{datetime.datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(FileFormatter())

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)
    return logger


logger = setup_logger(__name__)

class BoT(commands.Bot):
    async def setup_hook(self):
        logger.info('Setup_hook called!')

bot = BoT(intents=discord.Intents.all(), command_prefix='!')

@bot.command()
@commands.is_owner()
async def create_account(ctx, username: str, password: str, hwid: str, subscription: str, days: int):
    until = datetime.datetime.now() + datetime.timedelta(days=days)
    try:
        with db.cursor() as cur:
            cur.execute('''
                INSERT INTO accounts (username, password, hwid, subscription, until, banned) 
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
            ''', (username, password, hwid, subscription, until, False))
            db.commit()
        await ctx.send('Account created successfully')
    except Exception as e:
        db.rollback()
        await ctx.send(f'Error: {e}')

@bot.command()
@commands.is_owner()
async def delete_account(ctx, username: str):
    try:
        with db.cursor() as cur:
            cur.execute('DELETE FROM accounts WHERE username = %s', (username,))
            db.commit()
        await ctx.send('Account deleted successfully')
    except Exception as e:
        db.rollback()
        await ctx.send(f'Error: {e}')

@bot.command()
@commands.is_owner()
async def ban_user(ctx, username: str):
    try:
        with db.cursor() as cur:
            cur.execute('UPDATE accounts SET banned = TRUE WHERE username = %s', (username,))
            db.commit()
        await ctx.send('User banned successfully')
    except Exception as e:
        db.rollback()
        await ctx.send(f'Error: {e}')

@bot.command()
@commands.is_owner()
async def unban_user(ctx, username: str):
    try:
        with db.cursor() as cur:
            cur.execute('UPDATE accounts SET banned = FALSE WHERE username = %s', (username,))
            db.commit()
        await ctx.send('User unbanned successfully')
    except Exception as e:
        db.rollback()
        await ctx.send(f'Error: {e}')

@bot.command()
@commands.is_owner()
async def create_coupon(ctx, product: str, days: int):
    coupon = str(uuid.uuid4())
    try:
        with db.cursor() as cur:
            cur.execute('''
                INSERT INTO coupons (coupon, product, days) 
                VALUES (%s, %s, %s)
            ''', (coupon, product, days))
            db.commit()
        await ctx.send(f'Coupon: {coupon}\nCoupon created successfully')
    except Exception as e:
        db.rollback()
        await ctx.send(f'Error: {e}')

@bot.command()
@commands.is_owner()
async def delete_coupon(ctx, coupon: str):
    try:
        with db.cursor() as cur:
            cur.execute('DELETE FROM coupons WHERE coupon = %s', (coupon,))
            db.commit()
        await ctx.send('Coupon deleted successfully')
    except Exception as e:
        db.rollback()
        await ctx.send(f'Error: {e}')

@bot.command()
@commands.is_owner()
async def update_hwid(ctx, username: str, hwid: str):
    try:
        with db.cursor() as cur:
            cur.execute('UPDATE accounts SET hwid = %s WHERE username = %s', (hwid, username))
            db.commit()
        await ctx.send('HWID updated successfully')
    except Exception as e:
        db.rollback()
        await ctx.send(f'Error: {e}')

@bot.command()
@commands.is_owner()
async def extend_subscription(ctx, username: str, days: int):
    try:
        with db.cursor() as cur:
            cur.execute('''
                UPDATE accounts 
                SET until = until + interval %s day 
                WHERE username = %s
            ''', (days, username))
            db.commit()
        await ctx.send('Subscription extended successfully')
    except Exception as e:
        db.rollback()
        await ctx.send(f'Error: {e}')

@bot.command()
@commands.is_owner()
async def set_subscription(ctx, username: str, subscription: str):
    try:
        with db.cursor() as cur:
            cur.execute('UPDATE accounts SET subscription = %s WHERE username = %s', (subscription, username))
            db.commit()
        await ctx.send('Subscription set successfully')
    except Exception as e:
        db.rollback()
        await ctx.send(f'Error: {e}')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        pass
    else:
        raise error

bot.run('')
