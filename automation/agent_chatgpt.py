import os
import json
import time
from openai import OpenAI

SYSTEM_PROMPT = """
You are a Quality Controller for Spot CTR campaign data.

CHECK:
1. Volume type: estReward ≈ $0.70 / token_price
2. Equal type: maxParticipants ≈ total_pool_usd / 1.50
3. If trade token X, reward token Y: logo = X's logo, name/coinId = Y
4. Difficulty: Equal=Easy, Volume=Medium, others=Hard/Very Hard
5. All dates ISO format. rewardDate with no time → ends T23:59:59
6. earlyBirdSlots format: "YYYY-MM-DD HH:MM", multiplier ends with "x"
7. poolAmt = general pool only
8. rumored/rewardDateTBD/rewardPostponed must be null

OUTPUT JSON:
{
  "audit_status": "verified" | "fixed" | "rejected",
  "fixes": [],
  "reason": "if rejected",
  "campaign": { ...same schema... }
}
"""

def audit_campaign(gemini1_result):
    api_key = os.environ["OPENAI_API_KEY"]
    client = OpenAI(api_key=api_key)
    user_message = f"""
Audit this campaign:
CAMPAIGN JSON:
{json.dumps(gemini1_result.get('campaign'), indent=2)}
SUMMARY: {gemini1_result.get('summary', '')}
"""
    print("[ChatGPT] Auditing...")
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_message}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content.strip())
            print(f"[ChatGPT] Status: {result.get('audit_status')}")
            return result
        except Exception as e:
            print(f"[ChatGPT] Error attempt {attempt+1}: {e}")
            if attempt < 2: time.sleep(2 ** attempt)
    return {"audit_status": "rejected", "reason": "ChatGPT failed", "campaign": None, "fixes": []}
