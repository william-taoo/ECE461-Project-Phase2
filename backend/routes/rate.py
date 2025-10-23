from flask import Blueprint, jsonify
from utils.registry_utils import load_registry, save_registry

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
    registry = load_registry()
    # Get model and rate using phase 1 metrics

    # Save scores to registry
    save_registry(registry)

    return jsonify({
        "model_id": model_id,
        # "scores": scores
    })