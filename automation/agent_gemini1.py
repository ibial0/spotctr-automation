import os
import json
import time
import google.generativeai as genai

SYSTEM_PROMPT = """
You are a strict data extraction agent for Spot CTR, a Binance Spot Trading campaign tracker.

REJECT (return {"eligible": false, "reason": "..."}) if:
- Futures, Options, derivatives
- APY, staking, savings, earn products
- Network support, chain additions
- Alpha trading, VIP features
- Token Delisting
- NFT events
- Launchpool, BNB Vault

ACCEPT if:
- Spot Trading Campaign or Tournament
- New Spot Token Listing Campaign
- Trade to Earn events for spot trading

IF ELIGIBLE return this JSON:
{
  "eligible": true,
  "campaign": {
    "id": "<unix_timestamp_ms_as_string>",
    "title": "<campaign title or null>",
    "name": "<reward token symbol>",
    "coinId": "<CoinGecko coin ID of reward token>",
    "logo": "<URL of TRADING token logo from CoinGecko>",
    "campLink": "<official Binance campaign URL>",
    "poolAmt": <total reward pool as number>,
    "type": "<volume|equal|ranked_fixed|points_lb|points_nl|unestimable>",
    "estReward": "<for volume: tokens per $1000 volume = $0.70/token_price>",
    "maxParticipants": <for equal: round(pool_usd/1.50), else null>,
    "rankStart": <null or number>,
    "rankEnd": <null or number>,
    "rankEligVol": <null or number>,
    "rankMinVol": <null or number>,
    "totalPoints": <null or number>,
    "costPerPoint": <null or number>,
    "minPoints": <null or number>,
    "costPerPointNl": <null or number>,
    "minVolume": <min USD volume to qualify, 0 if none>,
    "difficulty": "<Easy|Medium|Hard|Very Hard>",
    "start": "<ISO datetime>",
    "end": "<ISO datetime>",
    "rewardDate": "<ISO datetime or null>",
    "rewardDateTBD": null,
    "rewardPostponed": null,
    "rumored": null,
    "hasEarlyBird": <true or null>,
    "earlyBirdSlots": [{"startUtc": "YYYY-MM-DD HH:MM", "endUtc": "YYYY-MM-DD HH:MM", "multiplier": "2x"}] or null
  },
  "summary": "<200-word summary>"
}

Return ONLY valid JSON, no markdown.
poolAmt = general public pool only, NOT special top-rank prizes.
"""

def extract_campaign(scraped_data):
    api_key = os.environ["GEMINI_1_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=SYSTEM_PROMPT)
    user_prompt = f"""
CAMPAIGN PAGE URL: {scraped_data.get('landing_url', 'N/A')}
CAMPAIGN PAGE TEXT:
{scraped_data.get('raw_text', '')}
Current timestamp for ID: {int(time.time() * 1000)}
Return ONLY JSON.
"""
    print("[Gemini1] Extracting...")
    for attempt in range(3):
        try:
            response = model.generate_content(user_prompt)
            raw = response.text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()
            result = json.loads(raw)
            print(f"[Gemini1] Eligible: {result.get('eligible')}")
            return result
        except json.JSONDecodeError as e:
            print(f"[Gemini1] JSON error attempt {attempt+1}: {e}")
            if attempt < 2: time.sleep(2 ** attempt)
        except Exception as e:
            print(f"[Gemini1] API error attempt {attempt+1}: {e}")
            if attempt < 2: time.sleep(2 ** attempt)
    return {"eligible": False, "reason": "Gemini 1 failed after 3 attempts"}
