import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

BINANCE_DOMAINS = ["binance.com", "binance.info"]
MAX_WAIT_MS = 15000

def _is_binance_url(url):
    return any(d in url for d in BINANCE_DOMAINS)

def scrape_campaign_page(urls, message_text):
    binance_urls = [u for u in urls if _is_binance_url(u)]
    candidate_urls = binance_urls if binance_urls else urls
    if not candidate_urls:
        print("[Scraper] No URLs — using message text only")
        return {"landing_url": None, "raw_text": message_text, "source": "telegram_only"}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()
        page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (compatible; SpotCTR-Bot/1.0)"})
        for url in candidate_urls[:3]:
            try:
                print(f"[Scraper] Navigating to: {url}")
                page.goto(url, wait_until="domcontentloaded", timeout=MAX_WAIT_MS)
                time.sleep(2)
                final_url = page.url
                try:
                    page.click("button:has-text('Accept')", timeout=3000)
                except Exception:
                    pass
                raw_text = page.evaluate("() => document.body.innerText")
                if not raw_text or len(raw_text) < 100:
                    continue
                browser.close()
                print(f"[Scraper] Got {len(raw_text)} chars from {final_url}")
                return {"landing_url": final_url, "raw_text": raw_text[:12000], "source": "scrape"}
            except PlaywrightTimeout:
                print(f"[Scraper] Timeout on {url}")
            except Exception as e:
                print(f"[Scraper] Error: {e}")
        browser.close()
    print("[Scraper] All URLs failed — using message text")
    return {"landing_url": candidate_urls[0] if candidate_urls else None, "raw_text": message_text, "source": "telegram_only"}
