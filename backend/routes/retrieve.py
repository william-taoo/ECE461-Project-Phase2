from flask import Blueprint, request, jsonify, current_app
from utils.registry_utils import load_registry
import re


retrieve_bp = Blueprint("retrieve", __name__)

@retrieve_bp.route("/artifacts", methods=["POST"])
def get_artifacts():
    '''
    This will send a request for models in the registry 
    given a name and type
    '''

    # Access to config for registry path
    registry_path = current_app.config["REGISTRY_PATH"]
    registry = load_registry(registry_path)

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
            if (name == "*" or artifact["metadata"]["name"] == name) and \
                (not artifact_type or artifact["metadata"]["type"] == artifact_type):
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

    registry_path = current_app.config["REGISTRY_PATH"]
    registry = load_registry(registry_path)
    results = []

    for artifact in registry.values():
        artifact_name = artifact.get("metadata", {}).get("name", "")
        if name.lower() == artifact_name.lower():
            results.append(artifact["metadata"])
    
    # If no results
    if len(results) == 0:
        return jsonify({"error": "No artifacts found"}), 404
    
    return jsonify(results), 200

@retrieve_bp.route("/artifacts/<artifact_type>/<id>", methods=["GET"])
def get_artifact(artifact_type: str, id: str):
    '''
    Retrieve artifact metadata by type and id
    '''
    # Check authorization
    auth_header = request.headers.get("X-Authorization")
    if not auth_header:
        return jsonify({"error": "Missing authentication header"}), 403
    
    registry_path = current_app.config["REGISTRY_PATH"]
    registry = load_registry(registry_path)
    artifact = registry.get(id)
    if not artifact:
        return jsonify({"error": "Artifact not found"}), 404
    
    if artifact["metadata"]["type"] != artifact_type:
        return jsonify({"error": "Invalid artifact type"}), 400
    
    return jsonify(artifact), 200

@retrieve_bp.route("/artifact/<artifact_type>/<id>/cost", methods=["GET"])
def get_cost(artifact_type: str, id: str):
    '''
    Retrieve artifact cost by type and id
    '''
    dependency = request.args.get("dependency", "false").lower() == "true"

    # Check authorization
    auth_header = request.headers.get("X-Authorization")
    if not auth_header:
        return jsonify({"error": "Missing authentication header"}), 403
    
    if not artifact_type or not id:
        return jsonify({"error": "Missing field(s)"}), 400
    
    registry_path = current_app.config["REGISTRY_PATH"]
    registry = load_registry(registry_path)
    artifact = registry.get(id)
    if not artifact:
        return jsonify({"error": "Artifact not found"}), 404
    
    try:
        if dependency == False:
            # Return total cost
            cost = 0 # Call function to get cost of artifact
            return jsonify({
                id: {
                    "total_cost": cost
                }
            }), 200
        else:
            # Return standalone and total cost
            results = {}
            standalone_cost, total_cost = 0, 0 # Call function to get costs
            # Might need to iterate through and calculate cost
            return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": "Error with calculating cost"}), 500

@retrieve_bp.route("/artifact/<artifact_type>/<id>/audit", methods=["GET"])
def get_audit(artifact_type: str, id: str):
    '''
    Get the audit log for an artifact
    '''
    auth_header = request.headers.get("X-Authorization")
    if not auth_header:
        return jsonify({"error": "Missing authentication header"}), 403
    
    if not artifact_type or not id:
        return jsonify({"error": "Missing field(s)"}), 400
    
    registry_path = current_app.config["REGISTRY_PATH"]
    registry = load_registry(registry_path)
    artifact = registry.get(id)
    if not artifact:
        return jsonify({"error": "Artifact not found"}), 404
    
    # Get audit log 
    # - go in audit and retrieve id
    audits = []

    return jsonify(audits), 200

@retrieve_bp.route("/artifact/model/<id>/lineage", methods=["GET"])
def get_lineage(id: str):
    '''
    Get the lineage graph of an artifact
    '''
    auth_header = request.headers.get("X-Authorization")
    if not auth_header:
        return jsonify({"error": "Missing authentication header"}), 403
    
    if not id:
        return jsonify({"error": "Missing field"}), 400
    
    registry_path = current_app.config["REGISTRY_PATH"]
    registry = load_registry(registry_path)
    artifact = registry.get(id)
    if not artifact:
        return jsonify({"error": "Artifact not found"}), 404
    
    # Get lineage graph
    lineage = {}

    return jsonify(lineage), 200

@retrieve_bp.route("/artifact/model/<id>/license-check", methods=["POST"])
def check_license(id: str):
    '''
    Check if the license is compatible
    '''
    auth_header = request.headers.get("X-Authorization")
    if not auth_header:
        return jsonify({"error": "Missing authentication header"}), 403
    
    data = request.get_json()
    if not data or "github_url" not in data:
        return jsonify({"error": "Missing github_url"}), 400
    
    url = data["github_url"]
    valid_url = True
    if not valid_url:
        return jsonify({"error": "Invalid github URL"}), 404
    
    # Check license
    try:
        compatible = True
    except:
        return jsonify({"error": "License information couldn't be retrieved"}), 502


    return jsonify(compatible), 200

@retrieve_bp.route("/artifact/byRegEx", methods=["POST"])
def get_by_regex():
    '''
    Retrieve artifacts matching name regex
    '''
    auth_header = request.headers.get("X-Authorization")
    if not auth_header:
        return jsonify({"error": "Missing authentication header"}), 403
    
    regex = request.get_json()
    if not regex or "regex" not in regex:
        return jsonify({"error": "Missing regex"}), 400
    
    try:
        compiled_regex = re.compile(regex, re.IGNORECASE)
    except re.error:
        return jsonify({"error": "Invalid regular expression"}), 400
    
    registry_path = current_app.config["REGISTRY_PATH"]
    registry = load_registry(registry_path)

    matches = []
    for artifact_id, artifact_data in registry.items():
        metadata = artifact_data.get("metadata", {})
        name = metadata.get("name", "")
        artifact_type = metadata.get("type", "")

        if compiled_regex.search(name):
            matches.append({
                "name": name,
                "id": artifact_id,
                "type": artifact_type
            }) 

    if not matches:
        return jsonify({"error": "No artifacts found"}), 404
    
    return jsonify(matches), 200
