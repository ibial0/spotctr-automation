import os
import requests
from firebase_logger import save_campaign, init_firebase

COINGECKO_API = "https://api.coingecko.com/api/v3"

def _check_url(url, timeout=8):
    if not url: return False
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
        return r.status_code < 400
    except:
        return False

def _get_coingecko_logo(coin_id):
    api_key = os.environ.get("COINGECKO_API_KEY", "")
    headers = {"x-cg-demo-api-key": api_key} if api_key else {}
    try:
        r = requests.get(f"{COINGECKO_API}/coins/{coin_id}", params={"localization": "false", "tickers": "false", "market_data": "false", "community_data": "false"}, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return data.get("image", {}).get("large") or data.get("image", {}).get("small")
    except Exception as e:
        print(f"[Gemini2] CoinGecko error: {e}")
    return None

def validate_and_deploy(verified_campaign):
    campaign = dict(verified_campaign)
    fixes = []
    print("[Gemini2] Validating...")
    if not _check_url(campaign.get("logo")):
        fallback = _get_coingecko_logo(campaign.get("coinId", ""))
        if fallback and _check_url(fallback):
            campaign["logo"] = fallback
            fixes.append("Fixed logo via CoinGecko")
        else:
            campaign["logo"] = "https://assets.coingecko.com/coins/images/1/small/bitcoin.png"
            fixes.append("Used placeholder logo")
    camp_link = campaign.get("campLink")
    if camp_link and not _check_url(camp_link):
        if camp_link.startswith("http://"):
            alt = camp_link.replace("http://", "https://")
            if _check_url(alt):
                campaign["campLink"] = alt
                fixes.append("Fixed campLink http→https")
            else:
                campaign["campLink"] = None
                fixes.append("Removed invalid campLink")
        else:
            campaign["campLink"] = None
            fixes.append("Removed invalid campLink")
    campaign["poolAmt"] = float(campaign.get("poolAmt") or 0)
    campaign["minVolume"] = float(campaign.get("minVolume") or 0)
    campaign["rumored"] = None
    campaign["rewardDateTBD"] = None
    campaign["rewardPostponed"] = None
    print(f"[Gemini2] Writing to Firebase: {campaign.get('name')}")
    try:
        init_firebase()
        save_campaign(campaign["id"], campaign)
        print(f"[Gemini2] Live: {campaign.get('name')}")
        return {"success": True, "campaign_id": campaign["id"], "campaign_name": campaign.get("name"), "fixes": fixes}
    except Exception as e:
        print(f"[Gemini2] Firebase error: {e}")
        return {"success": False, "campaign_id": campaign.get("id"), "error": str(e), "fixes": fixes}
