# scrapers/isaco_scraper.py
# ======================================================================
# ISACO SCRAPER — FULLY WORKING & DOCUMENTED
# Scrapes: https://www.isaco.ir/قطعات for vehicle parts and prices (7200+ rows).
# Handles JS loading by waiting for cards, clicks "مشاهده قیمت", extracts table rows.
# Saves to timestamped CSV in 'output/' folder (e.g., isaco_2025-11-09.csv).
# Uses fallback browser launch from utils/helpers.py (chromium first, firefox on failure).
# For daily runs, use scheduler.py or Windows Task Scheduler.
# Telegram bot code is commented out — enable when you have a bot.
# ======================================================================

import asyncio
import time
from urllib.parse import urljoin
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PWTimeout

# --- SHARED UTILS ---
from utils.helpers import setup_logging, save_to_csv, get_current_date_str, launch_browser_with_fallback

# --- CONFIG FROM SETTINGS ---
from config.settings import TIMEOUT, SCROLL_WAIT_TIME   # ← FIXED: TIMOUT → TIMEOUT

# --- CONFIGURATION ---
START_URL = "https://www.isaco.ir/قطعات"  # Base URL

# --- CSS SELECTORS (from your specs) ---
CARD_SELECTOR = 'div.Parts_partsItem__josVI'  # Product card
SHOW_PRICE_BTN = '.MuiButton-containedPrimary'  # "مشاهده قیمت" button
TABLE_ROW = 'tr.PartsDetails_rowOfTable__vm_Zw'  # Price table rows

# --- OUTPUT FOLDER ---
OUTPUT_DIR = Path("output")  # Folder for CSVs (auto-created)
OUTPUT_DIR.mkdir(exist_ok=True)

# --- LOGGING SETUP ---
logger = setup_logging()

# =====================================================
# HELPER: Click button with timeout
# =====================================================
async def wait_and_click(page, selector, timeout=30000):
    """
    Waits for a button/link to appear and clicks it.
    :param page: Playwright page object
    :param selector: CSS selector
    :param timeout: Max wait in ms
    """
    try:
        await page.wait_for_selector(selector, timeout=timeout)
        await page.click(selector)
        logger.info(f"Clicked: {selector}")
    except PWTimeout:
        logger.error(f"Timeout: Could not find or click → {selector}")

# =====================================================
# MAIN SCRAPER FUNCTION
# =====================================================
async def scrape():
    """
    Main function: Opens the Isaco page, loops through all product cards, clicks "مشاهده قیمت", extracts table data, saves to daily CSV.
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
            # --- STEP 1: Open the base URL ---
            logger.info(f"Navigating to: {START_URL}")
            await page.goto(START_URL, wait_until="networkidle", timeout=TIMEOUT)

            # --- STEP 2: Wait for product cards ---
            await page.wait_for_selector(CARD_SELECTOR, timeout=60000)
            cards = await page.query_selector_all(CARD_SELECTOR)
            logger.info(f"Found {len(cards)} product cards")

            # --- STEP 3: Loop through each card ---
            for idx, card in enumerate(cards, 1):
                try:
                    # Get the <a> link inside the card
                    link_elem = await card.query_selector('a')
                    if not link_elem:
                        logger.warning(f"Card {idx}: No link found")
                        continue

                    href = await link_elem.get_attribute("href")
                    full_url = urljoin(page.url, href)  # Make full URL
                    logger.info(f"[{idx}/{len(cards)}] Opening: {full_url}")

                    # Open detail page in new tab
                    new_page = await context.new_page()
                    await new_page.goto(full_url, wait_until="networkidle", timeout=TIMEOUT)

                    # --- STEP 4: Click "مشاهده قیمت" ---
                    await wait_and_click(new_page, SHOW_PRICE_BTN)

                    # --- STEP 5: Wait for price table ---
                    await new_page.wait_for_selector(TABLE_ROW, timeout=30000)

                    # --- STEP 6: Extract each row ---
                    rows = await new_page.query_selector_all(TABLE_ROW)
                    logger.info(f"  → Found {len(rows)} price rows")

                    for row in rows:
                        tds = await row.query_selector_all("td")
                        if len(tds) >= 4:
                            part_no = (await tds[0].inner_text()).strip()
                            name = (await tds[1].inner_text()).strip()
                            brand = (await tds[2].inner_text()).strip()
                            price_raw = (await tds[3].inner_text()).strip()
                            price = "".join(filter(str.isdigit, price_raw))  # Clean price to integer

                            all_data.append({
                                "part_number": part_no,
                                "part_name": name,
                                "brand": brand,
                                "price": price,
                                "source_url": full_url,
                                "scrape_date": today
                            })

                    # Close tab and small delay
                    await new_page.close()
                    await asyncio.sleep(1)  # Be gentle

                except Exception as e:
                    logger.error(f"Failed on card {idx}: {e}")

            # --- STEP 7: Save to daily CSV ---
            if all_data:
                csv_path = OUTPUT_DIR / f"isaco_{today}.csv"
                save_to_csv(all_data, "isaco")  # Use helper to save
                logger.info(f"SAVED {len(all_data)} ROWS → {csv_path}")

                # --- AUTO BACKUP ---
                backup_dir = Path("backups")
                backup_dir.mkdir(exist_ok=True)
                import shutil
                shutil.copy(csv_path, backup_dir / f"isaco_{today}_backup.csv")
                logger.info(f"BACKUP → backups/isaco_{today}_backup.csv")

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
                # send_telegram(f"ISACO SCRAPED\n{len(all_data)} rows\n{time.strftime('%H:%M')}")

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
    print(f"ISACO SCRAPER FINISHED")
    print(f"Rows saved: {len(all_data)}")
    print(f"Time taken: {elapsed:.1f} seconds")
    print(f"Output: {OUTPUT_DIR}/isaco_{today}.csv")
    print(f"{'='*60}\n")

# =====================================================
# RUN DIRECTLY (for testing)
# =====================================================
if __name__ == "__main__":
    asyncio.run(scrape())