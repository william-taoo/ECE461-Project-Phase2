from flask import Blueprint, request, jsonify, current_app
from utils.registry_utils import load_registry, save_registry


remove_bp = Blueprint("remove", __name__)

@remove_bp.route("/reset", methods=["DELETE"])
def reset_registry():
    '''
    Reset registry to default system state
    Delete all artifacts
    '''
    # Check authorization
    auth_header = request.headers.get("X-Authorization")
    if not auth_header:
        return jsonify({"error": "Missing authentication header"}), 403
    
    # Check permissions - fill in admin-token 
    if auth_header != "admin-token":
        return jsonify({
            "error": "You don't have permission to reset the registry"
        }), 401

    default = {} # Can change to whatever default
    registry_path = current_app.config["REGISTRY_PATH"]
    save_registry(registry_path, default)
   
    return jsonify({"message": "Registry has been reset"}), 200

@remove_bp.route("/artifacts/<artifact_id>/<id>", methods=["DELETE"])
def delete_artifact(artifact_type: str, id: str):
    '''
    Delete an artifact given an id that matches 
    '''
    # Check authorization
    auth_header = request.headers.get("X-Authorization")
    if not auth_header:
        return jsonify({"error": "Missing authentication header"}), 403
    
    if artifact_type == None or id == None:
        return jsonify({"error": "Missing field(s)"}), 400
    
    registry_path = current_app.config["REGISTRY_PATH"]
    registry = load_registry(registry_path)
    artifact = registry.get(id)
    if not artifact:
        return jsonify({"error": "Artifact not found"}), 404
    
    del registry[id]
    save_registry(registry_path, registry)

    return jsonify({"message": "Artifact has been deleted"}), 200
