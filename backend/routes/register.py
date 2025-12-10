from flask import Blueprint, request, jsonify, current_app
import os
import uuid
import requests
from utils.registry_utils import load_registry, save_registry, infer_artifact_type, add_to_audit

from routes.download import (
    extract_hf_repo_id,
    stream_zip_of_hf_repo,
    upload_zip_stream_to_s3,
    make_presigned_url,
)

import zipstream
from huggingface_hub import HfApi
from urllib.parse import urlparse
from utils.artifact_size import get_artifact_size
from dotenv import load_dotenv
load_dotenv()


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

    registry_path = None
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

    try:
        total_size = get_artifact_size(url, artifact_type)
    except Exception as e:
        current_app.logger.warning("Failed to compute artifact size for %s: %s", url, e)
    total_size = 0

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
        save_registry(data=registry)

    # Rate the artifact
    if artifact_type == "model":
        base = request.host_url.rstrip('/')
        rate_url = f"{base}/artifact/model/{artifact_id}/rate"
        try:
            response = requests.get(rate_url)
            if response.status_code != 200:
                del registry[artifact_id]
                if ENV == "local":
                    save_registry(registry_path, registry)
                else:
                    save_registry(data=registry)
                return jsonify({"error": f"Failed to rate model: {response.text}"}), 424
            
            rating = response.json()
            net_score = rating.get("net_score", 0.0)

            # COME BACK AND SET SCORE THRESHOLD. NEED TO FIX RATING LOGIC IN MODEL.PY
            # TO HANDLE DIFFERENT HF URL FORMATS
            if net_score < -1:
                # Reject artifact
                del registry[artifact_id]
                if ENV == "local":
                    save_registry(registry_path, registry)
                else:
                    save_registry(data=registry)
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
                save_registry(data=registry)
        except Exception as e:
            del registry[artifact_id]

            if ENV == "local":
                save_registry(registry_path, registry)
            else:
                save_registry(data=registry)
                
            return jsonify({"error": f"Failed to rate model: {e}"}), 424
    
    # download the artifact
    try:
        # S3 key for all artifact types
        safe_name = artifact_name.replace("/", "_")
        s3_key = f"artifacts/{artifact_type}/{artifact_id}/{safe_name}.zip"

        # # CASE 1: Models from Hugging Face -> real download
        # if artifact_type == "model" and "huggingface.co" in url:
        #     repo_id = extract_hf_repo_id(url)
        #     if not repo_id:
        #         return jsonify({"error": "Invalid HuggingFace URL"}), 400

        #     # build ZIP of full model from HF
        #     zip_stream = stream_zip_of_hf_repo(repo_id, component=None)

        #     # upload to S3
        #     upload_zip_stream_to_s3(zip_stream, s3_key)

        # # CASE 2: Everything else -> empty ZIP placeholder
        # else:
        #     z = zipstream.ZipFile(mode="w", compression=zipstream.ZIP_DEFLATED)
            
        #     # add empty placeholder file inside ZIP
        #     z.write_iter("placeholder.txt", iter([b""]))

        #     # Upload empty ZIP
        #     upload_zip_stream_to_s3(z, s3_key)

        # TEMPORARY: Always upload an empty ZIP file for all artifact types
        z = zipstream.ZipFile(mode="w", compression=zipstream.ZIP_DEFLATED)
        z.write_iter("placeholder.txt", iter([b""]))
        upload_zip_stream_to_s3(z, s3_key)

        # generate presigned URL
        presigned_url = make_presigned_url(s3_key)

        # save S3 metadata inside registry entry
        entry["data"]["download_url"] = presigned_url
        entry["data"]["s3_key"] = s3_key

        # update registry entry
        if isinstance(registry, dict):
            registry[artifact_id] = entry
        else:
            registry.append(entry)

        # save registry
        if ENV == "local":
            save_registry(registry_path, registry)
        else:
            save_registry(data=registry)

    except Exception as e:
        return jsonify({
            "error": "Failed to download and package artifact",
            "details": str(e)
        }), 500

    # # Add to audit
    # name = "Name" # Change this later
    # admin = False # Change this later
    # add_to_audit(name, admin, artifact_type, artifact_id, artifact_name, "CREATE") 
    
    return jsonify(entry), 201