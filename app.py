from flask import Flask, jsonify, request
from uuid import uuid4

from audit import read_log, utc_timestamp, write_log_entry
from detector import analyze_repetition, analyze_stylometric, analyze_with_groq
from labels import generate_label
from scoring import combine_scores, get_attribution
from appeals import submit_appeal
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)



@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Provenance Guard API is running",
        "endpoints": ["/submit", "/log"]
    })


@app.route("/submit", methods=["POST"])
@limiter.limit("10 per minute;100 per day")
def submit():
    data = request.get_json(silent=True) or {}

    text = data.get("text", "").strip()
    creator_id = data.get("creator_id", "").strip()

    if not text:
        return jsonify({"error": "Missing required field: text"}), 400

    if not creator_id:
        return jsonify({"error": "Missing required field: creator_id"}), 400

    content_id = str(uuid4())

    llm_score = analyze_with_groq(text)
    stylometric_score = analyze_stylometric(text)
    repetition_score = analyze_repetition(text)

    confidence = combine_scores(llm_score, stylometric_score, repetition_score)
    attribution = get_attribution(confidence)
    label = generate_label(attribution)

    response = {
        "content_id": content_id,
        "creator_id": creator_id,
        "attribution": attribution,
        "confidence": confidence,
        "label": label,
        "signals": {
            "llm_score": llm_score,
            "stylometric_score": stylometric_score,
            "repetition_score": repetition_score
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

@app.route("/appeal", methods=["POST"])
def appeal():
    data = request.get_json(silent=True) or {}

    content_id = data.get("content_id", "").strip()
    creator_reasoning = data.get("creator_reasoning", "").strip()

    if not content_id:
        return jsonify({"error": "Missing required field: content_id"}), 400

    if not creator_reasoning:
        return jsonify({"error": "Missing required field: creator_reasoning"}), 400

    result = submit_appeal(content_id, creator_reasoning)

    if not result["success"]:
        return jsonify(result), 404

    return jsonify(result), 200

@app.route("/log", methods=["GET"])
def get_log():
    return jsonify({"entries": read_log()}), 200


if __name__ == "__main__":
    app.run(debug=True)