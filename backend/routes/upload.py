from flask import Blueprint, request, jsonify, current_app
import os
import uuid
import requests
from utils.registry_utils import load_registry, save_registry, infer_artifact_type

upload_bp = Blueprint("upload", __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")


@upload_bp.route("/upload", methods=["POST"])
def upload_artifact():
    '''
    Receive a model via url link from frontend and
    detect the type from phase 1 code
    '''
    registry_path = current_app.config["REGISTRY_PATH"]
    registry = load_registry(registry_path)
    
    data = request.get_json(silent=True) or {}
    if not data or "url" not in data:
        return jsonify({"error": "No url provided"}), 400
    
    url = (data.get("url") or "").strip()
    name = (data.get("name") or "").strip()

    if not url or not name:
        return jsonify({"error": "Missing field(s): url and name are required"}), 400
    
    try:
        artifact_type = infer_artifact_type(url)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
    # TODO: compute real rating; placeholder kept to match spec flow
    rating = 0
    if rating < 0.5:
        return jsonify({"error": "Rating too low. Not uploading."}), 424

    # Get url type
    if artifact_type == "unknown":
        return jsonify({"error": "Could not detect artifact type"}), 400
    
    artifact_id = uuid.uuid4().hex
    artifact_entry = {
        "metadata": {"name": name, "id": artifact_id, "type": artifact_type},
        "data": {"url": url}
    }

    registry[artifact_id] = artifact_entry
    save_registry(registry_path, registry)
    return jsonify(artifact_entry), 201
    # try:
    #     response = requests.post(
    #         f"http://localhost:5000/artifact/{artifact_type}",
    #         json={"url": url},
    #     )
    #     return jsonify(response.json()), response.status_code
    # except Exception as e:
    #     return jsonify({"Failed to forward to artifact endpoint": str(e)}), 500


@upload_bp.route("/artifact/<artifact_type>", methods=["POST"])
def register_artifact(artifact_type: str):
    '''
    Register artifact into registry
    Parameters:
        artifact_type: Type of url: model, dataset, code
    '''
    auth_header = request.headers.get("X-Authorization")
    if not auth_header:
        return jsonify({"error": "Missing authentication header"}), 403

    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "No url provided"}), 400

    url = data["url"]
    name = url.rstrip("/").split("/")[-1]
    id = str(uuid.uuid4())

    # Access REGISTRY_PATH only inside the function
    registry_path = current_app.config["REGISTRY_PATH"]

    registry = load_registry(registry_path)
    if not isinstance(registry, dict):
        registry = {}

    for entry in registry.values():
        if entry["data"]["url"] == url:
            return jsonify({"error": "Artifact already exists"}), 409

    rating = 0  # placeholder
    if rating < 0.5:
        return jsonify({"error": "Rating too low. Not uploading."}), 424

    artifact_entry = {
        "metadata": {"name": name, "id": id, "type": artifact_type},
        "data": {"url": url}
    }

    registry[id] = artifact_entry
    save_registry(registry_path, registry)

    return jsonify(artifact_entry), 201
