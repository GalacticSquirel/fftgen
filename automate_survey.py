#!/usr/bin/env python3
"""
McDonald's Food for Thoughts Survey Automation

Automates the customer feedback survey at https://www.mcdfoodforthoughts.com/
using Playwright. Configure your receipt code and desired responses in config.py.

Usage:
    python automate_survey.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from playwright.sync_api import Page, sync_playwright, TimeoutError as PwTimeout

import config


SURVEY_URL = "https://www.mcdfoodforthoughts.com/"


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


def _enter_price(page: Page) -> None:
    """Enter the receipt price (XX.XX) on the price input page."""
    price = config.PRICE
    print(f"▶ Entering price: ${price}")

    # Split price into dollars and cents (e.g. "12.34" → "12", "34").
    parts = price.split(".")
    if len(parts) != 2:
        print(f"  ⚠  Price must be in XX.XX format (dollars.cents), got: {price}")
        return

    dollars, cents = parts

    # Try to find dedicated dollar/cent fields.
    dollar_field = page.locator("input#DollarSign, input[name='DollarSign'], input#Dollar, input[name='Dollar']")
    cent_field = page.locator("input#CentSign, input[name='CentSign'], input#Cent, input[name='Cent']")

    if dollar_field.count() > 0 and cent_field.count() > 0:
        dollar_field.first.fill(dollars)
        cent_field.first.fill(cents)
        _screenshot(page, "02b_price_entered")
        _click_next(page)
        print("  ✔  Price submitted (dollar/cent fields)")
        return

    # Fallback: look for visible text inputs on the current page.
    text_inputs = page.locator("input[type='text']:visible")
    if text_inputs.count() >= 2:
        text_inputs.nth(0).fill(dollars)
        text_inputs.nth(1).fill(cents)
        _screenshot(page, "02b_price_entered")
        _click_next(page)
        print("  ✔  Price submitted (generic text inputs)")
        return

    if text_inputs.count() == 1:
        text_inputs.first.fill(price)
        _screenshot(page, "02b_price_entered")
        _click_next(page)
        print("  ✔  Price submitted (single input)")
        return

    _screenshot(page, "02b_price_field_not_found")
    print("  ⚠  Could not locate the price input field – check screenshot")


def _select_radio(page: Page, value: str) -> None:
    """Select a radio button by its value on the current question page."""
    radio = page.locator(f"input[type='radio'][value='{value}']")
    if radio.count() > 0:
        radio.first.click()
    else:
        # Some survey versions use table-based layouts.
        radio = page.locator(f"td.Opt{value} input, label:has-text('{value}') input")
        if radio.count() > 0:
            radio.first.click()
        else:
            print(f"  ⚠  Could not find radio button with value '{value}'")


# ── Survey Steps ─────────────────────────────────────────────────────────────

def step_welcome(page: Page) -> None:
    """Navigate to the survey and verify the landing page loads."""
    print("▶ Opening survey …")
    page.goto(SURVEY_URL, wait_until="domcontentloaded", timeout=30_000)
    _screenshot(page, "01_welcome")
    print("  ✔  Welcome page loaded")


def step_enter_code(page: Page) -> None:
    """Enter the survey code (XXXX-XXXX-XXXX) and price from the receipt."""
    print(f"▶ Entering survey code: {config.SURVEY_CODE}")

    # Split the XXXX-XXXX-XXXX code into its three segments.
    code_segments = config.SURVEY_CODE.split("-")
    if len(code_segments) != 3 or not all(len(s) == 4 for s in code_segments):
        print(f"  ⚠  Survey code must be in XXXX-XXXX-XXXX format (three 4-character segments), got: {config.SURVEY_CODE}")
        return

    # Pattern A: Multiple segmented input fields (CN1, CN2, CN3).
    cn_fields = page.locator("input[id^='CN']")
    if cn_fields.count() >= 3:
        for i in range(3):
            cn_fields.nth(i).fill(code_segments[i])
        _screenshot(page, "02_code_entered")
        _click_next(page)
        print(f"  ✔  Code submitted (3 segmented fields)")
    else:
        # Fallback: try generic visible text inputs in order.
        text_inputs = page.locator("input[type='text']:visible")
        if text_inputs.count() >= 3:
            for i in range(3):
                text_inputs.nth(i).fill(code_segments[i])
            _screenshot(page, "02_code_entered")
            _click_next(page)
            print("  ✔  Code submitted (generic text inputs)")
        else:
            _screenshot(page, "02_code_field_not_found")
            print("  ⚠  Could not locate the survey code input fields – check screenshot")
            return

    # Enter the price on the next page/section.
    _enter_price(page)


def step_answer_questions(page: Page) -> None:
    """Iterate through satisfaction questions and submit configured answers."""
    print("▶ Answering survey questions …")

    questions = list(config.RESPONSES.items())
    page_num = 3

    for label, value in questions:
        # Many SMG surveys show one or a few questions per page.
        # Select the appropriate radio button(s) and advance.
        radios = page.locator("input[type='radio']:visible")
        if radios.count() == 0:
            # Page may have a different input type (dropdown, scale, etc.)
            print(f"  ⚠  No radio buttons found for '{label}' – skipping")
        else:
            # If multiple radio groups on one page, handle each group.
            groups: dict[str, list[object]] = {}
            for i in range(radios.count()):
                name = radios.nth(i).get_attribute("name") or f"group_{i}"
                groups.setdefault(name, []).append(radios.nth(i))

            for group_name, group_radios in groups.items():
                # Pick the radio whose value matches the desired rating.
                selected = False
                for radio in group_radios:
                    if radio.get_attribute("value") == value:
                        radio.click()
                        selected = True
                        break
                if not selected and group_radios:
                    # Fallback: click the first radio (highest satisfaction).
                    group_radios[0].click()

        _screenshot(page, f"{page_num:02d}_{label}")
        page_num += 1

        try:
            _click_next(page)
        except PwTimeout:
            print(f"  ⚠  Timed out clicking Next on '{label}' – may already be on next page")
        except Exception as exc:
            print(f"  ⚠  Error advancing past '{label}': {exc}")

        print(f"  ✔  {label} → {value}")


def step_additional_comments(page: Page) -> None:
    """Fill in the optional free-text comment box if configured."""
    if not config.ADDITIONAL_COMMENTS:
        print("▶ Skipping additional comments (empty in config)")
        return

    print("▶ Entering additional comments …")
    textarea = page.locator("textarea:visible")
    if textarea.count() > 0:
        textarea.first.fill(config.ADDITIONAL_COMMENTS)
        _screenshot(page, "90_comments")
        _click_next(page)
        print("  ✔  Comments submitted")
    else:
        print("  ⚠  No comment textarea found on this page")


def step_capture_validation_code(page: Page) -> None:
    """Capture the validation/offer code shown at the end of the survey."""
    print("▶ Looking for validation code …")
    _screenshot(page, "99_final_page")

    # The code is usually displayed in a prominent element.
    selectors = [
        ".ValCode",
        "#ValCode",
        "span.ValCode",
        "div.ValCode",
        ".CouponsContainer",
        "#finishContent",
    ]
    for sel in selectors:
        el = page.locator(sel)
        if el.count() > 0:
            text = el.first.inner_text()
            print(f"\n{'=' * 50}")
            print(f"  🎉  VALIDATION CODE: {text.strip()}")
            print(f"{'=' * 50}\n")
            return

    # Fallback: try to find any large, bold text on the final page.
    body_text = page.locator("body").inner_text()
    print("  ℹ  Could not locate a validation code element.")
    print("      Final page text (first 500 chars):")
    print(f"      {body_text[:500]}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("McDonald's Food for Thoughts – Survey Automation")
    print(f"Survey URL : {SURVEY_URL}")
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
            step_welcome(page)
            step_enter_code(page)
            step_answer_questions(page)
            step_additional_comments(page)
            step_capture_validation_code(page)
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
