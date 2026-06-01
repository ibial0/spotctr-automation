from telethon.sync import TelegramClient
from telethon.sessions import StringSession

API_ID   = 31407317
API_HASH = "8c359de66040dfb05b6e745ee5a11e86"
PHONE    = "+8801733506469"

print("Connecting to Telegram...")
with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    client.start(phone=PHONE)
    session_string = client.session.save()
    print("\n" + "="*60)
    print("SESSION STRING:")
    print(session_string)
    print("="*60)
    print("Copy this and add to GitHub Secret as: TELEGRAM_SESSION_STRING")
