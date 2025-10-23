from flask import Blueprint, request, jsonify
import os, uuid
from utils.registry_utils import load_registry, save_registry
from backend.app import REGISTRY_PATH

upload_bp = Blueprint("upload", __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")

@upload_bp.route("/upload", methods=["POST"])
def upload_model():
    '''
    Upload a model as a zipped file and register it
    Expected form data:
    - file: .zip file
    - name: model name
    *Might be more*
    '''
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    name = request.form.get("name")
    
    if not name:
        return jsonify({"error": "Model name is required"}), 400

    # Save file locally
    model_id = f"{name}-{uuid.uuid4().hex[:8]}"
    file_path = os.path.join(UPLOAD_FOLDER, f"{model_id}.zip")
    file.save(file_path)

    # Update registry
    registry = load_registry(REGISTRY_PATH)
    registry.append({
        "id": model_id,
        "name": name,
        "path": file_path,
        "scores": {}
        })
    save_registry(REGISTRY_PATH, registry)

    return jsonify({
        "message": "Model uploaded successfully",
        "model_id": model_id
    }), 201
