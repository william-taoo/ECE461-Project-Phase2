from flask import Blueprint, request, jsonify, current_app
from utils.registry_utils import load_registry, add_to_audit, get_audit_entries
from utils.lineage_utils import build_lineage_graph
import re
import fnmatch
import typing
import os
from dotenv import load_dotenv

load_dotenv()

retrieve_bp = Blueprint("retrieve", __name__)
ENV = os.getenv("ENVIRONMENT", "local")


# ------------------------
# Registry loader
# ------------------------

def get_registry():
    if ENV == "local":
        registry_path = current_app.config.get("REGISTRY_PATH")
        assert registry_path is not None
        return load_registry(registry_path)
    return load_registry()


# ------------------------
# SERIALIZER (kept for future use)
# ------------------------

def serialize_artifact(artifact_id: str, artifact: dict) -> dict:
    metadata = artifact.get("metadata", {}) if isinstance(artifact, dict) else {}
    return {
        "id": str(artifact_id),
        "name": metadata.get("name", ""),
        "type": metadata.get("type", ""),
        "version": metadata.get("version", ""),
        "metadata": metadata
    }


# ------------------------
# GET ARTIFACTS (QUERY)
# ------------------------

@retrieve_bp.route("/artifacts", methods=["GET", "POST"], strict_slashes=False)
def get_artifacts():
    registry = get_registry()

    query = request.get_json(silent=True) or request.args or {}
    if query is None:
        query = {}
    elif isinstance(query, list):
        query = query[0] if query else {}
    elif not isinstance(query, dict):
        return jsonify({"error": "Invalid request format"}), 400

    name_query = str(query.get("name", "*")).strip()
    type_query = str(query.get("type", "all")).strip().lower()
    version_query = str(query.get("version", "")).strip()

    results: typing.List[dict] = []

    for artifact in registry.values():
        meta = artifact.get("metadata", {})
        name = str(meta.get("name", ""))
        a_type = str(meta.get("type", "")).lower()
        version = str(meta.get("version", ""))

        if name_query != "*" and name_query.lower() != name.lower():
            continue

        if type_query != "all" and a_type != type_query.rstrip("s"):
            continue

        if version_query:
            if "*" in version_query:
                if not fnmatch.fnmatch(version, version_query):
                    continue
            elif version_query != version:
                continue

        # RETURN RAW ARTIFACT
        results.append(artifact)

    return jsonify(results), 200


# ------------------------
# GET BY NAME
# ------------------------

@retrieve_bp.route("/artifact/byName/<name>", methods=["GET"], strict_slashes=False)
def get_name(name: str):
    registry = get_registry()
    query = name.strip().lower()

    results = [
        artifact
        for artifact in registry.values()
        if artifact.get("metadata", {}).get("name", "").lower() == query
    ]

    if not results:
        return jsonify({"error": "No artifacts found"}), 404

    return jsonify(results), 200


# ------------------------
# GET SINGLE ARTIFACT
# ------------------------

@retrieve_bp.route("/artifacts/<artifact_type>/<id>", methods=["GET"], strict_slashes=False)
def get_artifact(artifact_type: str, id: str):
    registry = get_registry()

    artifact = registry.get(id)
    if not artifact:
        return jsonify({"error": "Artifact not found"}), 404

    meta_type = artifact.get("metadata", {}).get("type", "")
    if meta_type != artifact_type.rstrip("s"):
        return jsonify({"error": "Invalid artifact type"}), 400

    return jsonify(artifact), 200


# ------------------------
# COST
# ------------------------

@retrieve_bp.route("/artifact/<artifact_type>/<id>/cost", methods=["GET"], strict_slashes=False)
def get_cost(artifact_type: str, id: str):
    registry = get_registry()

    artifact = registry.get(id)
    if not artifact:
        return jsonify({"error": "Artifact not found"}), 404

    dependency = request.args.get("dependency", "false").lower() == "true"

    standalone_cost = float(artifact.get("standalone_cost") or 0)
    total_cost = float(artifact.get("total_cost") or 0)

    if dependency:
        return jsonify({
            id: {
                "standalone_cost": standalone_cost,
                "total_cost": total_cost
            }
        }), 200

    return jsonify({id: {"total_cost": total_cost}}), 200


# ------------------------
# AUDIT
# ------------------------

@retrieve_bp.route("/artifact/<artifact_type>/<id>/audit", methods=["GET"], strict_slashes=False)
def get_audit(artifact_type: str, id: str):
    registry = get_registry()

    artifact = registry.get(id)
    if not artifact:
        return jsonify({"error": "Artifact not found"}), 404

    artifact_name = artifact["metadata"]["name"]

    add_to_audit(
        user="system",
        admin=False,
        artifact_type=artifact_type,
        artifact_id=id,
        artifact_name=artifact_name,
        action="AUDIT"
    )

    audit = get_audit_entries(id)
    if audit is None:
        return jsonify({"error": "Audit error"}), 400

    return jsonify(audit), 200


# ------------------------
# LINEAGE
# ------------------------

@retrieve_bp.route("/artifact/model/<id>/lineage", methods=["GET"])
def get_lineage(id: str):
    registry = get_registry()

    artifact = registry.get(id)
    if not artifact:
        return jsonify({"error": "Artifact not found"}), 404

    lineage = build_lineage_graph(registry, id, artifact)
    return jsonify(lineage), 200


# ------------------------
# REGEX SEARCH
# ------------------------

@retrieve_bp.route("/artifact/byRegEx", methods=["POST"], strict_slashes=False)
def get_by_regex():
    data = request.get_json(force=True, silent=True)
    if not data or "regex" not in data:
        return jsonify({"error": "Missing regex"}), 400

    try:
        pattern = re.compile(data["regex"], re.IGNORECASE)
    except re.error:
        return jsonify({"error": "Invalid regular expression"}), 400

    registry = get_registry()

    matches = [
        artifact
        for artifact in registry.values()
        if pattern.search(artifact.get("metadata", {}).get("name", ""))
    ]

    if not matches:
        return jsonify({"error": "No artifacts found"}), 404

    return jsonify(matches), 200
