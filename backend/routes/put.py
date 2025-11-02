from flask import Blueprint, request, jsonify, current_app
from utils.registry_utils import load_registry, save_registry
import jwt
from datetime import datetime, timezone, timedelta


put_bp = Blueprint("put", __name__)

@put_bp.route("/artifacts/<artifact_type>/<id>", methods=["PUT"])
def update_artifact(artifact_type: str, id: str):
    # Access to config for registry path
    registry_path = current_app.config["REGISTRY_PATH"]
    registry = load_registry(registry_path)
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing artifact data"}), 400
    
    if id not in registry:
        return jsonify({"error": "Artifact not found"}), 404
    
    # Verify id and type match
    old_artifact = registry[id]
    if (
        old_artifact["metadata"]["id"] != data["metadata"]["id"]
        or old_artifact["metadata"]["type"] != artifact_type
    ):
        return jsonify({"error": "ID or type mismatch"}), 400

    # Replace the artifact contents
    registry[id] = data
    save_registry(registry_path, registry)

    return jsonify({"message": "Artifact updated"}), 200

@put_bp.route("/authenticate", methods=["PUT"])
def authenticate():
    try:
        data = request.get_json()
        if not data or "user" not in data or "secret" not in data:
            return jsonify({"error": "Missing fields"}), 400

        username = data["user"].get("name")
        password = data["secret"].get("password")

        if not username or not password:
            return jsonify({"error": "Missing username or password"}), 401

        # Create JWT token
        token = jwt.encode({
            "sub": username,
            "is_admin": True,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }, current_app.config['SECRET_KEY'], algorithm="HS256")

        return jsonify(f"bearer {token}"), 200
    except Exception as e:
        print(e)
        return jsonify({"error": "Not implemented"}), 501

