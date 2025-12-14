from flask import Blueprint, request, jsonify, current_app
from utils.registry_utils import load_registry, add_to_audit, get_audit_entries
from utils.lineage_utils import build_lineage_graph
from typing import Any, Optional, Set
import re
import fnmatch
import typing
import os
from dotenv import load_dotenv
load_dotenv()


retrieve_bp = Blueprint("retrieve", __name__)
ENV = os.getenv("ENVIRONMENT", "local")


def serialize_artifact(artifact_id: str, artifact: dict) -> dict:
    """
    Return a normalized artifact dict.
    """
    # get artifact metadata
    metadata = artifact.get("metadata", {}) if isinstance(artifact, dict) else {}
    
    # if metadata has id, prefer the dictionary key (artifact_id) as canonical id.
    return {
        "name": metadata.get("name", "") if isinstance(metadata, dict) else "",
        "id": str(artifact_id),
        "type": metadata.get("type", "") if isinstance(metadata, dict) else "",
        "version": metadata.get("version", "") if isinstance(metadata, dict) else "",
        
        # keep original metadata object (empty dict if missing)
        "metadata": metadata if isinstance(metadata, dict) else {}
    }


@retrieve_bp.route("/artifacts", methods=["POST"], strict_slashes=False)
def get_artifacts():
    """
    This will send a request for models in the registry 
    given a name and type
    """
    # get path to registry
    if ENV == "local":
        registry_path = current_app.config.get("REGISTRY_PATH")
        assert registry_path is not None
        registry = load_registry(registry_path)
    else:
        registry = load_registry()

    # parse JSON safely (handle single element list) 
    query = request.get_json(force=True, silent=True)
    if isinstance(query, dict):
        queries = [query]
    elif isinstance(query, list):
        queries = query
    else:
        return jsonify({"error": "Invalid request format"}), 400

    if not queries or any(not isinstance(q, dict) for q in queries):
        return jsonify({"error": "Invalid request format"}), 400

    allowed_types = {"model", "dataset", "code"}
    def normalize_types(raw: Any) -> Optional[Set[str]]:
        if raw is None:
            return None
        if isinstance(raw, str):
            t = raw.strip().lower()
            if t in ("", "all", "*"):
                return None
            if t not in allowed_types:
                raise ValueError("Invalid type")
            return {t}
        if isinstance(raw, list):
            s = {str(x).strip().lower() for x in raw if str(x).strip()}
            if not s or "all" in s or "*" in s:
                return None
            if any(t not in allowed_types for t in s):
                raise ValueError("Invalid type")
            return s

        raise ValueError("Invalid types")
    
    norm_queries = []
    for q in queries:
        name_q = q.get("name")
        if not isinstance(name_q, str) or not name_q.strip():
            return jsonify({"error": "Missing or invalid name"}), 400
        name_q = name_q.strip()

        try:
            types_set = normalize_types(q.get("types", None))
        except ValueError:
            return jsonify({"error": "Invalid types"}), 400

        norm_queries.append((name_q, types_set))

    try:
        offset = int(request.args.get("offset", 0))
    except Exception:
        offset = 0
    if offset < 0:
        offset = 0
    page_size = 10

    results = []
    seen_ids = set()

    for artifact_id, artifact in registry.items():
        meta = artifact.get("metadata", {}) if isinstance(artifact, dict) else {}
        a_name = str(meta.get("name", "")).strip() if isinstance(meta, dict) else ""
        a_type = str(meta.get("type", "")).strip().lower() if isinstance(meta, dict) else ""

        matched = False
        for (name_q, types_set) in norm_queries:
            if name_q != "*" and a_name.lower() != name_q.lower():
                continue

            if types_set is not None and a_type not in types_set:
                continue

            matched = True
            break

        if not matched:
            continue

        if artifact_id not in seen_ids:
            results.append(serialize_artifact(artifact_id, artifact))
            seen_ids.add(artifact_id)

    if len(results) > 100:
        return jsonify({"error": "Too many artifacts returned"}), 413

    paginated = results[offset: offset + page_size]
    next_offset = offset + len(paginated)

    resp = jsonify(paginated)
    resp.headers["offset"] = str(next_offset)
    return resp, 200

@retrieve_bp.route("/artifact/byName/<name>", methods=["GET"], strict_slashes=False)
def get_name(name: str):
    """
    Return metadata for all artifacts matching the provided name.
    Returns a list of serialized artifacts.
    """
    # handle missing artifact name
    if not name or not name.strip():
        return jsonify({"error": "Missing or invalid artifact name"}), 400

    # get path to registry
    if ENV == "local":
        registry_path = current_app.config.get("REGISTRY_PATH")
        assert registry_path is not None
        registry = load_registry(registry_path)
    else:
        registry = load_registry()

    results = []
    query = name.strip().lower()

    # append artifacts that match the name query
    for artifact_id, artifact in registry.items():
        metadata = artifact.get("metadata", {}) if isinstance(artifact, dict) else {}
        artifact_name = str(metadata.get("name", "")).strip().lower() if isinstance(metadata, dict) else ""
        if artifact_name == query:
            results.append(serialize_artifact(artifact_id, artifact))

    # handle no results
    if not results:
        return jsonify({"error": "No artifacts found"}), 404

    return jsonify(results), 200


