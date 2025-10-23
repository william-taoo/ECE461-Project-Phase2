from flask import Blueprint, jsonify
from utils.registry_utils import load_registry, save_registry

download_bp = Blueprint("download", __name__)

@download_bp.route("/download/<model_id>", methods=["GET"])
def download_model(model_id):
    '''
    Download a zipped model from the registry
    Can be downloaded with these options:
    - Full model package,
    - Sub aspects: weights, associated datasets, etc.
    '''
    