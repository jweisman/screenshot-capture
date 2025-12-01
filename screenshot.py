import csv
import argparse
from pathlib import Path
from collections import defaultdict
from string import Formatter
from playwright.sync_api import sync_playwright

STATE_PATH = "storage_state.json"

URL_TMPL = "https://dashboard.taranis.ag/app/insights/{org_id}/{field_id}/timeline/overview/timeline?cycle={cycle_id}&dataTypes=missions,notes,replanting,planting,precipitation,temperature,ndvi,today&disease=1&emergence=1&field_health=2,1,0&insect=1&nutrient=1&seasonId=55&seasonView=2&timeline=daysAfterPlanting,dates&weed=1"
FILENAME_TMPL = "{client_name}__{farm_name}_{field_name}_{field_id}"

def slug(s: str) -> str:
    s = (s or "").strip()
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in s)[:150]

def format_fields_used(tmpl: str) -> set:
    return {fname for _, fname, _, _ in Formatter().parse(tmpl) if fname}

def required_columns(url_tmpl: str, fname_tmpl: str) -> set:
    # Only the URL fields are *required* to build a valid target
    return format_fields_used(url_tmpl)

def build_targets_from_csv(csv_path: str, url_tmpl: str, fname_tmpl: str):
    req = required_columns(url_tmpl, fname_tmpl)
    targets = []
    #seen = set()
    with open(csv_path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        headers = set(r.fieldnames or [])
        missing_headers = req - headers
        if missing_headers:
            raise SystemExit(
                f"CSV is missing required columns for URL template: {', '.join(sorted(missing_headers))}"
            )

        for i, row in enumerate(r, start=2):  # 1-based header, so data starts at line 2
            # Clean raw row values (no slugging yet)
            clean = {k: (v or "").strip() for k, v in row.items()}
            dd = defaultdict(str, clean)

            # Ensure required URL fields are non-empty
            missing_values = [k for k in req if not dd[k]]
            if missing_values:
                print(f"SKIP line {i}: missing values for {missing_values}")
                continue

            url = url_tmpl.format_map(dd)

            # Build filename with slugged values only for readability/safety
            dd_slug = defaultdict(str, {k: slug(v) for k, v in clean.items()})
            fname = fname_tmpl.format_map(dd_slug) or "shot"
            fname = f"{fname}.png"

            targets.append((url, fname))
    return targets

def main():
    ap = argparse.ArgumentParser(description="Retrieve screenshot of field timeline.")
    ap.add_argument("--input", required=True, help="Input CSV path")
    ap.add_argument("--output", help=f"Output folder, default input folder")
    args = ap.parse_args()

    input_path = Path(args.input)
    output_dir = Path(f"{input_path.parent}/{input_path.stem}")
    output_dir.mkdir(exist_ok=True)
    targets = build_targets_from_csv(args.input, URL_TMPL, FILENAME_TMPL)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            storage_state=STATE_PATH,
            viewport={"width": 1640, "height": 900},
            device_scale_factor=2,
        )

        for url, tag in targets:
          page = context.new_page()
          try:
              page.goto(url, timeout=45_000)
              mission_locators = page.locator('[data-for^="mission-"]') # Wait for any mission to appear
              mission_locators.first.wait_for(state="visible", timeout=30_000)

              page.screenshot(path=output_dir / f"{tag}", full_page=True)
              print(f"Saved {tag}  ←  {url}")
          except Exception as e:
              print(f"Field {tag} failed ({e}) ←  {url}")
          finally:
              page.close()

        browser.close()

if __name__ == "__main__":
    main()        