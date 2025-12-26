

from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id = 28655452  # Replace with your actual api_id
api_hash = '57066f39c0d226f9864a14976a8dfc7e'  # Replace with your api_hash

# Create a new session to get the security session (StringSession)
with TelegramClient(StringSession(), api_id, api_hash) as client:
    print("Starting the client...")

    # This will start the login process
    client.start()

    # Once you're logged in, this will print your session string
    print("Your session string is:")
    print(client.session.save())  # This is the session string you need to save 