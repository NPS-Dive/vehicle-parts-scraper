# Vehicle Parts Scraper

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![Framework](https://img.shields.io/badge/framework-Playwright-lightgrey)
![Status](https://img.shields.io/badge/status-active-success)
![License](https://img.shields.io/badge/license-MIT-green)

Vehicle Parts Scraper is a Playwright-based Python project for scraping vehicle parts data from multiple Iranian online marketplaces.
It uses asynchronous browser automation, shared configuration, and reusable utilities to collect parts, prices, and related metadata into structured CSV files.

The project is designed to be modular, configurable, and suitable for both manual runs and automated scheduled execution.

---

## Features

- Asynchronous web scraping using Playwright
- Multiple site-specific scrapers:
  - ISACO (https://www.isaco.ir/قطعات)
  - IKCO Part (https://ikcopart.com/shop/)
  - Saipa StopYadak (https://stopyadak.com/Products/NewProducts)
- Shared configuration via `config/settings.py`
- Browser fallback logic (tries Chromium first, then Firefox)
- Headless and headed execution modes
- Basic Cloudflare / anti-bot handling with custom user agent and human-like delays
- CLI menu to choose which scraper to run or run all
- Daily scheduler using APScheduler
- Structured logging to file and console
- CSV export with UTF-8 BOM for Excel compatibility
- Easy extension for adding new scrapers

---

## Project Structure

```text
vehicle-parts-scraper/
├── scrapers/
│   ├── ikcopart_scraper.py
│   ├── isaco_scraper.py
│   ├── sapia_stopyadak_scraper.py
│   └── __init__.py
├── utils/
│   ├── helpers.py
│   └── __init__.py
├── config/
│   ├── settings.py
│   └── __init__.py
├── logs/
│   └── scraper.log            # main log file (created at runtime)
├── cli_menu.py                # interactive CLI menu
├── run_scrapers.py            # run all scrapers manually
├── scheduler.py               # daily scheduler using APScheduler
├── requirements.txt
└── README.md
```

Description of main parts:

- `scrapers/` : site-specific scraper implementations (each exposes an async `scrape()` function)
- `utils/` : shared helpers for logging, browser launch, and CSV saving
- `config/` : central configuration (browser, timeouts, URLs)
- `logs/` : log files generated at runtime
- `cli_menu.py` : main entry point for interactive usage
- `run_scrapers.py` : entry point to run all scrapers sequentially
- `scheduler.py` : sets up and runs daily scraping jobs

---

## Requirements

- Python 3.9 or higher
- Playwright and supported browsers

Install dependencies:

```bash
pip install -r requirements.txt
```

Install Playwright browsers (at least Chromium):

```bash
playwright install chromium
```

If needed, install all supported browsers:

```bash
playwright install
```

---

## How to Run

### 1. Run all scrapers manually

```bash
python run_scrapers.py
```

This will launch each scraper sequentially and create CSV output files in the `output/` directory (if configured in helpers).

### 2. Use the interactive CLI menu

```bash
python cli_menu.py
```

Example usage:

- `python cli_menu.py` → show menu and choose scraper interactively
- `python cli_menu.py a` → run all scrapers
- `python cli_menu.py 1` → run only a specific scraper (depending on menu mapping)

### 3. Run with the daily scheduler

```bash
python scheduler.py
```

The scheduler uses APScheduler to run scrapers at configured times (e.g., every day at 02:00).  
Keep this script running (or run it as a service / scheduled task) to enable automated daily scraping.

---

## Configuration

Global configuration is defined in:

```text
config/settings.py
```

Key options include:

- `BROWSER_FALLBACK` : list of browsers to try in order (e.g., `['chromium', 'firefox']`)
- `HEADLESS` : `True` for headless mode, `False` to see the browser window
- `SCROLL_WAIT_TIME` : delay between scrolls for lazy-loaded pages
- `TIMEOUT` : page load timeout in milliseconds
- `CLOUDFLARE_TITLE` : page title substring used to detect Cloudflare and switch browser
- `ISACO_URL`, `IKCOPART_URL`, `SAPIYA_STOP_YADAK_URL` : base URLs for each scraper

Adjust these settings to control browser behavior, timeouts, and target URLs without changing scraper code.

---

## Output and Logs

- CSV files are saved with timestamped names in the configured output directory (e.g., `output/ikcopart_YYYY-MM-DD.csv`).
- Logs are written to `logs/scraper.log` and printed to the console.
- CSVs are saved with UTF-8 BOM to ensure correct display in Excel and similar tools.

---

## Extending the Project

To add a new site:

1. Create a new file in `scrapers/` (for example, `newsite_scraper.py`).
2. Implement an `async def scrape()` function that:
   - launches a browser using the shared helpers
   - collects data into a list of dictionaries
   - saves results with `save_to_csv()`
3. Import and call your new scraper in:
   - `run_scrapers.py` for manual runs
   - `cli_menu.py` for menu-based runs
   - `scheduler.py` if you want to schedule it
4. Add any new URLs or settings to `config/settings.py`.

---

## Disclaimer

This project is intended for educational and research purposes.  
Always respect target websites' terms of service and applicable laws when scraping data.

---

## License

MIT License
