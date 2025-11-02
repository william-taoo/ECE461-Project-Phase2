from flask import Blueprint, request, jsonify, current_app
from utils.registry_utils import (
    load_registry,
    save_registry,
    find_model_in_registry
)
from utils.time_utils import ms_to_seconds

ModelClass = None
try:
    from CustomObjects.Model import Model as ModelClass  # type: ignore
except Exception:
    try:
        from Model import Model as ModelClass  # type: ignore
    except Exception:
        ModelClass = None

rate_bp = Blueprint("rate", __name__)

@rate_bp.route("/artifact/model/<id>/rate", methods=["GET"])
def rate_model(id):
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
    if ModelClass is None:
        return jsonify({"error": "Model implementation unavailable"}), 500

    registry_path = current_app.config.get("REGISTRY_PATH")
    if not registry_path:
        return jsonify({"error": "Server misconfigured: REGISTRY_PATH unset"}), 500

    registry = load_registry(registry_path)
    entry = find_model_in_registry(registry, id) or registry.get(id)
    if not entry:
        return jsonify({"error": "Artifact does not exist."}), 404
    
    metadata = entry.get("metadata") or {}
    data = entry.get("data") or {}

    if (metadata.get("type") or "").lower() != "model":
        return jsonify({"error": "Rating is only supported for artifact_type=model."}), 400

    model_url = (data.get("url") or "").strip()
    dataset_url = (data.get("dataset_url") or metadata.get("dataset_url") or "").strip()
    code_url = (data.get("code_url") or metadata.get("code_url") or "").strip()

    if not model_url:
        return jsonify({"error": "Artifact is missing model url"}), 400
    
    model = ModelClass(model_url=model_url, dataset_url=dataset_url, code_url=code_url)

    api_key = current_app.config.get("API_KEY")

    try:
        model.compute_net_score(api_key=api_key)
    except Exception as e:
        return jsonify({"error": f"Failed to compute net score: {e}"}), 500
    
    size_score = getattr(model, "size_score", {}) or {}
    size_score = {
        "raspberry_pi": float(size_score.get("raspberry_pi", 0.0)),
        "jetson_nano": float(size_score.get("jetson_nano", 0.0)),
        "desktop_pc": float(size_score.get("desktop_pc", 0.0)),
        "aws_server": float(size_score.get("aws_server", 0.0)),
    }

    response = {
        "name": (model.get_name() or metadata.get("name") or "").strip(),
        "category": "model",

        "net_score": float(getattr(model, "net_score", 0.0)),
        "net_score_latency": ms_to_seconds(getattr(model, "net_score_latency", 0)),

        "ramp_up_time": float(getattr(model, "ramp_up_time", 0.0)),
        "ramp_up_time_latency": ms_to_seconds(getattr(model, "ramp_up_time_latency", 0)),

        "bus_factor": float(getattr(model, "bus_factor", 0.0)),
        "bus_factor_latency": ms_to_seconds(getattr(model, "bus_factor_latency", 0)),

        "performance_claims": float(getattr(model, "performance_claims", 0.0)),
        "performance_claims_latency": ms_to_seconds(getattr(model, "performance_claims_latency", 0)),

        "license": float(getattr(model, "license_score", 0.0)),
        "license_latency": ms_to_seconds(getattr(model, "license_latency", 0)),

        "dataset_and_code_score": float(getattr(model, "dataset_and_code_score", 0.0)),
        "dataset_and_code_score_latency": ms_to_seconds(getattr(model, "dataset_and_code_score_latency", 0)),

        "dataset_quality": float(getattr(getattr(model, "dataset", object()), "quality", 0.0)),
        "dataset_quality_latency": ms_to_seconds(getattr(model, "dataset_quality_latency", 0)),

        "code_quality": float(getattr(getattr(model, "code", object()), "quality", 0.0)),
        "code_quality_latency": ms_to_seconds(getattr(model, "code_quality_latency", 0)),

        # New metrics (already computed inside Model.py)
        "reproducibility": float(getattr(model, "reproducibility", 0.0)),
        "reproducibility_latency": ms_to_seconds(getattr(model, "reproducibility_latency", 0)),

        "reviewedness": float(getattr(model, "reviewedness", 0.0)),  # may be -1.0 if unknown
        "reviewedness_latency": ms_to_seconds(getattr(model, "reviewedness_latency", 0)),

        "tree_score": float(getattr(model, "treescore", 0.0)),
        "tree_score_latency": ms_to_seconds(getattr(model, "treescore_latency", 0)),

        "size_score": size_score,
        "size_score_latency": ms_to_seconds(getattr(model, "size_score_latency", 0)),
    }

    entry["rating"] = response
    registry[id] = entry
    save_registry(registry_path, registry)

    return jsonify(response), 200
    
    
