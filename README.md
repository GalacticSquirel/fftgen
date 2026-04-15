# McDonald's Food for Thoughts – Survey Automation

Automates the customer feedback survey at
[mcdfoodforthoughts.com](https://www.mcdfoodforthoughts.com/) using
[Playwright for Python](https://playwright.dev/python/).

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Python      | 3.9+    |
| pip         | latest  |

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install the Playwright browsers (first time only)
python -m playwright install chromium

# 3. Edit config.py with your receipt code, price, and desired responses
#    - Set SURVEY_CODE to the code from your receipt (format: XXXX-XXXX-XXXX)
#    - Set PRICE to the total from your receipt (format: XX.XX)
#    - Adjust satisfaction ratings and other responses if needed

# 4. Run the automation
python automate_survey.py
```

## Configuration (`config.py`)

| Setting          | Description                                            |
|------------------|--------------------------------------------------------|
| `SURVEY_CODE`    | Survey code from your receipt (format: XXXX-XXXX-XXXX) |
| `PRICE`          | Total price from your receipt (format: XX.XX)           |
| `RESPONSES`      | Dictionary of page_id → response value (see below)     |
| `HEADLESS`       | `True` to run without a visible browser window          |
| `SLOW_MO`        | Milliseconds between actions (increase if unstable)     |
| `SCREENSHOT_DIR` | Folder where per-step screenshots are saved             |

### Rating Scale (satisfaction questions)

The survey uses a 5-point scale where **5 is the best**:

| Value | Meaning                              |
|-------|--------------------------------------|
| `"5"` | Highly Satisfied / Highly Likely     |
| `"4"` | Satisfied / Likely                   |
| `"3"` | Neither Satisfied nor Dissatisfied   |
| `"2"` | Dissatisfied / Unlikely              |
| `"1"` | Highly Dissatisfied / Highly Unlikely|

### Response Types

| Page type   | `RESPONSES` value format                                                 |
|-------------|--------------------------------------------------------------------------|
| `radio`     | `"value"` for single-group pages, `{"R000xxx": "val", ...}` for multi   |
| `checkbox`  | `["R000xxx", "R000yyy"]` – list of checkbox names to tick               |
| `textarea`  | `"free text string"` or `""` to skip                                    |

## How It Works

1. **Opens** the survey URL in a Chromium browser.
2. **Enters** the survey code and amount spent from your receipt.
3. **Answers** each satisfaction/preference question using the values in `config.py`.
4. **Ticks** checkboxes for items ordered, staff recognition, and party composition.
5. **Submits** any additional comments.
6. **Selects** how to receive the validation/offer code.

Screenshots are saved at each step in the `screenshots/` directory so you
can verify the automation ran correctly.

## Survey Pages

The full survey flow (derived from `survey_source.html`) includes:

| # | Page ID                   | Type     | Description                                    |
|---|---------------------------|----------|------------------------------------------------|
| 1 | `welcome`                 | none     | Welcome / privacy notice                       |
| 2 | `survey_code_and_price`   | text     | Enter 12-digit code + amount spent             |
| 3 | `overall_satisfaction`    | radio    | Overall satisfaction rating                    |
| 4 | `order_placement`         | radio    | Where you placed your order                    |
| 5 | `app_order`               | radio    | Whether you used the McDonald's app            |
| 6 | `satisfaction_batch_1`    | radio    | Temperature, quality, accuracy, friendliness, speed |
| 7 | `satisfaction_batch_2`    | radio    | Food appearance, restaurant cleanliness        |
| 8 | `order_accuracy`          | radio    | Order accuracy + customisation questions       |
| 9 | `customisation_correct`   | radio    | Was customisation correct (conditional)        |
| 10| `problem_experienced`     | radio    | Did you experience a problem                   |
| 11| `items_ordered`           | checkbox | Select items you ordered                       |
| 12| `friendliness_staff`      | checkbox | Which staff were friendly                      |
| 13| `friendliness_reasons`    | checkbox | Why you were satisfied with friendliness       |
| 14| `recognise_staff`         | radio    | Recognise a staff member                       |
| 15| `check_order_and_carpark` | radio    | Check order on screen + wait in carpark        |
| 16| `party_composition`       | checkbox | Who was in your party                          |
| 17| `additional_comments`     | textarea | Free-text comments                             |
| 18| `demographics`            | radio    | Gender and age                                 |
| 19| `validation_code_delivery`| radio    | How to receive validation code                 |

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Selectors not found | The survey platform may have updated its HTML. Open the survey manually, inspect elements, and update selectors in `automate_survey.py`. |
| Timeout errors | Increase `SLOW_MO` in `config.py` (e.g., `1000`). |
| Browser not installed | Run `python -m playwright install chromium`. |
| Headless mode fails | Some surveys block headless browsers. Set `HEADLESS = False`. |
| Conditional pages skipped | Some pages only appear based on previous answers (e.g., customisation). The automation handles missing elements gracefully. |

## Project Structure

```
├── automate_survey.py   # Main automation script
├── config.py            # Survey code, responses, and settings
├── survey.txt           # Survey page definitions (order, type, groups)
├── survey_source.html   # Original HTML from the survey (reference)
├── requirements.txt     # Python dependencies
├── screenshots/         # Auto-generated screenshots per step
└── README.md            # This file
```

## Adding or Removing Survey Pages

All survey pages are defined in `survey.txt`. To add a new page, append a
block like:

```ini
[my_new_question]
type = radio
groups = R000999
options = 1, 2, 3, 4, 5
description = How satisfied were you with …
```

Then add a matching entry in `config.py`:

```python
RESPONSES = {
    ...
    "my_new_question": "5",
}
```

For checkbox pages:

```ini
[my_checkboxes]
type = checkbox
groups = R000100, R000101, R000102
description = Select all that apply
```

```python
RESPONSES = {
    ...
    "my_checkboxes": ["R000100", "R000102"],
}
```

To remove a page, delete its block from `survey.txt` and the corresponding
key from `RESPONSES`. No changes to `automate_survey.py` are needed.

## Disclaimer

This tool is intended for automating your **own** legitimate survey
responses. Use it responsibly and in accordance with McDonald's terms of
service. The author is not responsible for misuse.
