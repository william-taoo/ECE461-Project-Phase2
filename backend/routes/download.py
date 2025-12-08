from flask import Blueprint, jsonify, request, send_file, current_app
import os
import tempfile
import zipfile
import shutil
from urllib.parse import urlparse
from huggingface_hub import snapshot_download
from typing import Optional
from utils.registry_utils import (
    load_registry,
    find_model_in_registry,
    add_to_audit
)
from dotenv import load_dotenv
load_dotenv()

download_bp = Blueprint("download", __name__)
ENV = os.getenv("ENVIRONMENT", "local")


def extract_hf_repo_id(url: str) -> Optional[str]:
    """
    Convert a HuggingFace URL into a repo ID.
    Example:
        https://huggingface.co/WinKawaks/vit-tiny-patch16-224
        --->
        WinKawaks/vit-tiny-patch16-224
    """
    
    try:
        path = urlparse(url).path.strip("/")
        parts = path.split("/")

        if len(parts) < 2:
            return None

        return "/".join(parts[:2])

    except Exception:
        return None


@download_bp.route("/download/<model_id>", methods=["GET"])
def download_model(model_id):
    '''
    Download a zipped model from the registry.

    Can be downloaded with these options:
        - Full model package,
        - Sub aspects: weights, associated datasets, etc.
    
    We will get a component param, specifying what to download.
    '''

    # load registry
    if ENV == "local":
        registry_path = current_app.config["REGISTRY_PATH"]
        registry = load_registry(registry_path)
    else:
        registry = load_registry()

    # check if model is in registry
    model = find_model_in_registry(registry, model_id)
    if not model:
        return jsonify({"error": "Model not found"}), 404
    
    # determine download source
    hf_url = model.get("data", {}).get("url")
    local_path = model.get("path")
    
    # add to audit
    name = "Name" # Change this later
    admin = False # Change this later
    artifact_name = model["metadata"]["name"]
    add_to_audit(name, admin, "model", model_id, artifact_name, "DOWNLOAD")

    # create temp directory
    temp_dir = tempfile.mkdtemp()

    try:
        # CASE 1: hugging face url
        if hf_url and "huggingface.co" in hf_url:
            repo_id = extract_hf_repo_id(hf_url)
            if not repo_id:
                return jsonify({"error": "Invalid HuggingFace URL"}), 400

            # download with HuggingFace Hub
            repo_dir = snapshot_download(
                repo_id=repo_id,
                local_dir=temp_dir,
                local_dir_use_symlinks=False,
            )
            source_dir = repo_dir

        # CASE 2: local path
        elif local_path and os.path.exists(local_path):
            source_dir = local_path

        else:
            return jsonify({"error": "Model source not found"}), 404

        # zip model
        zip_name = f"{artifact_name.replace('/', '_')}.zip"
        zip_path = os.path.join(temp_dir, zip_name)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, source_dir)
                    zipf.write(full_path, rel_path)

        return send_file(
            zip_path,
            mimetype="application/zip",
            as_attachment=True,
            download_name=zip_name
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
