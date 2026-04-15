#!/usr/bin/env python3
"""
McDonald's Food for Thoughts Survey Automation

Automates the customer feedback survey at https://www.mcdfoodforthoughts.com/
using Playwright. Configure your receipt code and desired responses in config.py.

The list and order of survey pages is read from survey.txt so that every page
is programmable through config.py without touching automation code.

Usage:
    python automate_survey.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Locator, Page, sync_playwright, TimeoutError as PwTimeout

import config


SURVEY_URL = "https://www.mcdfoodforthoughts.com/"


# ── Survey-definition parser ────────────────────────────────────────────────

def parse_survey_file(filepath: str) -> list[dict[str, Any]]:
    """Parse *survey.txt* and return an ordered list of page definitions.

    Each element is a dict with keys:
        id          – page identifier (matches config.RESPONSES keys)
        type        – "none" | "text" | "radio" | "textarea"
        fields      – list[str]  (only for type == "text")
        options     – list[str]  (only for type == "radio")
        description – human-readable label
    """
    pages: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    with open(filepath, encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()

            # Skip blank lines and comments.
            if not line or line.startswith("#"):
                continue

            # New page header: [page_id]
            if line.startswith("[") and line.endswith("]"):
                if current is not None:
                    pages.append(current)
                page_id = line[1:-1].strip()
                current = {
                    "id": page_id,
                    "type": "none",
                    "fields": [],
                    "options": [],
                    "description": page_id,
                }
                continue

            # Key = value inside a page block.
            if "=" in line and current is not None:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()

                if key == "type":
                    current["type"] = value
                elif key == "fields":
                    current["fields"] = [f.strip() for f in value.split(",") if f.strip()]
                elif key == "options":
                    current["options"] = [o.strip() for o in value.split(",") if o.strip()]
                elif key == "description":
                    current["description"] = value

    # Don't forget the last page.
    if current is not None:
        pages.append(current)

    return pages


# ── Helpers ──────────────────────────────────────────────────────────────────

def _screenshot(page: Page, name: str) -> None:
    """Save a timestamped screenshot for debugging."""
    out = Path(config.SCREENSHOT_DIR)
    out.mkdir(exist_ok=True)
    path = out / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    print(f"  📸  Screenshot saved → {path}")


def _click_next(page: Page) -> None:
    """Click the 'Next' button that advances the survey."""
    next_btn = page.locator("input[id='NextButton']")
    if next_btn.count() == 0:
        # Fallback selectors for different survey versions.
        next_btn = page.locator("a.NextButton, button.NextButton, #NextButton")
    next_btn.first.click()
    page.wait_for_load_state("domcontentloaded")


# ── Page handlers (keyed by page type) ──────────────────────────────────────

def _handle_none(page: Page, page_def: dict[str, Any], step: int) -> None:
    """Handle informational pages that need no input (welcome, validation)."""
    _screenshot(page, f"{step:02d}_{page_def['id']}")

    if page_def["id"] == "validation_code":
        _capture_validation_code(page)
        return  # Final page – nothing to advance to.

    try:
        _click_next(page)
    except Exception:
        pass  # welcome page may auto-advance or have no Next button


def _handle_text(page: Page, page_def: dict[str, Any], step: int) -> None:
    """Handle text-input pages (survey code, price)."""
    page_id = page_def["id"]

    if page_id == "survey_code":
        _enter_survey_code(page, step)
    elif page_id == "price":
        _enter_price(page, step)
    else:
        # Generic text-field handler: fill visible text inputs in order.
        values = config.RESPONSES.get(page_id, "").split(",")
        text_inputs = page.locator("input[type='text']:visible")
        for i in range(min(len(values), text_inputs.count())):
            text_inputs.nth(i).fill(values[i].strip())
        _screenshot(page, f"{step:02d}_{page_id}")
        _click_next(page)

    print(f"  ✔  {page_def['description']}")


def _handle_radio(page: Page, page_def: dict[str, Any], step: int) -> None:
    """Handle radio-button pages (satisfaction ratings, visit type, …)."""
    page_id = page_def["id"]
    value = config.RESPONSES.get(page_id, "1")

    radios = page.locator("input[type='radio']:visible")
    if radios.count() == 0:
        print(f"  ⚠  No radio buttons found for '{page_def['description']}' – skipping")
    else:
        # Group radios by their name attribute.
        groups: dict[str, list[Locator]] = {}
        for i in range(radios.count()):
            name = radios.nth(i).get_attribute("name") or f"group_{i}"
            groups.setdefault(name, []).append(radios.nth(i))

        for _group_name, group_radios in groups.items():
            selected = False
            for radio in group_radios:
                if radio.get_attribute("value") == value:
                    radio.click()
                    selected = True
                    break
            if not selected and group_radios:
                group_radios[0].click()

    _screenshot(page, f"{step:02d}_{page_id}")

    try:
        _click_next(page)
    except PwTimeout:
        print(f"  ⚠  Timed out clicking Next on '{page_id}' – may already be on next page")
    except Exception as exc:
        print(f"  ⚠  Error advancing past '{page_id}': {exc}")

    print(f"  ✔  {page_def['description']} → {value}")


def _handle_textarea(page: Page, page_def: dict[str, Any], step: int) -> None:
    """Handle free-text comment pages."""
    page_id = page_def["id"]
    text = config.RESPONSES.get(page_id, "")

    if not text:
        print(f"▶ Skipping {page_def['description']} (empty in config)")
        _screenshot(page, f"{step:02d}_{page_id}_skipped")
        try:
            _click_next(page)
        except Exception:
            pass
        return

    textarea = page.locator("textarea:visible")
    if textarea.count() > 0:
        textarea.first.fill(text)
        _screenshot(page, f"{step:02d}_{page_id}")
        _click_next(page)
        print(f"  ✔  {page_def['description']} submitted")
    else:
        _screenshot(page, f"{step:02d}_{page_id}_not_found")
        print(f"  ⚠  No textarea found for '{page_def['description']}'")


_PAGE_HANDLERS = {
    "none": _handle_none,
    "text": _handle_text,
    "radio": _handle_radio,
    "textarea": _handle_textarea,
}


# ── Specialised text-page helpers ────────────────────────────────────────────

def _enter_survey_code(page: Page, step: int) -> None:
    """Enter the survey code (XXXX-XXXX-XXXX) from the receipt."""
    print(f"▶ Entering survey code: {config.SURVEY_CODE}")

    code_segments = config.SURVEY_CODE.split("-")
    if len(code_segments) != 3 or not all(len(s) == 4 for s in code_segments):
        print(f"  ⚠  Survey code must be in XXXX-XXXX-XXXX format, got: {config.SURVEY_CODE}")
        return

    cn_fields = page.locator("input[id^='CN']")
    if cn_fields.count() >= 3:
        for i in range(3):
            cn_fields.nth(i).fill(code_segments[i])
        _screenshot(page, f"{step:02d}_survey_code")
        _click_next(page)
    else:
        text_inputs = page.locator("input[type='text']:visible")
        if text_inputs.count() >= 3:
            for i in range(3):
                text_inputs.nth(i).fill(code_segments[i])
            _screenshot(page, f"{step:02d}_survey_code")
            _click_next(page)
        else:
            _screenshot(page, f"{step:02d}_survey_code_not_found")
            print("  ⚠  Could not locate survey code input fields – check screenshot")


def _enter_price(page: Page, step: int) -> None:
    """Enter the receipt price (XX.XX) on the price input page."""
    price = config.PRICE
    print(f"▶ Entering price: ${price}")

    parts = price.split(".")
    if len(parts) != 2:
        print(f"  ⚠  Price must be in XX.XX format, got: {price}")
        return

    dollars, cents = parts

    dollar_field = page.locator(
        "input#DollarSign, input[name='DollarSign'], input#Dollar, input[name='Dollar']"
    )
    cent_field = page.locator(
        "input#CentSign, input[name='CentSign'], input#Cent, input[name='Cent']"
    )

    if dollar_field.count() > 0 and cent_field.count() > 0:
        dollar_field.first.fill(dollars)
        cent_field.first.fill(cents)
        _screenshot(page, f"{step:02d}_price")
        _click_next(page)
        return

    text_inputs = page.locator("input[type='text']:visible")
    if text_inputs.count() >= 2:
        text_inputs.nth(0).fill(dollars)
        text_inputs.nth(1).fill(cents)
        _screenshot(page, f"{step:02d}_price")
        _click_next(page)
        return

    if text_inputs.count() == 1:
        text_inputs.first.fill(price)
        _screenshot(page, f"{step:02d}_price")
        _click_next(page)
        return

    _screenshot(page, f"{step:02d}_price_not_found")
    print("  ⚠  Could not locate the price input field – check screenshot")


def _capture_validation_code(page: Page) -> None:
    """Capture the validation/offer code shown at the end of the survey."""
    print("▶ Looking for validation code …")

    selectors = [
        ".ValCode", "#ValCode", "span.ValCode", "div.ValCode",
        ".CouponsContainer", "#finishContent",
    ]
    for sel in selectors:
        el = page.locator(sel)
        if el.count() > 0:
            text = el.first.inner_text()
            print(f"\n{'=' * 50}")
            print(f"  🎉  VALIDATION CODE: {text.strip()}")
            print(f"{'=' * 50}\n")
            return

    body_text = page.locator("body").inner_text()
    print("  ℹ  Could not locate a validation code element.")
    print("      Final page text (first 500 chars):")
    print(f"      {body_text[:500]}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    # Load the survey page definitions from survey.txt.
    survey_file = getattr(config, "SURVEY_FILE", "survey.txt")
    pages = parse_survey_file(survey_file)

    if not pages:
        print("❌  No pages found in survey definition file – nothing to do.")
        sys.exit(1)

    print("McDonald's Food for Thoughts – Survey Automation")
    print(f"Survey URL : {SURVEY_URL}")
    print(f"Survey file: {survey_file}  ({len(pages)} pages)")
    print(f"Headless   : {config.HEADLESS}")
    print(f"Slow-mo    : {config.SLOW_MO}ms")
    print()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=config.HEADLESS,
            slow_mo=config.SLOW_MO,
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        try:
            # Navigate to the survey once; then iterate through pages.
            print("▶ Opening survey …")
            page.goto(SURVEY_URL, wait_until="domcontentloaded", timeout=30_000)

            for step, page_def in enumerate(pages, start=1):
                page_type = page_def["type"]
                handler = _PAGE_HANDLERS.get(page_type)
                if handler is None:
                    print(f"  ⚠  Unknown page type '{page_type}' for '{page_def['id']}' – skipping")
                    continue
                print(f"▶ Page {step}/{len(pages)}: {page_def['description']}")
                handler(page, page_def, step)

            print("\n✅  Survey automation complete!")
        except Exception as exc:
            _screenshot(page, "error")
            print(f"\n❌  Error: {exc}", file=sys.stderr)
            sys.exit(1)
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
