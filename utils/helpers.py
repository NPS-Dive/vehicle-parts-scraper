# utils/helpers.py
# ======================================================================
# SHARED UTILITIES FOR ALL SCRAPERS
# Includes logging, CSV saving with UTF-8 BOM for Persian text in Excel, date formatting,
# and **STEALTH** browser launch with fallback (chromium → firefox).
# Uses `playwright-stealth` to bypass Cloudflare and anti-bot on stopyadak.com.
# Features: Iranian mobile UA, human-like delays, proxy support (optional).
# ======================================================================

import os
import logging
from datetime import datetime
import pandas as pd
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from playwright_stealth import stealth  # ← CORRECT: stealth (not stealth_async)

# --- CONFIG FROM SETTINGS ---
from config.settings import BROWSER_FALLBACK, HEADLESS, TIMEOUT, CLOUDFLARE_TITLE

# ----------------------------------------------------------------------
# SETUP LOGGING
# ----------------------------------------------------------------------
def setup_logging(log_dir: str = "logs"):
    """
    Sets up logging to file and console with Persian support.
    :param log_dir: Folder for log files (auto-created)
    :return: Logger object
    """
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "scraper.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

# ----------------------------------------------------------------------
# SAVE TO CSV WITH UTF-8 BOM (FOR EXCEL)
# ----------------------------------------------------------------------
def save_to_csv(data: list[dict], prefix: str, output_dir: str = "output"):
    """
    Saves data to timestamped CSV with UTF-8 BOM (fixes Persian text in Excel).
    :param data: List of dicts (rows)
    :param prefix: CSV filename prefix (e.g., 'sapia_stopyadak')
    :param output_dir: Folder for CSV (auto-created)
    :return: Path to saved CSV
    """
    if not data:
        logging.warning("No data to save.")
        return None
    
    df = pd.DataFrame(data)
    df = df.drop_duplicates().sort_values("part_name")
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"{prefix}_{today}.csv"
    filepath = Path(output_dir) / filename
    os.makedirs(output_dir, exist_ok=True)
    
    df.to_csv(filepath, index=False, encoding='utf-8-sig')  # 'utf-8-sig' adds BOM for Excel
    logging.info(f"Saved {len(df)} rows to {filepath} with UTF-8 BOM")
    return filepath

# ----------------------------------------------------------------------
# GET TODAY'S DATE
# ----------------------------------------------------------------------
def get_current_date_str() -> str:
    """
    Returns today's date as YYYY-MM-DD string.
    :return: Date string
    """
    return datetime.now().strftime("%Y-%m-%d")

# ----------------------------------------------------------------------
# STEALTH BROWSER LAUNCH WITH FALLBACK
# ----------------------------------------------------------------------
async def launch_browser_with_fallback(p, start_url):
    """
    Launches browser with STEALTH + REAL IRANIAN USER-AGENT + FALLBACK.
    Bypasses Cloudflare and anti-bot on stopyadak.com.
    :param p: Playwright instance
    :param start_url: URL to test for Cloudflare
    :return: (page, context) from successful browser
    """
    logger = logging.getLogger(__name__)

    # Real Iranian mobile user-agent (from real Android device in Iran)
    IRANIAN_UA = (
        "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36"
    )

    for browser_type in BROWSER_FALLBACK:
        logger.info(f"Trying browser: {browser_type} with STEALTH")
        browser = None
        try:
            # Launch with anti-detection flags
            browser = await p[browser_type].launch(
                headless=HEADLESS,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--start-maximized",
                    "--disable-infobars",
                    "--disable-extensions",
                    "--disable-plugins",
                    "--disable-dev-shm-usage"
                ]
            )

            # Mobile context
            context = await browser.new_context(
                viewport={"width": 390, "height": 844},  # iPhone 14 size
                locale="fa-IR",
                user_agent=IRANIAN_UA,
                java_script_enabled=True,
                bypass_csp=True,
                # proxy=PROXY,  # ← UNCOMMENT IN config/settings.py IF USING PROXY
            )

            # Create page and apply stealth
            page = await context.new_page()
            await stealth(page)  # ← FIXED: stealth_async → stealth

            # Human-like delay
            import random
            await page.wait_for_timeout(random.uniform(2000, 5000))

            # Navigate and test
            logger.info(f"Testing {start_url} with {browser_type} + STEALTH...")
            await page.goto(start_url, wait_until="domcontentloaded", timeout=TIMEOUT)

            # Check for Cloudflare / anti-bot
            title = await page.title()
            body = await page.text_content("body") or ""
            if (CLOUDFLARE_TITLE.lower() in title.lower() or 
                "just a moment" in title.lower() or 
                "checking your browser" in body.lower() or
                len(body) < 1000):
                raise PWTimeout("Anti-bot or Cloudflare challenge detected")

            logger.info(f"SUCCESS with {browser_type} + STEALTH")
            return page, context

        except Exception as e:
            logger.warning(f"{browser_type} failed: {e} — switching browser")
            if browser:
                try:
                    await browser.close()
                except:
                    pass

    logger.error("ALL BROWSERS FAILED — Site may require proxy or CAPTCHA solve")
    return None, None