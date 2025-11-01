from flask import Blueprint, request, jsonify, current_app
from utils.registry_utils import (
    load_registry,
    save_registry,
    find_model_in_registry
)


rate_bp = Blueprint("rate", __name__)

@rate_bp.route("/rate/<model_id>", methods=["GET"])
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
    registry_path = current_app.config["REGISTRY_PATH"]
    registry = load_registry(registry_path)

    # Check if model is in registry
    model = find_model_in_registry(registry, model_id)
    if not model:
        return jsonify({"error": "Model not found"}), 404

    # Get model and rate using phase 1 metrics
    scores = 0 

    # Save scores to registry
    model["scores"] = scores
    save_registry(registry_path, registry)

    return jsonify({
        "model_id": model_id,
        "scores": scores
    })