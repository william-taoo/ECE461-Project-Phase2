from flask import Blueprint, jsonify, request, send_file, current_app
import os
from utils.registry_utils import (
    load_registry,
    find_model_in_registry,
    add_to_audit
)


download_bp = Blueprint("download", __name__)
ENV = os.getenv("ENVIRONMENT", "local")

@download_bp.route("/download/<model_id>", methods=["GET"])
def download_model(model_id):
    '''
    Download a zipped model from the registry
    Can be downloaded with these options:
    - Full model package,
    - Sub aspects: weights, associated datasets, etc.
    We will get a component param, specifying what to download
    '''
    if ENV == "local":
        registry_path = current_app.config["REGISTRY_PATH"]
        registry = load_registry(registry_path)
    else:
        registry = load_registry()

    # Check if model is in registry
    model = find_model_in_registry(registry, model_id)
    if not model:
        return jsonify({"error": "Model not found"}), 404
    
    component = request.args.get("component", "full")
    file_path = model["path"]
    if not os.path.exists(file_path):
        return jsonify({"error": "Model file not found"}), 404
    
    # Add to audit
    name = "Name" # Change this later
    admin = False # Change this later
    artifact_name = model["metadata"]["name"]
    add_to_audit(name, admin, "model", model_id, artifact_name, "DOWNLOAD")
    
    return send_file(file_path, as_attachment=True)
