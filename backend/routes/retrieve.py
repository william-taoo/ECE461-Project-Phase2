from flask import Blueprint, request, jsonify, current_app
from utils.registry_utils import load_registry, add_to_audit, get_audit_entries
from utils.artifact_size import get_artifact_size
import re
import fnmatch
import typing

retrieve_bp = Blueprint("retrieve", __name__)


def serialize_artifact(artifact_id: str, artifact: dict) -> dict:
    """
    Return a normalized artifact dict.
    """
    # get artifact metadata
    metadata = (
        artifact.get("metadata", {}) if isinstance(artifact, dict) else {}
    )

    return {
        "id": str(artifact_id),
        "name": metadata.get("name", "") if isinstance(metadata, dict) else "",
        "type": metadata.get("type", "") if isinstance(metadata, dict) else "",
        "version": (
            metadata.get("version", "") if isinstance(metadata, dict) else ""
        ),
        # keep original metadata object (empty dict if missing)
        "metadata": metadata if isinstance(metadata, dict) else {},
    }


@retrieve_bp.route("/artifacts", methods=["POST"], strict_slashes=False)
def get_artifacts():
    """
    This will send a request for models in the registry
    given a name and type
    """
    # get path to registry
    registry_path = current_app.config.get("REGISTRY_PATH")
    assert registry_path is not None
    registry = load_registry(registry_path)

    # parse JSON safely (handle single element list)
    query = request.get_json(force=True, silent=True)
    if isinstance(query, list) and len(query) == 1:
        query = query[0]

    if not query or not isinstance(query, dict):
        return jsonify({"error": "Invalid request format"}), 400

    # query parameters
    name_query = str(query.get("name", "*")).strip()
    type_query = str(query.get("type", "all")).strip().lower()
    version_query = str(query.get("version", "")).strip()

    try:
        offset = int(request.args.get("offset", 0))
    except Exception:
        offset = 0
    page_size = 10

    results: typing.List[dict] = []

    # iterate items so we have artifact_id and artifact object
    for artifact_id, artifact in registry.items():
        meta = (
            artifact.get("metadata", {}) if isinstance(artifact, dict) else {}
        )
        name = str(meta.get("name", "")) if isinstance(meta, dict) else ""
        a_type = (
            str(meta.get("type", "")).lower() if isinstance(meta, dict) else ""
        )
        version = (
            str(meta.get("version", "")) if isinstance(meta, dict) else ""
        )

        # name filter
        if name_query != "*" and name_query.lower() != name.lower():
            continue

        # type filter
        if type_query != "all" and a_type != type_query:
            continue

        # version filter (supports wildcard)
        if version_query:
            if "*" in version_query:
                if not fnmatch.fnmatch(version, version_query):
                    continue
            elif version_query != version:
                continue

        results.append(serialize_artifact(artifact_id, artifact))

    # limit guard if too many artifacts are returned
    if len(results) > 100:
        return jsonify({"error": "Too many artifacts returned"}), 413

    paginated = results[offset: offset + page_size]
    next_offset = offset + len(paginated)

    response = jsonify(paginated)
    response.headers["offset"] = str(next_offset)
    return response, 200


@retrieve_bp.route(
    "/artifact/byName/<name>", methods=["GET"], strict_slashes=False
)
def get_name(name: str):
    """
    Return metadata for all artifacts matching the provided name.
    Returns a list of serialized artifacts.
    """
    # handle missing artifact name
    if not name or not name.strip():
        return jsonify({"error": "Missing or invalid artifact name"}), 400

    # get path to registry
    registry_path = current_app.config.get("REGISTRY_PATH")
    assert registry_path is not None
    registry = load_registry(registry_path)

    results = []
    query = name.strip().lower()

    # append artifacts that match the name query
    for artifact_id, artifact in registry.items():
        metadata = (
            artifact.get("metadata", {}) if isinstance(artifact, dict) else {}
        )
        artifact_name = (
            str(metadata.get("name", "")).strip().lower()
            if isinstance(metadata, dict)
            else ""
        )
        if artifact_name == query:
            results.append(serialize_artifact(artifact_id, artifact))

    # handle no results
    if not results:
        return jsonify({"error": "No artifacts found"}), 404

    return jsonify(results), 200


