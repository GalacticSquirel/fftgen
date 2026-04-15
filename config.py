"""
Configuration for the McDonald's Food for Thoughts survey automation.

Edit the values below to match your receipt and desired survey responses.
Every configurable survey page listed in survey.txt has a matching entry
in the RESPONSES dictionary so the automation can fill it in automatically.
"""

# ── Survey Definition ────────────────────────────────────────────────────────
# Path to the file that describes every survey page (order, type, options).
SURVEY_FILE = "survey.txt"

# ── Receipt Details ──────────────────────────────────────────────────────────
# The survey code printed on your McDonald's receipt (format: XXXX-XXXX-XXXX).
SURVEY_CODE = "0000-0000-0000"

# The total price from your receipt (format: XX.XX).
PRICE = "00.00"

# ── Survey Responses ─────────────────────────────────────────────────────────
# This dictionary maps every answerable page_id from survey.txt to the value
# the automation should submit.  Only pages whose type is "radio" or
# "textarea" need an entry here; "none" and "text" pages (welcome, code,
# price, validation) are handled separately.
#
# Rating scale used by the survey (typically 1-5):
#   1 = Highly Satisfied / Highly Likely
#   2 = Satisfied / Likely
#   3 = Neither Satisfied nor Dissatisfied
#   4 = Dissatisfied / Unlikely
#   5 = Highly Dissatisfied / Highly Unlikely

RESPONSES = {
    # ── Radio pages (one answer per page) ────────────────────────────────
    "visit_type": "1",               # 1=Dine-in, 2=Drive-thru, 3=Carry-out,
                                     #   4=Delivery, 5=Other
    "overall_satisfaction": "1",     # Highly Satisfied
    "food_quality": "1",             # Highly Satisfied
    "speed_of_service": "1",         # Highly Satisfied
    "friendliness": "1",             # Highly Satisfied
    "accuracy_of_order": "1",        # Highly Satisfied
    "cleanliness": "1",              # Highly Satisfied
    "value_for_money": "1",          # Highly Satisfied
    "likely_to_return": "1",         # Highly Likely
    "likely_to_recommend": "1",      # Highly Likely

    # ── Textarea pages ───────────────────────────────────────────────────
    "additional_comments": "",       # Free-text (leave empty to skip)
}

# ── Browser Settings ─────────────────────────────────────────────────────────
HEADLESS = False          # Set True to run without visible browser window
SLOW_MO = 500             # Milliseconds to wait between actions (helps stability)
SCREENSHOT_DIR = "screenshots"  # Folder for per-step screenshots