@retrieve_bp.route("/artifacts/<artifact_type>/<id>", methods=["GET"], strict_slashes=False)
def get_artifact(artifact_type: str, id: str):
    """
    Retrieve the full stored artifact entry by id. We return the raw artifact object
    but ensure it includes id/name/type/version/metadata via serialization.
    """
    # get path to registry
    if ENV == "local":
        registry_path = current_app.config.get("REGISTRY_PATH")
        assert registry_path is not None
        registry = load_registry(registry_path)
    else:
        registry = load_registry()

    # get artifact by id
    artifact = registry.get(id)
    if not artifact:
        return jsonify({"error": "Artifact not found"}), 404

    # type check
    meta_type = artifact.get("metadata", {}).get("type", "") if isinstance(artifact, dict) else ""
    if meta_type != artifact_type:
        return jsonify({"error": "Invalid artifact type"}), 400

    # return the full artifact but normalized fields at top-level for safety
    normalized = serialize_artifact(id, artifact)

    # also include the rest of the artifact payload if present
    full = dict(artifact) if isinstance(artifact, dict) else {}

    # overwrite top-level id/name/type/version/metadata with normalized values
    full.update(normalized)
    return jsonify(full), 200


@retrieve_bp.route("/artifact/<artifact_type>/<id>/cost", methods=["GET"], strict_slashes=False)
def get_cost(artifact_type: str, id: str):
    """
    Return cost for an artifact.
    """
    # check for dependencies
    dependency = request.args.get("dependency", "false").lower() == "true"

    # handle missing artifact type or id
    if not artifact_type or not id:
        return jsonify({"error": "Missing field(s)"}), 400

    # get path to registry
    if ENV == "local":
        registry_path = current_app.config.get("REGISTRY_PATH")
        assert registry_path is not None
        registry = load_registry(registry_path)
    else:
        registry = load_registry()

    # get artifact
    artifact = registry.get(id)
    if not artifact:
        return jsonify({"error": "Artifact not found"}), 404

    # INSERT COST CALCULATIONS HERE
    try:
        standalone_cost = float(artifact.get("standalone_cost") or 0)
        total_cost = float(artifact.get("total_cost") or 0)

        if dependency:
            response = {
                str(id): {
                    "standalone_cost": standalone_cost,
                    "total_cost": total_cost
                }
            }
        else:
            response = {
                str(id): {
                    "total_cost": total_cost
                }
            }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": f"Error calculating artifact cost: {str(e)}"}), 500


@retrieve_bp.route("/artifact/<artifact_type>/<id>/audit", methods=["GET"], strict_slashes=False)
def get_audit(artifact_type: str, id: str):
    '''
    Get the audit log for an artifact
    '''
    if not artifact_type or not id:
        return jsonify({"error": "Missing field(s)"}), 400
    
    if ENV == "local":
        registry_path = current_app.config.get("REGISTRY_PATH")
        assert registry_path is not None
        registry = load_registry(registry_path)
    else:
        registry = load_registry()

    artifact = registry.get(id)
    if not artifact:
        return jsonify({"error": "Artifact not found"}), 404
    
    # add to audit
    name = "Name" # Change this later
    admin = False # Change this later
    artifact_name = artifact["metadata"]["name"]
    add_to_audit(name, admin, artifact_type, id, artifact_name, "AUDIT") 
    
    # get audit log 
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

    if ENV == "local":
        registry_path = current_app.config.get("REGISTRY_PATH")
        assert registry_path is not None
        registry = load_registry(registry_path)
    else:
        registry = load_registry()

    artifact = registry.get(id) if isinstance(registry, dict) else None
    if not artifact:
        return jsonify({"error": "Artifact not found"}), 404

    lineage = build_lineage_graph(registry, str(id), artifact)

    if not isinstance(lineage, dict) or "nodes" not in lineage or "edges" not in lineage:
        meta = artifact.get("metadata") or {}
        data = artifact.get("data") or {}

        root_node = {
            "artifact_id": str(meta.get("id") or id),
            "name": str(meta.get("name") or ""),
            "source": "metadata",
        }

        url = data.get("url")
        if isinstance(url, str) and url:
            root_node["metadata"] = {"repository_url": url}

        lineage = {
            "nodes": [root_node],
            "edges": [],
        }

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
    except Exception:
        return jsonify({"error": "License information couldn't be retrieved"}), 502

    return jsonify(compatible), 200


@retrieve_bp.route("/artifact/byRegEx", methods=["POST"], strict_slashes=False)
def get_by_regex():
    """
    Body format expected: {"regex": "<pattern>"}
    Returns list of serialized artifacts whose name matches the regex.
    """
    data = request.get_json(force=True, silent=True)
    if not data or "regex" not in data:
        return jsonify({"error": "Missing regex"}), 400

    pattern = data["regex"]
    if not isinstance(pattern, str):
        return jsonify({"error": "Invalid regex type"}), 400

    try:
        compiled_regex = re.compile(pattern, re.IGNORECASE)
    except re.error:
        return jsonify({"error": "Invalid regular expression"}), 400

    if ENV == "local":
        registry_path = current_app.config.get("REGISTRY_PATH")
        assert registry_path is not None
        registry = load_registry(registry_path)
    else:
        registry = load_registry()

    matches = []
    for artifact_id, artifact in registry.items():
        metadata = artifact.get("metadata", {}) if isinstance(artifact, dict) else {}
        name = str(metadata.get("name", ""))
        if compiled_regex.search(name):
            matches.append(serialize_artifact(artifact_id, artifact))

    if not matches:
        return jsonify({"error": "No artifacts found"}), 404

    return jsonify(matches), 200
