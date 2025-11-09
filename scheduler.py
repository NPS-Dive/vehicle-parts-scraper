# scheduler.py
# ======================================================================
# DAILY SCHEDULER USING APSCHEDULER
# Runs all scrapers or specific ones daily at a set time (e.g., 02:00).
# Keep this script running (e.g., as a background process or service).
# To run: python scheduler.py
# ======================================================================

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import asyncio

# Import scraper functions (add new ones here)
from scrapers.isaco_scraper import scrape as scrape_isaco
from scrapers.ikcopart_scraper import scrape as scrape_ikcopart
from scrapers.sapia_stopyadak_scraper import scrape as scrape_sapia_stopyadak

# ----------------------------------------------------------------------
# DAILY JOB — RUN ALL SCRAPERS
# ----------------------------------------------------------------------
async def daily_job():
    """Runs all scrapers sequentially at the scheduled time."""
    print(f"DAILY SCRAPE STARTED at {datetime.now()}")
    await scrape_isaco()
    await scrape_ikcopart()
    await scrape_sapia_stopyadak()
    print(f"DAILY SCRAPE FINISHED at {datetime.now()}")

# ----------------------------------------------------------------------
# MAIN SCHEDULER
# ----------------------------------------------------------------------
def main():
    scheduler = AsyncIOScheduler()
    # Schedule daily at 02:00 (change 'hour' and 'minute' as needed)
    scheduler.add_job(daily_job, CronTrigger(hour=2, minute=0, timezone="Asia/Tehran"))  # Iran time

    print("Scheduler started. Next run: 02:00 daily (Asia/Tehran)")
    scheduler.start()

    # Keep running forever
    loop = asyncio.get_event_loop()
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        scheduler.shutdown()
        print("Scheduler stopped.")

if __name__ == "__main__":
    main()