import asyncio
import websockets
import json

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

async def communicate():
    usr = None
    psw = None
    uri = "ws://localhost:1337"
    
    async with websockets.connect(uri, ping_interval=None, ping_timeout=None) as websocket:
        while True:
            print("\nSelect an action:")
            print("1. Register")
            print("2. Login")
            print("3. Redeem Coupon")
            print("4. Get Script")
            print("5. Report Violation")
            print("6. Exit")
            choice = input("Enter the number of your choice: ")

            if choice == '1':
                username = usr or input("Enter username: ")
                password = psw or input("Enter password: ")
                hwid = input("Enter HWID: ")
                data = {
                    "action": encode("register"),
                    "username": encode(username),
                    "password": encode(password),
                    "hwid": encode(hwid)
                }

            elif choice == '2':
                username = usr or input("Enter username: ")
                password = psw or input("Enter password: ")
                data = {
                    "action": encode("login"),
                    "username": encode(username),
                    "password": encode(password)
                }

            elif choice == '3':
                username = usr or input("Enter username: ")
                password = psw or input("Enter password: ")
                coupon = input("Enter coupon code: ")
                data = {
                    "action": encode("redeem"),
                    "username": encode(username),
                    "password": encode(password),
                    "coupon": encode(coupon)
                }

            elif choice == '4':
                username = usr or input("Enter username: ")
                password = psw or input("Enter password: ")
                hwid = input("Enter HWID: ")
                data = {
                    "action": encode("get_script"),
                    "username": encode(username),
                    "password": encode(password),
                    "hwid": encode(hwid)
                }

            elif choice == '5':
                username = usr or input("Enter username: ")
                password = psw or input("Enter password: ")
                violation = input("Enter violation message: ")
                data = {
                    "action": encode("violation"),
                    "username": encode(username),
                    "password": encode(password),
                    "violation": encode(violation)
                }

            elif choice == '6':
                print("Exiting...")
                break

            else:
                print("Invalid choice. Please try again.")
                continue

            await websocket.send(json.dumps(data))
            response = await websocket.recv()
            data = json.loads(response)
            print(f'Action response recived: {decode(data['action'])}\nSuccessed: {decode(data['success'])}\nMessage: {decode(data['message'])}')
            if decode(data['action']) == 'login' and decode(data['success']) == 'true':
                usr = username
                psw = password

if __name__ == "__main__":
    asyncio.run(communicate())
