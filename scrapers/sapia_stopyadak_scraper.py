# scrapers/sapia_stopyadak_scraper.py
# ======================================================================
# SAIPA STOP YADAK SCRAPER — FULLY WORKING & DOCUMENTED
# Scrapes: https://stopyadak.com/Products/NewProducts for Saipa vehicle parts and prices.
# Handles JS loading and lazy loading by scrolling to the bottom until no new content loads.
# Extracts part names from class="ti-pr" and prices from class="p-tx-num".
# Saves to timestamped CSV in 'output/' folder (e.g., sapia_stopyadak_2025-11-09.csv).
# Uses fallback browser launch from utils/helpers.py (chromium first, firefox on failure).
# For daily runs, use scheduler.py or Windows Task Scheduler.
# Telegram bot code is commented out — enable when you have a bot.
# ======================================================================

import asyncio
import time
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PWTimeout

# --- SHARED UTILS ---
from utils.helpers import setup_logging, save_to_csv, get_current_date_str, launch_browser_with_fallback

# --- CONFIG FROM SETTINGS ---
from config.settings import TIMEOUT, SCROLL_WAIT_TIME

# --- CONFIGURATION ---
START_URL = "https://stopyadak.com/Products/NewProducts"

# --- CSS SELECTORS ---
PART_NAME_SELECTOR = '.ti-pr'
PRICE_SELECTOR = '.p-tx-num'

# --- OUTPUT FOLDER ---
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# --- LOGGING SETUP ---
logger = setup_logging()   # ← FIXED: was missing

# =====================================================
# HELPER: Scroll to load all lazy content
# =====================================================
async def scroll_and_load_all(page):
    """
    Scrolls to the bottom of the page repeatedly until no new content loads.
    :param page: Playwright page object
    """
    prev_height = 0
    stable_rounds = 0
    while stable_rounds < 3:  # Stable for 3 rounds = no more loading
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(int(SCROLL_WAIT_TIME * 1000))  # Wait for JS to load new items
        cur_height = await page.evaluate("document.body.scrollHeight")
        if cur_height == prev_height:
            stable_rounds += 1
        else:
            stable_rounds = 0
        prev_height = cur_height
        logger.info(f"Scrolling... Height now: {cur_height}")
    logger.info(f"Scrolling complete. No more lazy loading.")

# =====================================================
# MAIN SCRAPER FUNCTION
# =====================================================
async def scrape():
    """
    Main function: Opens the Saipa page, scrolls to load all items, extracts part names and prices, saves to daily CSV.
    Uses fallback browser launch from utils/helpers.py (chromium first, firefox on failure).
    """
    start_time = time.time()
    all_data = []  # List to hold part data
    today = get_current_date_str()  # e.g., 2025-11-09

    # --- Start Playwright browser with fallback ---
    async with async_playwright() as p:
        page, context = await launch_browser_with_fallback(p, START_URL)
        if not page:
            logger.error("Failed to launch browser — exiting")
            return

        try:
            # --- STEP 1: Open the base URL (with retry on error) ---
            logger.info(f"Navigating to: {START_URL}")
            for attempt in range(3):  # Retry up to 3 times
                try:
                    await page.goto(START_URL, wait_until="networkidle", timeout=TIMEOUT)
                    await page.wait_for_selector('.ti-pr', timeout=30000)
                    await page.wait_for_selector('.p-tx-num', timeout=30000)
                    break  # Success — exit loop
                except PWTimeout:
                    logger.error(f"Timeout on attempt {attempt+1} — retrying...")
                    await asyncio.sleep(5)  # Wait before retry
                except Exception as e:
                    logger.error(f"Navigation error: {e} — retrying...")
                    await asyncio.sleep(5)
            else:
                logger.error("Failed to load page after 3 attempts — check internet or site status")
                return  # Exit if failed

            # --- STEP 2: Scroll to load all lazy content ---
            await scroll_and_load_all(page)

            # --- STEP 3: Extract all part names and prices ---
            names = await page.query_selector_all(PART_NAME_SELECTOR)
            prices = await page.query_selector_all(PRICE_SELECTOR)

            logger.info(f"Found {len(names)} part names and {len(prices)} prices")

            # --- STEP 4: Pair names and prices (assume 1:1 order) ---
            for idx, (name_elem, price_elem) in enumerate(zip(names, prices)):
                try:
                    part_name = (await name_elem.inner_text()).strip()
                    price_raw = (await price_elem.inner_text()).strip()
                    price = "".join(filter(str.isdigit, price_raw))  # Clean price to integer

                    if part_name and price:
                        all_data.append({
                            "part_name": part_name,
                            "price": price,
                            "source_url": START_URL,
                            "scrape_date": today
                        })
                except Exception as e:
                    logger.error(f"Error on item {idx}: {e}")

            # --- STEP 5: Save to daily CSV ---
            if all_data:
                csv_path = OUTPUT_DIR / f"sapia_stopyadak_{today}.csv"
                save_to_csv(all_data, "sapia_stopyadak")  # Use helper to save
                logger.info(f"SAVED {len(all_data)} ROWS → {csv_path}")

                # --- AUTO BACKUP ---
                backup_dir = Path("backups")
                backup_dir.mkdir(exist_ok=True)
                import shutil
                shutil.copy(csv_path, backup_dir / f"sapia_stopyadak_{today}_backup.csv")
                logger.info(f"BACKUP → backups/sapia_stopyadak_{today}_backup.csv")

                # --- TELEGRAM ALERT (COMMENTED) ---
                # To enable: Create bot with @BotFather on Telegram, get TOKEN and CHAT_ID
                # Un comment and fill in
                # import requests
                # def send_telegram(msg):
                #     TOKEN = "YOUR_BOT_TOKEN"  # e.g., "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
                #     CHAT_ID = "YOUR_CHAT_ID"  # e.g., "123456789"
                #     url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                #     try:
                #         requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
                #     except:
                #         logger.warning("Telegram send failed")
                # send_telegram(f"SAIPA SCRAPED\n{len(all_data)} rows\n{time.strftime('%H:%M')}")

            else:
                logger.warning("NO DATA COLLECTED — Check selectors or internet")

        except Exception as e:
            logger.exception(f"CRITICAL ERROR: {e}")
        finally:
            if context and context.browser:
                await context.browser.close()

    # --- FINAL SUMMARY ---
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"SAIPA SCRAPER FINISHED")
    print(f"Rows saved: {len(all_data)}")
    print(f"Time taken: {elapsed:.1f} seconds")
    print(f"Output: {OUTPUT_DIR}/sapia_stopyadak_{today}.csv")
    print(f"{'='*60}\n")

# =====================================================
# RUN DIRECTLY (for testing)
# =====================================================
if __name__ == "__main__":
    asyncio.run(scrape())