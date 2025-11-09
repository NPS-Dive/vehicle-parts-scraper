# config/settings.py
# ======================================================================
# CENTRAL CONFIG FOR THE PROJECT
# All scrapers read from this file for shared settings like browser options, fallback, timeouts, and URLs.
# Edit here to change behavior for all scrapers (e.g., make all headless).
# Browser fallback: Tries browsers in order from BROWSER_FALLBACK (chromium first, firefox on failure).
# Failure detection: On TimeoutError or if page title contains CLOUDFLARE_TITLE.
# ======================================================================

# Browser settings (used by all scrapers)
BROWSER_FALLBACK = ['chromium', 'firefox']  # Fallback list: chromium → firefox on failure
HEADLESS = False  # True = no browser window (production) | False = see browser (debug)
SCROLL_WAIT_TIME = 2.0  # Seconds to wait between scrolls for lazy loading
TIMEOUT = 90000  # Max wait time in ms for page loads (90 seconds)   ← FIXED: was TIMOUT

# Cloudflare detection string (if page title contains this, switch browser)
CLOUDFLARE_TITLE = 'Cloudflare'

# URLs for each scraper (edit if sites change)
ISACO_URL = "https://www.isaco.ir/قطعات"  # Isaco base URL
IKCOPART_URL = "https://ikcopart.com/shop/"  # IKCO base URL
SAPIYA_STOP_YADAK_URL = "https://stopyadak.com/Products/NewProducts"  # Saipa base URL