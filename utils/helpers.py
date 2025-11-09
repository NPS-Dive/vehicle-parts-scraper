# utils/helpers.py
# ======================================================================
# SHARED UTILITIES — FULL MANUAL STEALTH (NO playwright-stealth)
# Works on Python 3.13.7 — Bypasses Cloudflare & anti-bot on stopyadak.com
# Uses Playwright's built-in evasion + Iranian mobile UA + human delays
# ======================================================================

import os
import logging
from datetime import datetime
import pandas as pd
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

# --- CONFIG FROM SETTINGS ---
from config.settings import BROWSER_FALLBACK, HEADLESS, TIMEOUT, CLOUDFLARE_TITLE

# ----------------------------------------------------------------------
# SETUP LOGGING
# ----------------------------------------------------------------------
def setup_logging(log_dir: str = "logs"):
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
# SAVE TO CSV WITH UTF-8 BOM
# ----------------------------------------------------------------------
def save_to_csv(data: list[dict], prefix: str, output_dir: str = "output"):
    if not data:
        logging.warning("No data to save.")
        return None
    df = pd.DataFrame(data)
    df = df.drop_duplicates().sort_values("part_name")
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"{prefix}_{today}.csv"
    filepath = Path(output_dir) / filename
    os.makedirs(output_dir, exist_ok=True)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    logging.info(f"Saved {len(df)} rows to {filepath} with UTF-8 BOM")
    return filepath

# ----------------------------------------------------------------------
# GET TODAY'S DATE
# ----------------------------------------------------------------------
def get_current_date_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")

# ----------------------------------------------------------------------
# MANUAL STEALTH BROWSER LAUNCH (NO playwright-stealth)
# ----------------------------------------------------------------------
async def launch_browser_with_fallback(p, start_url):
    """
    Full manual stealth — bypasses Cloudflare & anti-bot on stopyadak.com
    Works on Python 3.13.7
    """
    logger = logging.getLogger(__name__)

    # Real Iranian mobile UA
    IRANIAN_UA = (
        "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36"
    )

    for browser_type in BROWSER_FALLBACK:
        logger.info(f"Trying browser: {browser_type} with MANUAL STEALTH")
        browser = None
        try:
            browser = await p[browser_type].launch(
                headless=HEADLESS,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    "--disable-extensions",
                    "--disable-plugins",
                    "--disable-dev-shm-usage",
                    "--start-maximized",
                    "--disable-web-security",
                    "--allow-running-insecure-content",
                    "--disable-features=IsolateOrigins,site-per-process"
                ]
            )

            context = await browser.new_context(
                viewport={"width": 390, "height": 844},
                locale="fa-IR",
                user_agent=IRANIAN_UA,
                java_script_enabled=True,
                bypass_csp=True,
                permissions=["geolocation"],
                color_scheme="light",
                reduced_motion="no-preference",
            )

            # === MANUAL STEALTH INJECTIONS ===
            page = await context.new_page()

            # 1. Remove webdriver flag
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false,
                });
            """)

            # 2. Mock plugins
            await page.add_init_script("""
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
            """)

            # 3. Mock languages
            await page.add_init_script("""
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['fa-IR', 'fa', 'en-US', 'en'],
                });
            """)

            # 4. Mock chrome runtime
            await page.add_init_script("""
                window.chrome = {
                    runtime: {},
                    loadTimes: () => {},
                    csi: () => {},
                };
            """)

            # 5. Mock permissions
            await page.add_init_script("""
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: 'denied' }) :
                    originalQuery(parameters)
                );
            """)

            # Human delay
            import random
            await page.wait_for_timeout(random.uniform(2000, 5000))

            # Navigate
            logger.info(f"Testing {start_url} with {browser_type} + MANUAL STEALTH...")
            await page.goto(start_url, wait_until="domcontentloaded", timeout=TIMEOUT)

            # Check for blocks
            title = await page.title()
            body = await page.text_content("body") or ""
            if (CLOUDFLARE_TITLE.lower() in title.lower() or 
                "just a moment" in title.lower() or 
                "checking your browser" in body.lower() or
                len(body) < 1000):
                raise PWTimeout("Anti-bot detected")

            logger.info(f"SUCCESS with {browser_type} + MANUAL STEALTH")
            return page, context

        except Exception as e:
            logger.warning(f"{browser_type} failed: {e} — switching")
            if browser:
                try:
                    await browser.close()
                except:
                    pass

    logger.error("ALL BROWSERS FAILED — Try proxy or slower rate")
    return None, None