from flask import Blueprint, jsonify, request, current_app
from utils.registry_utils import load_registry, iter_registry

by_name_bp = Blueprint("by_name", __name__)

@by_name_bp.route("/artifact/byName/<name>", methods=["GET"])
def artifact_by_name(name: str):
    _ = request.headers.get("X-Authorization", "")  # required by spec; not enforcing auth here
    clean = (name or "").strip()
    if not clean:
        return jsonify({"error": "Missing or invalid artifact name"}), 400

    reg_path = current_app.config["REGISTRY_PATH"]
    registry = load_registry(reg_path) or {}

    out = []
    for aid, item in iter_registry(registry):
        meta = item.get("metadata") or {
            "name": item.get("name"),
            "version": item.get("version"),
            "type": item.get("type"),
            "id": item.get("id"),
        }
        if (meta.get("name") or "").strip().lower() == clean.lower():
            out.append({
                "name": meta.get("name"),
                "version": meta.get("version"),
                "id": meta.get("id") or aid,
                "type": meta.get("type"),
            })

    if not out:
        return jsonify({"error": "No such artifact"}), 404
    return jsonify(out), 200