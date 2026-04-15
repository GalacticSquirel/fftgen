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
        type        – "none" | "text" | "radio" | "checkbox" | "textarea"
        fields      – list[str]  (only for type == "text")
        groups      – list[str]  (radio group names for "radio"/"checkbox")
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
                    "groups": [],
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
                elif key == "groups":
                    current["groups"] = [g.strip() for g in value.split(",") if g.strip()]
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
    next_btn = page.locator("input#NextButton")
    if next_btn.count() == 0:
        # Fallback selectors for different survey versions.
        next_btn = page.locator("input[id='NextButton']")
    if next_btn.count() == 0:
        next_btn = page.locator("a.NextButton, button.NextButton, #NextButton")
    next_btn.first.click()
    page.wait_for_load_state("domcontentloaded")


def _select_radio(page: Page, group_name: str, value: str) -> bool:
    """Select a radio button by its group name and value.

    The actual survey uses sr-only radio inputs with branded label styling,
    so we click the parent container (`.rbloption`) or the label when the
    raw input is hidden.
    """
    # Try direct radio input click first.
    radio = page.locator(f"input[name='{group_name}'][value='{value}']")
    if radio.count() > 0:
        try:
            radio.first.click(force=True)
            return True
        except Exception:
            pass

    # Fallback: click the label or parent wrapper.
    label = page.locator(f"label[for='{group_name}.{value}']")
    if label.count() > 0:
        try:
            label.first.click()
            return True
        except Exception:
            pass

    return False


def _tick_checkbox(page: Page, group_name: str) -> bool:
    """Tick a checkbox by its group name (value is always '1')."""
    cb = page.locator(f"input[name='{group_name}'][type='checkbox']")
    if cb.count() > 0:
        try:
            cb.first.check(force=True)
            return True
        except Exception:
            pass

    # Fallback: click the label.
    label = page.locator(f"label[for='{group_name}.1']")
    if label.count() > 0:
        try:
            label.first.click()
            return True
        except Exception:
            pass

    return False


# ── Page handlers (keyed by page type) ──────────────────────────────────────

def _handle_none(page: Page, page_def: dict[str, Any], step: int) -> None:
    """Handle informational pages that need no input (welcome, privacy)."""
    _screenshot(page, f"{step:02d}_{page_def['id']}")

    try:
        _click_next(page)
    except Exception:
        pass  # welcome page may auto-advance or have no Next button

    print(f"  ✔  {page_def['description']}")


def _handle_text(page: Page, page_def: dict[str, Any], step: int) -> None:
    """Handle text-input pages (survey code + price on one page)."""
    page_id = page_def["id"]

    if page_id == "survey_code_and_price":
        _enter_survey_code_and_price(page, step)
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
    """Handle radio-button pages (one or more groups per page)."""
    page_id = page_def["id"]
    response = config.RESPONSES.get(page_id, "5")
    groups = page_def.get("groups", [])

    if isinstance(response, dict):
        # Multiple groups with per-group values.
        for group_name in groups:
            value = response.get(group_name, "5")
            if not _select_radio(page, group_name, value):
                print(f"  ⚠  Could not select {group_name}={value}")
    else:
        # Single value applied to all groups on the page.
        for group_name in groups:
            if not _select_radio(page, group_name, str(response)):
                # Fallback: try selecting the first visible radio in the group.
                fallback = page.locator(f"input[name='{group_name}']")
                if fallback.count() > 0:
                    fallback.first.click(force=True)
                else:
                    print(f"  ⚠  No radio buttons found for group '{group_name}'")

    _screenshot(page, f"{step:02d}_{page_id}")

    try:
        _click_next(page)
    except PwTimeout:
        print(f"  ⚠  Timed out clicking Next on '{page_id}' – may already be on next page")
    except Exception as exc:
        print(f"  ⚠  Error advancing past '{page_id}': {exc}")

    print(f"  ✔  {page_def['description']} → {response}")


def _handle_checkbox(page: Page, page_def: dict[str, Any], step: int) -> None:
    """Handle checkbox pages (select all that apply)."""
    page_id = page_def["id"]
    selected: list[str] = config.RESPONSES.get(page_id, [])

    if not isinstance(selected, list):
        selected = [str(selected)]

    for group_name in selected:
        if not _tick_checkbox(page, group_name):
            print(f"  ⚠  Could not tick checkbox '{group_name}' on '{page_id}'")

    _screenshot(page, f"{step:02d}_{page_id}")

    try:
        _click_next(page)
    except PwTimeout:
        print(f"  ⚠  Timed out clicking Next on '{page_id}'")
    except Exception as exc:
        print(f"  ⚠  Error advancing past '{page_id}': {exc}")

    print(f"  ✔  {page_def['description']} → {selected}")


def _handle_textarea(page: Page, page_def: dict[str, Any], step: int) -> None:
    """Handle free-text comment pages."""
    page_id = page_def["id"]
    text = config.RESPONSES.get(page_id, "")

    if not text:
        print(f"  ▶  Skipping {page_def['description']} (empty in config)")
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
    "checkbox": _handle_checkbox,
    "textarea": _handle_textarea,
}


# ── Specialised text-page helpers ────────────────────────────────────────────

def _enter_survey_code_and_price(page: Page, step: int) -> None:
    """Enter the survey code (XXXX-XXXX-XXXX) and price on the entry page.

    The actual survey combines the code and price on one page with fields:
        CN1, CN2, CN3           – survey code segments
        AmountSpent1, AmountSpent2 – pounds/euros and pence/cents
    """
    # ── Survey code ──
    code = config.SURVEY_CODE
    print(f"  ▶  Entering survey code: {code}")

    code_segments = code.split("-")
    if len(code_segments) != 3 or not all(len(s) == 4 for s in code_segments):
        print(f"  ⚠  Survey code must be in XXXX-XXXX-XXXX format, got: {code}")
        return

    for i, field_id in enumerate(["CN1", "CN2", "CN3"]):
        field = page.locator(f"input#{field_id}")
        if field.count() > 0:
            field.first.fill(code_segments[i])
        else:
            print(f"  ⚠  Could not find input #{field_id}")

    # ── Price / amount spent ──
    price = config.PRICE
    print(f"  ▶  Entering price: {price}")

    parts = price.split(".")
    if len(parts) != 2:
        print(f"  ⚠  Price must be in XX.XX format, got: {price}")
        return

    dollars, cents = parts

    dollar_field = page.locator("input#AmountSpent1")
    cent_field = page.locator("input#AmountSpent2")

    if dollar_field.count() > 0 and cent_field.count() > 0:
        dollar_field.first.fill(dollars)
        cent_field.first.fill(cents)
    else:
        # Fallback: try generic text inputs after the code fields.
        text_inputs = page.locator("input[type='text']:visible")
        count = text_inputs.count()
        if count >= 5:
            # First 3 are code fields, next 2 are price fields.
            text_inputs.nth(3).fill(dollars)
            text_inputs.nth(4).fill(cents)
        else:
            print("  ⚠  Could not locate price input fields")

    _screenshot(page, f"{step:02d}_survey_code_and_price")
    _click_next(page)


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
