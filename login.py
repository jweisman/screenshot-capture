# login_once_save_state.py
import os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

LOGIN_URL = os.getenv("LOGIN_URL") or "https://dashboard.taranis.ag/login"
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
STATE_PATH = os.getenv("STATE_PATH", "storage_state.json")

if not USERNAME or not PASSWORD:
    raise SystemExit("Set USERNAME and PASSWORD env vars.")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # do it visibly the first time
    context = browser.new_context()
    page = context.new_page()

    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60_000)

    # TODO: adjust selectors to your site
    page.get_by_placeholder("Email").fill(USERNAME)
    page.get_by_placeholder("Password").fill(PASSWORD)
    page.get_by_role("button", name="Sign in").click()

    # Wait for a logged-in landmark—e.g., avatar, dashboard, or a known selector.
    page.wait_for_selector('[data-cy="searchNav"]', timeout=60_000)

    # Persist cookies + localStorage
    context.storage_state(path=STATE_PATH)
    print(f"Saved storage to {STATE_PATH}")
    browser.close()
