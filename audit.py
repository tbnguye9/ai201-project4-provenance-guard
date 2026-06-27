import json
import os
from datetime import datetime, timezone

LOG_FILE = "logs.json"


def utc_timestamp():
    return datetime.now(timezone.utc).isoformat()


def read_log():
    if not os.path.exists(LOG_FILE):
        return []

    with open(LOG_FILE, "r", encoding="utf-8") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return []


def write_log_entry(entry):
    entries = read_log()
    entries.append(entry)

    with open(LOG_FILE, "w", encoding="utf-8") as file:
        json.dump(entries, file, indent=2)

def write_all_entries(entries):
    """
    Overwrite the audit log with the provided entries.
    """

    with open(LOG_FILE, "w", encoding="utf-8") as file:
        json.dump(entries, file, indent=2)