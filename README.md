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

# 3. Edit config.py with your receipt code and desired responses
#    - Set SURVEY_CODE to the 26-digit code from your receipt
#    - Adjust satisfaction ratings if needed

# 4. Run the automation
python automate_survey.py
```

## Configuration (`config.py`)

| Setting               | Description                                           |
|-----------------------|-------------------------------------------------------|
| `SURVEY_CODE`         | 26-digit code from your McDonald's receipt            |
| `RESPONSES`           | Dictionary of question → rating value (see scale below)|
| `ADDITIONAL_COMMENTS` | Free-text comment (leave empty to skip)               |
| `HEADLESS`            | `True` to run without a visible browser window        |
| `SLOW_MO`             | Milliseconds between actions (increase if unstable)   |
| `SCREENSHOT_DIR`      | Folder where per-step screenshots are saved           |

### Rating Scale

| Value | Meaning                              |
|-------|--------------------------------------|
| `"1"` | Highly Satisfied / Highly Likely     |
| `"2"` | Satisfied / Likely                   |
| `"3"` | Neither Satisfied nor Dissatisfied   |
| `"4"` | Dissatisfied / Unlikely              |
| `"5"` | Highly Dissatisfied / Highly Unlikely|

## How It Works

1. **Opens** the survey URL in a Chromium browser.
2. **Enters** the survey code from your receipt.
3. **Answers** each satisfaction question using the ratings in `config.py`.
4. **Submits** any additional comments.
5. **Captures** the validation/offer code displayed at the end.

Screenshots are saved at each step in the `screenshots/` directory so you
can verify the automation ran correctly.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Selectors not found | The survey platform may have updated its HTML. Open the survey manually, inspect elements, and update the selectors in `automate_survey.py`. |
| Timeout errors | Increase `SLOW_MO` in `config.py` (e.g., `1000`). |
| Browser not installed | Run `python -m playwright install chromium`. |
| Headless mode fails | Some surveys block headless browsers. Set `HEADLESS = False`. |

## Project Structure

```
├── automate_survey.py   # Main automation script
├── config.py            # Survey code, responses, and settings
├── requirements.txt     # Python dependencies
├── screenshots/         # Auto-generated screenshots per step
└── README.md            # This file
```

## Disclaimer

This tool is intended for automating your **own** legitimate survey
responses. Use it responsibly and in accordance with McDonald's terms of
service. The author is not responsible for misuse.
