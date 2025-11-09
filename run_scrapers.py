# run_scrapers.py
# ======================================================================
# ENTRY POINT TO RUN ALL SCRAPERS MANUALLY
# Useful for testing or CI/CD triggers.
# Import and call new scrapers here as you add sites.
# ======================================================================

import asyncio
import sys
from scrapers.ikcopart_scraper import scrape as scrape_ikcopart
from scrapers.isaco_scraper import scrape as scrape_isaco
from scrapers.sapia_stopyadak_scraper import scrape as scrape_sapia_stopyadak

async def main():
    """
    Run all scrapers sequentially.
    """
    print("Starting manual scrape run...")
    await scrape_ikcopart()
    await scrape_isaco()
    await scrape_sapia_stopyadak()
    print("All scrapers completed.")

if __name__ == "__main__":
    asyncio.run(main())

# Explanation: Simple orchestrator. Run this for one-off tests or in Azure pipeline. Logs trace each scraper's progress.