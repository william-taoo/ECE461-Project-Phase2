from flask import Blueprint, request, jsonify, current_app
import os
import uuid
import requests
from utils.registry_utils import load_registry, save_registry, infer_artifact_type, add_to_audit
from huggingface_hub import HfApi
from urllib.parse import urlparse
from utils.artifact_size import get_artifact_size

register_bp = Blueprint("artifact", __name__)
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
ENV = os.getenv("ENVIRONMENT", "local")

@register_bp.route("/artifact/<artifact_type>", methods=["POST"])
def register_artifact(artifact_type: str):
    '''
    Register artifact into registry
    Parameters:
        artifact_type: Type of url: model, dataset, code
    '''
    if artifact_type not in ("model", "dataset", "code"):
        return jsonify({"error": "invalid artifact_type"}), 400

    if ENV == "local":
        registry_path = current_app.config["REGISTRY_PATH"]
        registry = load_registry(registry_path)
    else:
        registry = load_registry()

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
        
    total_size = get_artifact_size(url, artifact_type)

    if total_size > 5 * 1024**3:
        return jsonify({"error": "Artifact is too large"}), 424

    artifact_id = uuid.uuid4().hex
    artifact_name = body.get("name") or os.path.basename(url) or "unnamed"
    entry = {
        "metadata": {
            "id": artifact_id,
            "name": artifact_name,
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

    if ENV == "local":
        save_registry(registry_path, registry)
    else:
        save_registry(registry)

    # Rate the artifact
    if artifact_type == "model":
        base = request.host_url.rstrip('/')
        rate_url = f"{base}/artifact/model/{artifact_id}/rate"
        try:
            response = requests.get(rate_url)
            if response.status_code != 200:
                del registry[artifact_id]
                save_registry(registry)
                return jsonify({"error": f"Failed to rate model: {response.text}"}), 424
            
            rating = response.json()
            net_score = rating.get("net_score", 0.0)

            # COME BACK AND SET SCORE THRESHOLD. NEED TO FIX RATING LOGIC IN MODEL.PY
            # TO HANDLE DIFFERENT HF URL FORMATS
            if net_score < -1:
                # Reject artifact
                del registry[artifact_id]
                save_registry(registry)
                return jsonify({"error": f"Model rejected. Score too low: ({net_score}). Upload failed."}), 424
            
            # Save rating in artifact entry
            final_entry = {
                "metadata": {
                    "id": artifact_id,
                    "name": artifact_name,
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

            if ENV == "local":
                save_registry(registry_path, registry)
            else:
                save_registry(registry)
        except Exception as e:
            del registry[artifact_id]

            if ENV == "local":
                save_registry(registry_path, registry)
            else:
                save_registry(registry)
                
            return jsonify({"error": f"Failed to rate model: {e}"}), 424
    
    # # Add to audit
    # name = "Name" # Change this later
    # admin = False # Change this later
    # add_to_audit(name, admin, artifact_type, artifact_id, artifact_name, "CREATE") 
    
    return jsonify(entry), 201