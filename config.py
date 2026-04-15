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
# the automation should submit.
#
# Satisfaction rating scale (5-point, HIGH is 5):
#   5 = Highly Satisfied / Highly Likely
#   4 = Satisfied / Likely
#   3 = Neither Satisfied nor Dissatisfied
#   2 = Dissatisfied / Unlikely
#   1 = Highly Dissatisfied / Highly Unlikely
#
# For radio pages, the value is the radio button value to select.
# For radio pages with multiple groups, provide a dict mapping group name
# to value.
# For checkbox pages, provide a list of group names to tick.

RESPONSES = {
    # ── Overall satisfaction (R000002: 5=Highly Satisfied) ───────────────
    "overall_satisfaction": "5",

    # ── Order placement (R000324: 1=Speaker, 2=Crew handheld, 3=App) ────
    "order_placement": "1",

    # ── App order (R000580: 1=Yes, 2=No) ────────────────────────────────
    "app_order": "2",

    # ── Satisfaction batch 1 (5=Highly Satisfied for all) ────────────────
    #    R000010=Temperature, R000008=Quality, R000012=Accuracy,
    #    R000019=Friendliness, R000017=Speed
    "satisfaction_batch_1": {
        "R000010": "5",
        "R000008": "5",
        "R000012": "5",
        "R000019": "5",
        "R000017": "5",
    },

    # ── Satisfaction batch 2 (5=Highly Satisfied for all) ────────────────
    #    R000011=Appearance, R000020=Cleanliness
    "satisfaction_batch_2": {
        "R000011": "5",
        "R000020": "5",
    },

    # ── Order accuracy + customisation ───────────────────────────────────
    #    R000052: 1=Yes order was accurate, R000265: 2=No did not customise
    "order_accuracy": {
        "R000052": "1",
        "R000265": "2",
    },

    # ── Customisation correct (conditional, shown if R000265=1) ──────────
    "customisation_correct": "1",

    # ── Problem experienced (R000026: 2=No) ──────────────────────────────
    "problem_experienced": "2",

    # ── Items ordered (list of checkbox group names to tick) ─────────────
    #    R000037=Big Mac, R000041=Fries, etc.
    "items_ordered": ["R000037", "R000041"],

    # ── Friendliness staff (list of checkbox group names to tick) ────────
    #    R000554=Person who took order, R000553=Person who handed order
    "friendliness_staff": ["R000554", "R000553"],

    # ── Friendliness reasons (list of checkbox group names to tick) ──────
    #    R000569=Greeted me, R000570=Smiled, R000573=Kind and polite
    "friendliness_reasons": ["R000569", "R000570", "R000573"],

    # ── Recognise staff (R000054: 2=No) ──────────────────────────────────
    "recognise_staff": "2",

    # ── Check order on screen + wait in carpark ──────────────────────────
    #    R000276: 1=Yes, R000168: 2=No
    "check_order_and_carpark": {
        "R000276": "1",
        "R000168": "2",
    },

    # ── Party composition (list of checkbox group names to tick) ─────────
    #    R000057=By myself
    "party_composition": ["R000057"],

    # ── Additional comments (free text, leave empty to skip) ─────────────
    "additional_comments": "",

    # ── Demographics ─────────────────────────────────────────────────────
    #    R000064: gender (9=Prefer not to answer)
    #    R000065: age   (9=Prefer not to answer)
    "demographics": {
        "R000064": "9",
        "R000065": "9",
    },

    # ── Validation code delivery (R000383: 2=Print it) ───────────────────
    "validation_code_delivery": "2",
}

# ── Browser Settings ─────────────────────────────────────────────────────────
HEADLESS = False          # Set True to run without visible browser window
SLOW_MO = 500             # Milliseconds to wait between actions (helps stability)
SCREENSHOT_DIR = "screenshots"  # Folder for per-step screenshots
