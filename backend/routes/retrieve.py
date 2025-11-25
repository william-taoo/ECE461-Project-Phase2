from flask import Blueprint, request, jsonify, current_app
from utils.registry_utils import load_registry, add_to_audit, get_audit_entries
from collections import OrderedDict
import re
import fnmatch
import os
import json


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
    
    # Request
    try:
        query = request.get_json(force=True, silent=True)
        print(query)
        # handle single-element list (autograder format)
        if isinstance(query, list) and len(query) == 1:
            query = query[0]
        if not query or not isinstance(query, dict):
            return jsonify({"error": "Invalid request format"}), 400
    except Exception:
        return jsonify({"error": "Invalid request"}), 400
    
    # Query parameters
    name_query = query.get("name", "*").strip()
    type_query = query.get("type", "all").strip().lower()
    version_query = query.get("version", "").strip()
    
    offset = int(request.args.get("offset", 0))
    page_size = 10

    results = []
    for artifact in registry.values():
        meta = artifact.get("metadata", {})
        name = meta.get("name", "")
        a_type = meta.get("type", "").lower()
        version = meta.get("version", "")

        if name_query != "*" and name_query.lower() != name.lower():
            continue

        if type_query != "all" and a_type != type_query:
            continue

        if version_query:
            if "*" in version_query:
                if not fnmatch.fnmatch(version, version_query):
                    continue
            elif version_query != version:
                continue

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
    """
    Return metadata for all artifacts matching the given name
    in the flat format expected by the API.
    """
    if not name or not name.strip():
        return jsonify({"error": "Missing or invalid artifact name"}), 400

    registry_path = current_app.config["REGISTRY_PATH"]
    registry = load_registry(registry_path)

    results = []
    for artifact in registry.values():
        metadata = artifact.get("metadata", {})
        if metadata.get("name", "").lower() == name.lower():
            results.append(artifact["metadata"])

    if not results:
        return jsonify({"error": "No artifacts found"}), 404

    return jsonify(results), 200


@retrieve_bp.route("/artifacts/<artifact_type>/<id>", methods=["GET"])
def get_artifact(artifact_type: str, id: str):
    '''
    Retrieve artifact metadata by type and id
    '''
    registry_path = current_app.config["REGISTRY_PATH"]
    registry = load_registry(registry_path)
    artifact = registry.get(id)
    print(artifact)
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
    if not artifact_type or not id:
        return jsonify({"error": "Missing field(s)"}), 400
    
    registry_path = current_app.config["REGISTRY_PATH"]
    registry = load_registry(registry_path)
    artifact = registry.get(id)
    if not artifact:
        return jsonify({"error": "Artifact not found"}), 404
    
    # Add to audit
    name = "Name" # Change this later
    admin = False # Change this later
    artifact_name = artifact["metadata"]["name"]
    add_to_audit(name, admin, artifact_type, id, artifact_name, "AUDIT") 
    
    # Get audit log 
    audit = get_audit_entries(id)
    if audit == None:
        return jsonify({"error": "Error with audit log"}), 400
    else:
        return jsonify(audit), 200

@retrieve_bp.route("/artifact/model/<id>/lineage", methods=["GET"])
def get_lineage(id: str):
    '''
    Get the lineage graph of an artifact
    '''
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
