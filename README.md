# Vehicle Parts Scraper Project

## Setup
1. Clone or create the project folder.
2. `pip install -r requirements.txt`
3. `playwright install chromium`
4. Edit `config/settings.py` for time/browser.

## Run Manually
python run_scrapers.py

## Run Scheduler
python scheduler.py  # Runs forever; stop with Ctrl+C

## Output
- CSVs in `output/` (daily files).
- Logs in `logs/scraper.log`.

## Add Site
1. Copy `scrapers/ikcopart_scraper.py` to new file.
2. Update URL/selectors.
3. Import/call in `run_scrapers.py`.

## Azure DevOps
See instructions in main response. Use self-hosted agent for local server.