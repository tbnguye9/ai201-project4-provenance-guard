from flask import Flask, jsonify, request
from uuid import uuid4

from audit import read_log, utc_timestamp, write_log_entry
from labels import generate_label

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Provenance Guard API is running",
        "endpoints": ["/submit", "/log"]
    })


@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json(silent=True) or {}

    text = data.get("text", "").strip()
    creator_id = data.get("creator_id", "").strip()

    if not text:
        return jsonify({"error": "Missing required field: text"}), 400

    if not creator_id:
        return jsonify({"error": "Missing required field: creator_id"}), 400

    content_id = str(uuid4())

    # Milestone 3 placeholder signal.
    llm_score = 0.75
    attribution = "uncertain"
    confidence = 0.75
    label = generate_label(attribution)

    response = {
        "content_id": content_id,
        "creator_id": creator_id,
        "attribution": attribution,
        "confidence": confidence,
        "label": label,
        "signals": {
            "llm_score": llm_score
        },
        "status": "classified"
    }

    log_entry = {
        "event_type": "classification",
        "timestamp": utc_timestamp(),
        **response
    }

    write_log_entry(log_entry)

    return jsonify(response), 200


@app.route("/log", methods=["GET"])
def get_log():
    return jsonify({"entries": read_log()}), 200


if __name__ == "__main__":
    app.run(debug=True)