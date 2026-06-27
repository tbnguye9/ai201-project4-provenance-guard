from audit import (
    read_log,
    write_log_entry,
    write_all_entries,
    utc_timestamp,
)

def submit_appeal(content_id, creator_reasoning):
    """
    Submit an appeal for previously classified content.
    """

    entries = read_log()

    target_entry = None

    for entry in reversed(entries):
        if (
            entry.get("content_id") == content_id
            and entry.get("event_type") == "classification"
        ):
            target_entry = entry
            break

    if target_entry is None:
        return {
            "success": False,
            "message": "Content not found."
        }

    target_entry["status"] = "under_review"
    
    write_all_entries(entries)

    appeal_entry = {
        "event_type": "appeal",
        "timestamp": utc_timestamp(),
        "content_id": content_id,
        "creator_reasoning": creator_reasoning,
        "status": "under_review"
    }

    write_log_entry(appeal_entry)

    return {
        "success": True,
        "message": "Appeal submitted successfully.",
        "status": "under_review"
    }