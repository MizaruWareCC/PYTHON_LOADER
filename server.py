import psycopg2
import logging
import colorama
from colorama import Fore, Style
import asyncio
import websockets
import json
import datetime

USERS_ONLINE = 0

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

DKEY = "awganwigjhaniwgnahiuregbnagijengwujhgbawubghabwgjhbawjhgawghawj"

def encode(script: str, key: str = DKEY) -> str:
    encoded = []
    key_length = len(key)
    for i, char in enumerate(script):
        key_char = key[i % key_length]
        encoded_char = chr((ord(char) ^ ord(key_char)) + i % 256)
        encoded.append(encoded_char)
    return ''.join(encoded)

def decode(encoded: str, key: str = DKEY) -> str:
    decoded = []
    key_length = len(key)
    for i, char in enumerate(encoded):
        key_char = key[i % key_length]
        decoded_char = chr((ord(char) - i % 256) ^ ord(key_char))
        decoded.append(decoded_char)
    return ''.join(decoded)

db: psycopg2.extensions.connection = psycopg2.connect(
    user='zrxw',
    password='zrxw',
    port='5432',
    host='localhost',
    database='loader_api'
)

crs = db.cursor()

crs.execute('''
CREATE TABLE IF NOT EXISTS accounts (
    username VARCHAR(50) NOT NULL PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    hwid VARCHAR(1337) NOT NULL,
    subscription VARCHAR(255),
    until TIMESTAMP WITH TIME ZONE NOT NULL,
    banned BOOL NOT NULL
)
''')

crs.execute('''
CREATE TABLE IF NOT EXISTS coupons (
    coupon CHAR(36) PRIMARY KEY,
    product VARCHAR(255) NOT NULL,
    days INTEGER NOT NULL,
    redeemer VARCHAR(50)
)
''')

crs.close()
db.commit()

async def handle_register(ws: websockets.WebSocketServerProtocol, data: dict):
    name = decode(data.get('username'))
    password = decode(data.get('password'))
    hwid = decode(data.get('hwid'))

    cursor = db.cursor()
    try:
        cursor.execute('SELECT username, password, hwid FROM accounts WHERE hwid = %s', (hwid,))
        fetch = cursor.fetchone()
        if fetch:
            await ws.send(json.dumps({'action': encode('register'), 'success': encode('false'), 'message': encode('Multi-account detected!')}))
        else:
            cursor.execute('SELECT username, password, hwid FROM accounts WHERE username = %s', (name,))
            fetch = cursor.fetchone()
            if fetch:
                await ws.send(json.dumps({'action': encode('register'), 'success': encode('false'), 'message': encode('Username taken')}))
            else:
                if len(name) < 4 or len(name) > 50:
                    await ws.send(json.dumps({'action': encode('register'), 'success': encode('false'), 'message': encode('Username must be between 4 and 50 symbols')}))
                else:
                    if len(password) < 4 or len(password) > 256:
                        await ws.send(json.dumps({'action': encode('register'), 'success': encode('false'), 'message': encode('Password must be between 4 and 255 symbols')}))
                    else:
                        cursor.execute('INSERT INTO accounts VALUES (%s, %s, %s, %s, %s, %s)', 
                                    (name, password, hwid, None, datetime.datetime(year=1, month=1, day=1), False))
                        db.commit()
                        await ws.send(json.dumps({'action': encode('register'), 'success': encode('true'), 'message': encode('Account created, please login to continue')}))
    finally:
        cursor.close()

async def handle_login(ws: websockets.WebSocketServerProtocol, data: dict):
    name = decode(data.get('username'))
    password = decode(data.get('password'))

    cursor = db.cursor()
    try:
        cursor.execute('SELECT banned FROM accounts WHERE username = %s AND password = %s', (name, password))
        fetch = cursor.fetchone()
        
        if fetch:
            if fetch[0]:
                await ws.send(json.dumps({'action': encode('login'), 'success': encode('false'), 'message': encode('User is banned')}))
            else:
                await ws.send(json.dumps({'action': encode('login'), 'success': encode('true'), 'message': encode('Logged in successfully')}))
        else:
            await ws.send(json.dumps({'action': encode('login'), 'success': encode('false'), 'message': encode('Invalid username or password')}))
    finally:
        cursor.close()

