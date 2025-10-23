from flask import Blueprint, jsonify, request, send_file
import os
from utils.registry_utils import (
    load_registry,
    find_model_in_registry
)
from backend.app import REGISTRY_PATH

download_bp = Blueprint("download", __name__)

@download_bp.route("/download/<model_id>", methods=["GET"])
def download_model(model_id):
    '''
    Download a zipped model from the registry
    Can be downloaded with these options:
    - Full model package,
    - Sub aspects: weights, associated datasets, etc.
    We will get a component param, specifying what to download
    '''
    registry = load_registry(REGISTRY_PATH)

    # Check if model is in registry
    model = find_model_in_registry(registry, model_id)
    if not model:
        return jsonify({"error": "Model not found"}), 404
    
    component = request.args.get("component", "full")
    file_path = model["path"]
    if not os.path.exists(file_path):
        return jsonify({"error": "Model file not found"}), 404
    
    return send_file(file_path, as_attachment=True)
