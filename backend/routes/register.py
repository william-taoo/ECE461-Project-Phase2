from flask import Blueprint, request, jsonify, current_app
import os
import uuid
import requests
from utils.registry_utils import (
    load_registry,
    save_registry,
    infer_artifact_type,
    add_to_audit,
)

from routes.download import (
    extract_hf_repo_id,
    stream_zip_of_hf_repo,
    upload_zip_stream_to_s3,
    make_presigned_url,
)

import zipstream
import boto3
from huggingface_hub import HfApi, hf_hub_url
from urllib.parse import urlparse
from utils.artifact_size import get_artifact_size
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client("s3", region_name="us-east-2")
S3_BUCKET = "461-phase2-team12"


def s3_object_exists(bucket: str, key: str) -> bool:
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except s3.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise


register_bp = Blueprint("artifact", __name__)
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
ENV = os.getenv("ENVIRONMENT", "local")


@register_bp.route("/artifact/<artifact_type>", methods=["POST"])
def register_artifact(artifact_type: str):
    """
    Register artifact into registry
    Parameters:
        artifact_type: Type of url: model, dataset, code
    """

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
            return (
                jsonify(
                    {
                        "error": f"URL looks like {detected}, not {artifact_type}"
                    }
                ),
                400,
            )
    except ValueError:
        pass

    for entry in (
        registry.values() if isinstance(registry, dict) else registry
    ):
        if entry.get("data", {}).get("url") == url:
            return (
                jsonify({"error": "Artifact with this URL already exists"}),
                409,
            )

    total_size = get_artifact_size(url, artifact_type)

    try:
        total_size = get_artifact_size(url, artifact_type)
    except Exception as e:
        current_app.logger.warning(
            "Failed to compute artifact size for %s: %s", url, e
        )
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

    # temporarily save
    if isinstance(registry, dict):
        registry[artifact_id] = entry
    else:
        registry.append(entry)

    if ENV == "local":
        save_registry(registry_path, registry)
    else:
        save_registry(data=registry)

    # rate the artifact
    if artifact_type == "model":
        base = request.host_url.rstrip("/")
        rate_url = f"{base}/artifact/model/{artifact_id}/rate"
        try:
            response = requests.get(rate_url)
            if response.status_code != 200:
                del registry[artifact_id]
                if ENV == "local":
                    save_registry(registry_path, registry)
                else:
                    save_registry(data=registry)
                return (
                    jsonify(
                        {"error": f"Failed to rate model: {response.text}"}
                    ),
                    424,
                )

            rating = response.json()
            net_score = rating.get("net_score", 0.0)

            # COME BACK AND SET SCORE THRESHOLD. NEED TO FIX RATING LOGIC IN MODEL.PY
            # TO HANDLE DIFFERENT HF URL FORMATS
            if net_score < -1:
                # reject artifact
                del registry[artifact_id]
                if ENV == "local":
                    save_registry(registry_path, registry)
                else:
                    save_registry(data=registry)
                return (
                    jsonify(
                        {
                            "error": f"Model rejected. Score too low: ({net_score}). Upload failed."
                        }
                    ),
                    424,
                )

            # save rating in artifact entry
            final_entry = {
                "metadata": {
                    "id": artifact_id,
                    "name": artifact_name,
                    "version": body.get("version") or "0.0.1",
                    "type": artifact_type,
                    "rating": rating,
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
        # create stable S3 key 
        if artifact_type == "model" and "huggingface.co" in url:
            repo_id = extract_hf_repo_id(url)
            if not repo_id:
                return jsonify({"error": "Invalid HuggingFace URL"}), 400
            safe_name = repo_id.replace("/", "_")
            s3_key = f"artifacts/models/{safe_name}.zip"
        else:
            # For code/dataset, use artifact_name
            safe_name = artifact_name.replace("/", "_")
            s3_key = f"artifacts/{artifact_type}/{safe_name}.zip"

        # check if zip already exists in S3
        if s3_object_exists(S3_BUCKET, s3_key):
            current_app.logger.info(
                f"S3 object already exists, skipping upload: {s3_key}"
            )

            presigned_url = make_presigned_url(s3_key)
            entry["data"]["download_url"] = presigned_url
            entry["data"]["s3_key"] = s3_key

        else:
            try:
                # # Hugging Face model — download ONLY weights
                # if artifact_type == "model" and "huggingface.co" in url:
                #     repo_id = extract_hf_repo_id(url)
                #     if not repo_id:
                #         raise Exception("Invalid HuggingFace URL")

                #     # download ONLY the weight files
                #     zip_stream = stream_zip_of_hf_repo(repo_id, component="weights")

                #     upload_zip_stream_to_s3(zip_stream, s3_key)

                # # Code or dataset -> upload a real placeholder zip
                # else:
                #     z_real = zipstream.ZipFile(
                #         mode="w", compression=zipstream.ZIP_DEFLATED
                #     )
                #     z_real.write_iter(
                #         "real_placeholder.txt", iter([b"real content"])
                #     )
                #     upload_zip_stream_to_s3(z_real, s3_key)

                z_real = zipstream.ZipFile(
                        mode="w", compression=zipstream.ZIP_DEFLATED)
                z_real.write_iter(
                        "real_placeholder.txt", iter([b"real content"]))
                upload_zip_stream_to_s3(z_real, s3_key)

            except Exception as zip_err:
                # fallback empty ZIP
                current_app.logger.warning(
                    f"Real ZIP failed, falling back to empty ZIP: {zip_err}"
                )

                z_empty = zipstream.ZipFile(
                    mode="w", compression=zipstream.ZIP_DEFLATED
                )
                z_empty.write_iter("placeholder.txt", iter([b""]))
                upload_zip_stream_to_s3(z_empty, s3_key)

            # after successful upload (real or empty), generate S3 URL
            presigned_url = make_presigned_url(s3_key)
            entry["data"]["download_url"] = presigned_url
            entry["data"]["s3_key"] = s3_key

        # update registry
        if isinstance(registry, dict):
            registry[artifact_id] = entry
        else:
            registry.append(entry)

        if ENV == "local":
            save_registry(registry_path, registry)
        else:
            save_registry(data=registry)

    except Exception as e:
        return jsonify({
            "error": "Failed to download and package artifact",
            "details": str(e),
        }), 500

    # # Add to audit
    # name = "Name" # Change this later
    # admin = False # Change this later
    # add_to_audit(name, admin, artifact_type, artifact_id, artifact_name, "CREATE")

    return jsonify(entry), 201
