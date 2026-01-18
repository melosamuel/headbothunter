import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = BASE_DIR + "/GUI/core/data.json"

DEFAULT_DATA = {
    "companies": [],
    "banned_titles": [],
    "banned_period_dates": []
}
