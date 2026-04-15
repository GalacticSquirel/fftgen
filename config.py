"""
Configuration for the McDonald's Food for Thoughts survey automation.

Edit the values below to match your receipt and desired survey responses.
"""

# ── Receipt Details ──────────────────────────────────────────────────────────
# The 26-digit survey code printed on your McDonald's receipt.
SURVEY_CODE = "00000000000000000000000000"

# ── Survey Responses ─────────────────────────────────────────────────────────
# Rating scale used by the survey (typically 1-5):
#   1 = Highly Satisfied
#   2 = Satisfied
#   3 = Neither Satisfied nor Dissatisfied
#   4 = Dissatisfied
#   5 = Highly Dissatisfied

RESPONSES = {
    "overall_satisfaction": "1",     # Highly Satisfied
    "food_quality": "1",             # Highly Satisfied
    "speed_of_service": "1",         # Highly Satisfied
    "friendliness": "1",             # Highly Satisfied
    "accuracy_of_order": "1",        # Highly Satisfied
    "cleanliness": "1",              # Highly Satisfied
    "value_for_money": "1",          # Highly Satisfied
    "likely_to_return": "1",         # Highly Likely
    "likely_to_recommend": "1",      # Highly Likely
}

# Optional free-text comment (leave empty to skip).
ADDITIONAL_COMMENTS = ""

# ── Browser Settings ─────────────────────────────────────────────────────────
HEADLESS = False          # Set True to run without visible browser window
SLOW_MO = 500             # Milliseconds to wait between actions (helps stability)
SCREENSHOT_DIR = "screenshots"  # Folder for per-step screenshots