async def handle_redeem(ws: websockets.WebSocketServerProtocol, data: dict):
    name = decode(data.get('username'))
    password = decode(data.get('password'))
    coupon = data.get('coupon')

    cursor = db.cursor()
    try:
        cursor.execute('SELECT banned FROM accounts WHERE username = %s AND password = %s', (name, password))
        fetch = cursor.fetchone()
        
        if fetch:
            if fetch[0]:
                await ws.send(json.dumps({'action': encode('redeem'), 'success': encode('false'), 'message': encode('User is banned')}))
            else:
                cursor.execute('SELECT product, days, redeemer FROM coupons WHERE coupon = %s', (coupon,))
                coupon_data = cursor.fetchone()
                if not coupon_data:
                    await ws.send(json.dumps({'action': encode('redeem'), 'success': encode('false'), 'message': encode('No coupon found')}))
                else:
                    if coupon_data[2] is not None:
                        await ws.send(json.dumps({'action': encode('redeem'), 'success': encode('false'), 'message': encode('Coupon was already redeemed by another user')}))
                    else:
                        cursor.execute('SELECT subscription, until FROM accounts WHERE username = %s', (name,))
                        fetch = cursor.fetchone()
                        if fetch[0] == 'beta' and coupon_data[0] == 'stable':
                            await ws.send(json.dumps({'action': encode('redeem'), 'success': encode('false'), 'message': encode('Coupon is for stable, when you\'re beta user')}))
                        else:
                            now = datetime.datetime.now(datetime.UTC)
                            if fetch[1] is None:
                                updated_until = now + datetime.timedelta(days=coupon_data[1])
                            elif now > fetch[1] and fetch[0] == coupon_data[0]:
                                updated_until = now + datetime.timedelta(days=coupon_data[1])
                            elif fetch[0] != coupon_data[0]:
                                updated_until = now + datetime.timedelta(days=coupon_data[1])
                            else:
                                updated_until = fetch[1] + datetime.timedelta(days=coupon_data[1])
                            
                            cursor.execute('UPDATE accounts SET until = %s, subscription = %s WHERE username = %s', 
                                           (updated_until, coupon_data[0], name))
                            cursor.execute('UPDATE coupons SET redeemer = %s WHERE coupon = %s', (name, coupon))
                            db.commit()
                            await ws.send(json.dumps({'action': encode('redeem'), 'success': encode('true'), 'message': encode(f'Used coupon for {coupon_data[0]} subscriptions for {coupon_data[1]} days')}))
        else:
            await ws.send(json.dumps({'action': encode('redeem'), 'success': encode('false'), 'message': encode('Invalid username or password')}))
    finally:
        cursor.close()

async def handle_get_script(ws: websockets.WebSocketServerProtocol, data: dict):
    name = decode(data.get('username'))
    password = decode(data.get('password'))
    hwid = decode(data.get('hwid'))

    cursor = db.cursor()
    try:
        cursor.execute('SELECT hwid, banned, subscription FROM accounts WHERE username = %s AND password = %s', (name, password))
        fetch = cursor.fetchone()
        
        if fetch:
            if fetch[1]:
                await ws.send(json.dumps({'action': encode('get_script'), 'success': encode('false'), 'message': encode('User is banned')}))
            else:
                if fetch[0] != hwid:
                    await ws.send(json.dumps({'action': encode('get_script'), 'success': encode('false'), 'message': encode('HWID mismatch')}))
                    logger.info(f'Hwid mismatch: {fetch[0]} and {hwid}')
                else:
                    if fetch[2] is None:
                        await ws.send(json.dumps({'action': encode('get_script'), 'success': encode('false'), 'message': encode('No subscription!')}))
                    else:
                        script_path = fetch[2] + '.lua'
                        try:
                            with open(script_path, 'r') as script_file:
                                script_content = script_file.read()
                            await ws.send(json.dumps({'action': encode('get_script'), 'success': encode('true'), 'message': encode(script_content)}))
                        except FileNotFoundError:
                            await ws.send(json.dumps({'action': encode('get_script'), 'success': encode('false'), 'message': encode('Script file not found')}))
        else:
            await ws.send(json.dumps({'action': encode('get_script'), 'success': encode('false'), 'message': encode('User isn\'t found, try to re logging in')}))
    finally:
        cursor.close()

async def handle_violation(ws: websockets.WebSocketServerProtocol, data: dict):
    name = decode(data.get('username'))
    password = decode(data.get('password'))
    violation = decode(data.get('violation'))

    cursor = db.cursor()
    try:
        cursor.execute('SELECT banned FROM accounts WHERE username = %s AND password = %s', (name, password))
        fetch = cursor.fetchone()
        
        if fetch:
            if fetch[0]:
                logger.error(f'{name} trying to send websocket violation as banned user: {violation}')
                await ws.send(encode('continiue'))
            else:
                logger.warning(f'{name} is violating rules: {violation}')
                await ws.send(encode('continiue'))
        else:
            logger.error(f'{name} trying to send websocket violation as not existing user: {violation}')
            await ws.send(encode('continiue'))
    finally:
        cursor.close()

async def handler(ws: websockets.WebSocketServerProtocol, path):
    global USERS_ONLINE
    logger.info('Recived connection')
    USERS_ONLINE += 1
    try:
        async for message in ws:
            data = json.loads(message)
            if not isinstance(data, dict):
                continue
            
            action = decode(data.get('action'))
            
            if action == 'register':
                await handle_register(ws, data)
            elif action == 'login':
                await handle_login(ws, data)
            elif action == 'redeem':
                await handle_redeem(ws, data)
            elif action == 'get_script':
                await handle_get_script(ws, data)
            elif action == 'violation':
                await handle_violation(ws, data)
            elif action == 'users_online':
                await ws.send(json.dumps({'action': encode('users_online'), 'message': encode(str(USERS_ONLINE))}))

            if action != 'users_online':
                logger.debug(f'Recived action: {action}')
            

    except Exception as e:
        logger.error(f"Error handling WebSocket connection: {e}")
    finally:
        await ws.close()
        USERS_ONLINE -= 1

start_server = websockets.serve(handler, "localhost", 1337, ping_interval=None, ping_timeout=None)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
