from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timezone
import os


health_bp = Blueprint("health", __name__)

@health_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "OK"}), 200

@health_bp.route("/health/components", methods=["GET"])
def health_check_components():
    '''
    Return per-component health diagnosis
    Params:
      - windowMinutes: length of trailing window
      - includeTimeline: default False
    '''

    # FIX SO THAT IT ACCESSES REGISTRY ON S3, NOT LOCAL
    registry_path = current_app.config["REGISTRY_PATH"]

    try:
        window_minutes = int(request.args.get("windowMinutes", 60))
        include_timeline = request.args.get("includeTimeline", "false").lower() == "true"
    except ValueError:
        window_minutes = 60
        include_timeline = False

    window_minutes = max(5, min(window_minutes, 1440))
    now = datetime.now(timezone.utc)
    registry_ok = True # Change when checks are implemented

    # Might need to change depending on what health diagnosis we have
    components = [{
        "id": "registry",
        "display_name": "Artifact Registry",
        "status": "OK" if registry_ok else "ERROR",
        "observed_at": now,
        "description": "Tracks all registered artifacts and their metadata.",
        "metrics": {
            "size_kb": os.path.getsize(registry_path) / 1024 if os.path.exists(registry_path) else 0
        },
        "issues": [] if registry_ok else [
            {
                "code": "REGISTRY_UNAVAILABLE",
                "severity": "critical",
                "summary": "Registry file missing or unreadable",
                "details": f"Path not accessible: {registry_path}"
            }
        ],
        "timeline": [],
        "logs": [
            {
                "label": "Registry File",
                "url": f"file://{registry_path}",
                "tail_available": os.path.exists(registry_path),
                "last_updated_at": now
            }
        ]
    }]

    if include_timeline:
        for comp in components:
            comp["timeline"] = [
                {
                    "bucket": datetime.now(timezone.utc).isoformat() + "Z",
                    "value": 0,
                    "unit": "events"
                }
            ]

    response = {
        "components": components,
        "generated_at": now,
        "window_minutes": window_minutes
    }

    return jsonify(response), 200
