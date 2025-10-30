from flask import Blueprint, request, jsonify
import os
import uuid
import requests
from utils.registry_utils import load_registry, save_registry
from backend.app import REGISTRY_PATH

retrieve_bp = Blueprint("retrieve", __name__)

@retrieve_bp.route("/artifact", methods=["POST"])
def get_artifacts():
    '''
    This will send a request for models in the registry 
    given a name and type
    '''
    registry = load_registry(REGISTRY_PATH)

    # Header
    auth_header = request.headers.get("X-Authorization")
    if not auth_header:
        return jsonify({"error": "Missing authentication header"}), 403
    
    # Request
    try:
        queries = request.get_json()
        if not isinstance(queries, list):
            raise ValueError
    except Exception:
        return jsonify({"error": "Invalid request"})
    
    # Query parameters
    offset = int(request.args.get("offset", 0))
    page_size = 1

    results = []
    for query in queries:
        name = query.get("name")
        artifact_type = query.get("type")
        for artifact in registry.values():
            if (name == "*" or artifact["name"] == name) and \
                (not artifact_type or artifact["type"] == artifact_type):
                results.append(artifact)

    # Handle too many artifacts
    if len(results) > 100:
        return jsonify({"error": "Too many artifacts returned"}), 413

    # Pagination
    paginated = results[offset:offset + page_size]
    next_offset = offset + len(paginated)

    response = jsonify(paginated)
    response.headers["offset"] = str(next_offset)

    return response, 200

@retrieve_bp.route("/artifact/byName/<name>", methods=["GET"])
def get_name(name: str):
    '''
    Return the metadata of the artifacts that match the
    provided name
    '''
    # Check authorization
    auth_header = request.headers.get("X-Authorization")
    if not auth_header:
        return jsonify({"error": "Missing authentication header"}), 403
    
    # Check if name is valid
    if not name or name.strip() == "":
        return jsonify({"error": "Missing or invalid artifact name"}), 400

    registry = load_registry(REGISTRY_PATH)
    results = []

    for artifact in registry.values():
        artifact_name = artifact.get("metadata", {}).get("name", "")
        if name.lower() == artifact_name.lower():
            results.append(artifact["metadata"])
    
    # If no results
    if len(results) == 0:
        return jsonify({"error": "No artifacts found"}), 404
    
    return jsonify(results), 200