# cli_menu.py
# ======================================================================
# MAIN ENTRY POINT FOR THE PROJECT
# Displays a CLI menu to choose which scraper to run (Isaco, IKCO, Saipa), or run all with 'a'.
# Usage: python cli_menu.py (menu) or python cli_menu.py a (run all) or python cli_menu.py 3 (Saipa).
# ======================================================================

import asyncio
import importlib
import sys

# ----------------------------------------------------------------------
# LIST OF SCRAPERS — ADD NEW ONES HERE
# ----------------------------------------------------------------------
# Each scraper must have an async def scrape() function.
# Add new scrapers by copying the dict format.
SCRAPERS = [
    {
        "name": "Isaco",
        "module": "scrapers.isaco_scraper",
        "description": "Scrapes Isaco.ir for vehicle parts and prices (7200+ rows)"
    },
    {
        "name": "IKCO Part",
        "module": "scrapers.ikcopart_scraper",
        "description": "Scrapes ikcopart.com for vehicle parts and prices"
    },
    {
        "name": "Saipa Stopyadak",
        "module": "scrapers.sapia_stopyadak_scraper",
        "description": "Scrapes stopyadak.com for Saipa vehicle parts and prices"
    }
]

# ----------------------------------------------------------------------
# RUN A SINGLE SCRAPER
# ----------------------------------------------------------------------
async def run_scraper(scraper):
    """Loads and runs a single scraper module."""
    try:
        mod = importlib.import_module(scraper["module"])  # Load the scraper module
        print(f"\n{'='*60}")
        print(f"  RUNNING → {scraper['name']}")
        print(f"  {scraper['description']}")
        print(f"{'='*60}\n")
        await mod.scrape()  # Call the scraper's scrape() function
    except Exception as e:
        print(f"\nERROR: {scraper['name']} failed → {e}\n")

# ----------------------------------------------------------------------
# RUN ALL SCRAPERS
# ----------------------------------------------------------------------
async def run_all():
    """Runs all scrapers sequentially."""
    print("\nRUNNING ALL SCRAPERS...")
    for scraper in SCRAPERS:
        await run_scraper(scraper)
    print("\nALL SCRAPERS COMPLETE.")

# ----------------------------------------------------------------------
# SHOW THE MENU
# ----------------------------------------------------------------------
def show_menu():
    """Displays the menu of available scrapers, including 'a' for all."""
    print("\n" + " SCRAPERS MENU ".center(60, "="))
    for i, s in enumerate(SCRAPERS, 1):
        print(f"{i}. {s['name']: <20} → {s['description']}")
    print("a. Run ALL scrapers")
    print("0. Exit")
    print("=" * 60)
    choice = input("\nEnter number or 'a': ").strip().lower()
    return choice

# ----------------------------------------------------------------------
# MAIN FUNCTION
# ----------------------------------------------------------------------
async def main():
    # Command line argument (e.g., python cli_menu.py a for all, or python cli_menu.py 3 for Saipa)
    if len(sys.argv) > 1:
        choice = sys.argv[1].lower()
    else:
        choice = show_menu()

    if not choice or choice == "0":
        print("Goodbye!")
        return

    if choice == "a" or choice == "all":
        await run_all()
    else:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(SCRAPERS):
                await run_scraper(SCRAPERS[idx])
            else:
                print("Invalid choice.")
        except ValueError:
            print("Enter a number or 'a'.")

if __name__ == "__main__":
    asyncio.run(main())