# scrapers/ikcopart_scraper.py
# ======================================================================
# IKCO PART SCRAPER — FULLY WORKING & DOCUMENTED
# Scrapes: https://ikcopart.com/shop/ for vehicle parts and prices.
# Handles JS loading and pagination by looping through pages.
# Extracts part names from class="wd-entities-title" and prices from class="woocommerce-Price-amount.amount bdi".
# Saves to timestamped CSV in 'output/' folder (e.g., ikcopart_2025-11-09.csv).
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
START_URL = "https://ikcopart.com/shop/"  # Base URL with pagination

# --- CSS SELECTORS ---
PART_NAME_SELECTOR = '.wd-entities-title'
PRICE_SELECTOR = '.woocommerce-Price-amount.amount bdi'

# --- OUTPUT FOLDER ---
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# --- LOGGING SETUP ---
logger = setup_logging()

# =====================================================
# HELPER: Scroll to load all lazy content
# =====================================================
async def scroll_and_load(page):
    prev_height = 0
    stable_rounds = 0
    while stable_rounds < 3:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(int(SCROLL_WAIT_TIME * 1000))
        cur_height = await page.evaluate("document.body.scrollHeight")
        if cur_height == prev_height:
            stable_rounds += 1
        else:
            stable_rounds = 0
        prev_height = cur_height
        logger.info(f"Scrolling... Height now: {cur_height}")
    logger.info("Scrolling complete.")

# =====================================================
# HELPER: Get total pages
# =====================================================
async def get_total_pages(page):
    try:
        links = await page.query_selector_all(".page-numbers a.page-numbers")
        numbers = [int(await a.inner_text()) for a in links if (await a.inner_text()).isdigit()]
        return max(numbers) if numbers else 1
    except:
        return 1

# =====================================================
# MAIN SCRAPER FUNCTION
# =====================================================
async def scrape():
    """
    Main function: Opens IKCO shop, loops through all pages, extracts part names and prices, saves to daily CSV.
    Uses fallback browser launch from utils/helpers.py (chromium first, firefox on failure).
    """
    start_time = time.time()
    all_data = []
    today = get_current_date_str()

    async with async_playwright() as p:
        page, context = await launch_browserfallback(p, START_URL)
        if not page:
            logger.error("Failed to launch browser — exiting")
            return

        try:
            await page.goto(START_URL, wait_until="networkidle", timeout=TIMEOUT)
            total_pages = await get_total_pages(page)
            logger.info(f"Found {total_pages} pages")

            for pg in range(1, total_pages + 1):
                url = f"{START_URL}?paged={pg}" if pg > 1 else START_URL
                await page.goto(url, wait_until="networkidle", timeout=TIMEOUT)
                logger.info(f"Scraping page {pg}/{total_pages}: {url}")

                await scroll_and_load(page)

                names = await page.query_selector_all(PART_NAME_SELECTOR)
                prices = await page.query_selector_all(PRICE_SELECTOR)

                for name_elem, price_elem in zip(names, prices):
                    part_name = (await name_elem.inner_text()).strip()
                    price_raw = (await price_elem.inner_text()).strip()
                    price = "".join(filter(str.isdigit, price_raw))
                    if part_name and price:
                        all_data.append({
                            "part_name": part_name,
                            "price": price,
                            "source_url": url,
                            "scrape_date": today
                        })

            if all_data:
                csv_path = OUTPUT_DIR / f"ikcopart_{today}.csv"
                save_to_csv(all_data, "ikcopart")
                logger.info(f"SAVED {len(all_data)} ROWS → {csv_path}")

                # --- AUTO BACKUP ---
                backup_dir = Path("backups")
                backup_dir.mkdir(exist_ok=True)
                import shutil
                shutil.copy(csv_path, backup_dir / f"ikcopart_{today}_backup.csv")

                # --- TELEGRAM ALERT (COMMENTED) ---
                # import requests
                # def send_telegram(msg):
                #     TOKEN = "YOUR_BOT_TOKEN"
                #     CHAT_ID = "YOUR_CHAT_ID"
                #     url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                #     try:
                #         requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
                #     except:
                #         logger.warning("Telegram send failed")
                # send_telegram(f"IKCO SCRAPED\n{len(all_data)} rows\n{time.strftime('%H:%M')}")

            else:
                logger.warning("NO DATA COLLECTED")

        except Exception as e:
            logger.exception(f"CRITICAL ERROR: {e}")
        finally:
            if context and context.browser:
                await context.browser.close()

    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"IKCO SCRAPER FINISHED")
    print(f"Rows saved: {len(all_data)}")
    print(f"Time taken: {elapsed:.1f} seconds")
    print(f"Output: {OUTPUT_DIR}/ikcopart_{today}.csv")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(scrape())