import os
import time
import datetime
from dotenv import load_dotenv
load_dotenv()
from telegram_listener import get_new_messages
from scraper import scrape_campaign_page
from agent_gemini1 import extract_campaign
from agent_chatgpt import audit_campaign
from agent_gemini2 import validate_and_deploy
from firebase_logger import log_run, is_processed, mark_processed, init_firebase

def run_pipeline():
    start_time = time.time()
    run_time = datetime.datetime.utcnow().isoformat()
    print(f"\n{'='*60}")
    print(f"[Pipeline] Starting run at {run_time} UTC")
    print(f"{'='*60}\n")
    init_firebase()
    posts_checked = 0
    campaigns_added = 0
    campaigns_rejected = 0
    details = []
    overall_status = "no_new_posts"
    try:
        new_messages = get_new_messages(is_processed)
        posts_checked = len(new_messages)
        if not new_messages:
            print("[Pipeline] No new posts found.")
            _save_log(run_time, "no_new_posts", posts_checked, 0, 0, time.time() - start_time, details, None)
            return
        overall_status = "partial"
        for msg in new_messages:
            msg_id = msg["message_id"]
            result = _process_message(msg)
            details.append(result)
            if result["action"] == "added":
                campaigns_added += 1
                mark_processed(msg_id)
            elif result["action"] == "rejected":
                campaigns_rejected += 1
                mark_processed(msg_id)
            elif result["action"] == "failed":
                pass
            else:
                mark_processed(msg_id)
        if campaigns_added > 0 and len([d for d in details if d["action"] == "failed"]) == 0:
            overall_status = "success"
        elif len([d for d in details if d["action"] == "failed"]) > 0:
            overall_status = "partial"
        else:
            overall_status = "success"
    except Exception as e:
        print(f"[Pipeline] CRITICAL ERROR: {e}")
        overall_status = "failed"
        _save_log(run_time, "failed", posts_checked, campaigns_added, campaigns_rejected,
                  time.time() - start_time, details, str(e))
        return
    duration = round(time.time() - start_time, 1)
    print(f"\n[Pipeline] Done in {duration}s | Added: {campaigns_added} | Rejected: {campaigns_rejected}")
    _save_log(run_time, overall_status, posts_checked, campaigns_added, campaigns_rejected, duration, details, None)

def _process_message(msg):
    msg_id = msg["message_id"]
    print(f"\n[Pipeline] Processing message {msg_id}...")
    try:
        scraped = scrape_campaign_page(msg["urls"], msg["text"])
        g1_result = extract_campaign(scraped)
        if not g1_result.get("eligible"):
            reason = g1_result.get("reason", "Not a spot trading campaign")
            return {"message_id": msg_id, "action": "rejected", "reason": reason, "campaign_name": None, "error": None}
        gpt_result = audit_campaign(g1_result)
        if gpt_result.get("audit_status") == "rejected":
            reason = gpt_result.get("reason", "Failed quality audit")
            return {"message_id": msg_id, "action": "rejected", "reason": f"Quality check: {reason}", "campaign_name": g1_result.get("campaign", {}).get("name"), "error": None}
        verified_campaign = gpt_result.get("campaign") or g1_result.get("campaign")
        deploy_result = validate_and_deploy(verified_campaign)
        if deploy_result.get("success"):
            return {"message_id": msg_id, "action": "added", "reason": f"Added. Fixes: {', '.join(deploy_result.get('fixes', [])) or 'None'}", "campaign_name": deploy_result.get("campaign_name"), "error": None}
        else:
            return {"message_id": msg_id, "action": "failed", "reason": "Firebase write failed", "campaign_name": verified_campaign.get("name"), "error": deploy_result.get("error")}
    except Exception as e:
        return {"message_id": msg_id, "action": "failed", "reason": "Unexpected exception", "campaign_name": None, "error": str(e)}

def _save_log(run_time, status, posts_checked, campaigns_added, campaigns_rejected, duration, details, error_message):
    log_data = {"run_time": run_time, "status": status, "posts_checked": posts_checked, "campaigns_added": campaigns_added, "campaigns_rejected": campaigns_rejected, "duration_seconds": duration, "details": details}
    if error_message:
        log_data["error_message"] = error_message
    log_run(log_data)

if __name__ == "__main__":
    run_pipeline()
