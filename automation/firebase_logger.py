import time
import json
import os
import firebase_admin
from firebase_admin import credentials, db

_initialized = False

def init_firebase():
    global _initialized
    if _initialized: return
    service_account_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    if not service_account_json:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON not set")
    cred = credentials.Certificate(json.loads(service_account_json))
    firebase_admin.initialize_app(cred, {"databaseURL": "https://spotctr-default-rtdb.firebaseio.com"})
    _initialized = True

def log_run(run_result):
    init_firebase()
    log_id = str(int(time.time() * 1000))
    db.reference(f"/pipeline_logs/{log_id}").set(run_result)
    print(f"[Firebase] Log saved: {log_id}")
    return log_id

def is_processed(message_id):
    init_firebase()
    return db.reference(f"/processed_ids/{message_id}").get() is True

def mark_processed(message_id):
    init_firebase()
    db.reference(f"/processed_ids/{message_id}").set(True)
    print(f"[Firebase] Marked: {message_id}")

def save_campaign(campaign_id, campaign_data):
    init_firebase()
    db.reference(f"/campaigns/{campaign_id}").set(campaign_data)
    print(f"[Firebase] Campaign saved: {campaign_id}")