@retrieve_bp.route(
    "/artifacts/<artifact_type>/<id>", methods=["GET"], strict_slashes=False
)
def get_artifact(artifact_type: str, id: str):
    """
    Retrieve the full stored artifact entry by id. We return the raw artifact
    object but ensure it includes id/name/type/version/metadata via
    serialization.
    """
    # get path to registry
    registry_path = current_app.config.get("REGISTRY_PATH")
    assert registry_path is not None
    registry = load_registry(registry_path)

    # get artifact by id
    artifact = registry.get(id)
    if not artifact:
        return jsonify({"error": "Artifact not found"}), 404

    # type check
    meta_type = (
        artifact.get("metadata", {}).get("type", "")
        if isinstance(artifact, dict)
        else ""
    )
    if meta_type != artifact_type:
        return jsonify({"error": "Invalid artifact type"}), 400

    # return the full artifact but normalized fields at top-level for safety
    normalized = serialize_artifact(id, artifact)

    # also include the rest of the artifact payload if present
    full = dict(artifact) if isinstance(artifact, dict) else {}

    # overwrite top-level id/name/type/version/metadata with normalized values
    full.update(normalized)
    return jsonify(full), 200


@retrieve_bp.route(
    "/artifact/<artifact_type>/<id>/cost",
    methods=["GET"],
    strict_slashes=False,
)
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
    registry_path = current_app.config.get("REGISTRY_PATH")
    assert registry_path is not None
    registry = load_registry(registry_path)

    # get artifact
    artifact = registry.get(id)
    if not artifact:
        return jsonify({"error": "Artifact not found"}), 404

    # INSERT COST CALCULATIONS HERE
    artifact_data = artifact.get("data")
    artifact_url = artifact_data.get("url")
    try:
        standalone_cost = float(get_artifact_size(artifact_url, artifact_type))
        if not standalone_cost:
            standalone_cost = 0.0

        # FIX THIS LOGIC
        total_cost = standalone_cost

        if dependency:
            response = {
                str(id): {
                    "standalone_cost": standalone_cost,
                    "total_cost": total_cost,
                }
            }
        else:
            response = {str(id): {"total_cost": total_cost}}

        return jsonify(response), 200

    except Exception as e:
        return (
            jsonify({"error": f"Error calculating artifact cost: {str(e)}"}),
            500,
        )


@retrieve_bp.route(
    "/artifact/<artifact_type>/<id>/audit",
    methods=["GET"],
    strict_slashes=False,
)
def get_audit(artifact_type: str, id: str):
    """
    Get the audit log for an artifact
    """
    if not artifact_type or not id:
        return jsonify({"error": "Missing field(s)"}), 400

    registry_path = current_app.config["REGISTRY_PATH"]
    registry = load_registry(registry_path)
    artifact = registry.get(id)
    if not artifact:
        return jsonify({"error": "Artifact not found"}), 404

    # add to audit
    name = "Name"  # CHANGE THIS LATER
    admin = False  # CHANGE THIS LATER
    artifact_name = artifact["metadata"]["name"]
    add_to_audit(name, admin, artifact_type, id, artifact_name, "AUDIT")

    # get audit log
    audit = get_audit_entries(id)
    if audit is None:
        return jsonify({"error": "Error with audit log"}), 400
    else:
        return jsonify(audit), 200


@retrieve_bp.route(
    "/artifact/model/<id>/lineage",
    methods=["GET"],
    strict_slashes=False,
)
def get_lineage(id: str):
    """
    Get the lineage graph of an artifact.
    """
    if not id:
        return jsonify({"error": "Missing field"}), 400

    registry_path = current_app.config["REGISTRY_PATH"]
    registry = load_registry(registry_path)
    artifact = registry.get(id)
    if not artifact:
        return jsonify({"error": "Artifact not found"}), 404

    # get lineage graph

    # INSERT LINEAGE GRAPH LOGIC HERE

    lineage = {}

    return jsonify(lineage), 200


@retrieve_bp.route(
    "/artifact/model/<id>/license-check",
    methods=["POST"],
    strict_slashes=False,
)
def check_license(id: str):
    """
    Check if the license is compatible.
    """
    data = request.get_json()
    if not data or "github_url" not in data:
        return jsonify({"error": "Missing github_url"}), 400

    # PLACE ACTUAL CHECK LICENSE LOGIC HERE

    valid_url = True
    if not valid_url:
        return jsonify({"error": "Invalid github URL"}), 404

    # Check license
    try:
        compatible = True
    except Exception:
        return (
            jsonify({"error": "License information couldn't be retrieved"}),
            502,
        )

    return jsonify(compatible), 200


@retrieve_bp.route("/artifact/byRegEx", methods=["POST"], strict_slashes=False)
def get_by_regex():
    """
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

    registry_path = current_app.config.get("REGISTRY_PATH")
    assert registry_path is not None
    registry = load_registry(registry_path)

    matches = []
    for artifact_id, artifact in registry.items():
        metadata = (
            artifact.get("metadata", {}) if isinstance(artifact, dict) else {}
        )
        name = str(metadata.get("name", ""))
        if compiled_regex.search(name):
            matches.append(serialize_artifact(artifact_id, artifact))

    if not matches:
        return jsonify({"error": "No artifacts found"}), 404

    return jsonify(matches), 200
