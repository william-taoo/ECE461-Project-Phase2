from flask import Blueprint, request, jsonify, current_app
import os
import uuid
import requests
from utils.registry_utils import load_registry, save_registry, infer_artifact_type
from huggingface_hub import HfApi
from urllib.parse import urlparse

register_bp = Blueprint("artifact", __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")

@register_bp.route("/artifact/<artifact_type>", methods=["POST"])
def register_artifact(artifact_type: str):
    '''
    Register artifact into registry
    Parameters:
        artifact_type: Type of url: model, dataset, code
    '''
    if artifact_type not in ("model", "dataset", "code"):
        return jsonify({"error": "invalid artifact_type"}), 400

    registry_path = current_app.config["REGISTRY_PATH"]
    registry = load_registry(registry_path)

    body = request.get_json(silent=True) or {}
    url = (body.get("url") or "").strip()
    if not url:
        return jsonify({"error": "url is required"}), 400

    try:
        detected = infer_artifact_type(url)
        if detected != artifact_type:
            return jsonify({"error": f"URL looks like {detected}, not {artifact_type}"}), 400
    except ValueError:
        pass

    for entry in (registry.values() if isinstance(registry, dict) else registry):
        if entry.get("data", {}).get("url") == url:
            return jsonify({"error": "Artifact with this URL already exists"}), 409
        
    # Check size limit, if the artifact is >5GB, reject it
    path_parts = urlparse(url).path.strip('/').split('/')
    if len(path_parts) < 2:
        return jsonify({"error": "Invalid URL"}), 400
    repo_id = f"{path_parts[0]}/{path_parts[1]}"

    # Use the HfApi to get model info, which includes file sizes
    api = HfApi()
    model_info = api.model_info(repo_id=repo_id, files_metadata=True)

    # Sum the size of all files in the repository
    total_size = sum(file.size for file in model_info.siblings if file.size is not None)

    if total_size > 5 * 1024**3:
        return jsonify({"error": "Artifact is too large"}), 424

    artifact_id = uuid.uuid4().hex
    entry = {
        "metadata": {
            "id": artifact_id,
            "name": body.get("name") or os.path.basename(url) or "unnamed",
            "version": body.get("version") or "0.0.1",
            "type": artifact_type,
        },
        "data": {"url": url},
    }

    # Temporarily save
    if isinstance(registry, dict):
        registry[artifact_id] = entry
    else:
        registry.append(entry)

    save_registry(registry_path, registry)

    # Rate the artifact
    base = request.host_url.rstrip('/')
    rate_url = f"{base}/artifact/model/{artifact_id}/rate"
    try:
        response = requests.get(rate_url)
        if response.status_code != 200:
            del registry[artifact_id]
            save_registry(registry_path, registry)
            return jsonify({"error": f"Failed to rate model: {response.text}"}), 424
        
        rating = response.json()
        net_score = rating.get("net_score", 0.0)

        if net_score < 0.5:
            # Reject artifact
            del registry[artifact_id]
            save_registry(registry_path, registry)
            return jsonify({"error": f"Model rejected. Score too low: ({net_score}). Upload failed."}), 424
        
        # Save rating in artifact entry
        final_entry = {
            "metadata": {
                "id": artifact_id,
                "name": body.get("name") or os.path.basename(url) or "unnamed",
                "version": body.get("version") or "0.0.1",
                "type": artifact_type,
                "rating": rating
            },
            "data": {"url": url},
        }

        if isinstance(registry, dict):
            registry[artifact_id] = final_entry
        else:
            registry.append(final_entry)
        save_registry(registry_path, registry)
    except Exception as e:
        del registry[artifact_id]
        save_registry(registry_path, registry)
        return jsonify({"error": f"Failed to rate model: {e}"}), 424
    
    return jsonify(entry), 201