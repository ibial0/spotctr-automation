import os
import re
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

CHANNEL = "binance_announcements"
MAX_MESSAGES = 10

def get_new_messages(processed_checker):
    api_id   = int(os.environ["TELEGRAM_API_ID"])
    api_hash = os.environ["TELEGRAM_API_HASH"]
    session  = os.environ.get("TELEGRAM_SESSION_STRING", "")
    new_messages = []
    with TelegramClient(StringSession(session), api_id, api_hash) as client:
        print(f"[Telegram] Connected. Fetching last {MAX_MESSAGES} messages...")
        for message in client.iter_messages(CHANNEL, limit=MAX_MESSAGES):
            msg_id = str(message.id)
            if processed_checker(msg_id):
                print(f"[Telegram] Skipping {msg_id} — already processed")
                continue
            text = message.text or ""
            urls = []
            if message.entities:
                for entity in message.entities:
                    from telethon.tl.types import MessageEntityTextUrl, MessageEntityUrl
                    if hasattr(entity, "url") and entity.url:
                        urls.append(entity.url)
            raw_urls = re.findall(r'https?://\S+', text)
            for u in raw_urls:
                if u not in urls:
                    urls.append(u)
            keywords = ["spot", "trading", "tournament", "campaign", "reward", "pool", "listing", "trade to earn"]
            if not any(kw in text.lower() for kw in keywords):
                print(f"[Telegram] Skipping {msg_id} — not relevant")
                continue
            new_messages.append({"message_id": msg_id, "text": text, "urls": urls})
            print(f"[Telegram] New: {msg_id}")
    print(f"[Telegram] {len(new_messages)} new messages.")
    return new_messages
