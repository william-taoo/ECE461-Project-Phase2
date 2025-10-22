from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import uuid

# Initialize Flask app
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "registry.json")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/upload", methods=["POST"])
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

    # Save file
    model_id = f"{name}-{uuid.uuid4().hex[:8]}"
    file_path = os.path.join(UPLOAD_FOLDER, f"{model_id}.zip")
    file.save(file_path)

    # Update registry
    # registry = load_registry() <- implement (can be like a list)
    # registry.append({
    #     "id": model_id,
    #     "name": name,
    #     "path": file_path,
    #     "scores": {}
    #     })
    # save_registry(registry) <- implement

    return jsonify({
        "message": "Model uploaded successfully",
        "model_id": model_id
    }), 201

@app.route("/rate/<model_id>", methods=["GET"])
def rate_model(model_id):
    '''
    Rate the model and return the net and sub scores
    from phase 1
    Also includes new metrics
    - Reproducibility: Whether model can be run using only 
    the demonstrated code in model card
    - Reviewedness: The fraction of all code in repo that was 
    introduced by pull requests with a code review
    - Treescore: Average of the total model scores of all parents
    of the model
    '''
    # registry = load_registry()
    # Get model and rate using phase 1 metrics

    # Save scores to registry

@app.route("/download/<model_id>", methods=["GET"])
def download_model(model_id):
    '''
    Download a zipped model from the registry
    Can be downloaded with these options:
    - Full model package,
    - Sub aspects: weights, associated datasets, etc.
    '''
    