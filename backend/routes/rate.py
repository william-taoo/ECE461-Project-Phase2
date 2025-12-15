from flask import Blueprint, request, jsonify, current_app
from registry_utils import (
    load_registry,
    save_registry,
    find_model_in_registry,
    add_to_audit
)
from time_utils import ms_to_seconds
import os
from urllib.parse import urlparse
import re
from typing import Optional, Set
from dotenv import load_dotenv
load_dotenv()

try:
    from CustomObjects.Model import Model as ModelClass
    from CustomObjects.Code import Code as CodeClass
    from CustomObjects.Dataset import Dataset as DatasetClass
    from CustomObjects.LLMQuerier import LLMQuerier as LLMPrompter
except Exception as e:
    ModelClass = None
    CodeClass = None
    DatasetClass = None
    LLMPrompter = None

rate_bp = Blueprint("rate", __name__)
ENV = os.getenv("ENVIRONMENT", "local")


def get_dataset_and_code(model_url, dataset_urls, code_urls, api_key):
    response = ["", ""]
    if LLMPrompter is None:
        return response
    
    llm_querier = LLMPrompter(endpoint="https://genai.rcac.purdue.edu/api/chat/completions", api_key=api_key)
    prompt = (
    f"""
        You are a strict data extraction function.

        Task:
        Given a model URL, choose:
        1) the single best matching dataset URL from the dataset list
        2) the single best matching code URL from the code list

        Inputs:
        Model URL:
        {model_url}

        Candidate dataset URLs:
        {dataset_urls}

        Candidate code URLs:
        {code_urls}

        Output rules (CRITICAL):
        - Output MUST be a single line string
        - Output format MUST be:
        dataset_url,code_url
        - Exactly ONE comma must appear
        - No spaces before or after the comma
        - Do NOT include quotes, markdown, explanations, or extra text
        - If no good dataset match exists, leave the dataset part empty
        - If no good code match exists, leave the code part empty

        DO NOT OUTPUT ANYTHING ELSE BESIDES THIS STRING. DO NOT SAY A SINGLE WORD BACK TO ME, JUST GIVE ME THE STRING, NO EXPLANATIONS
        """
    )

    response = llm_querier.query(prompt=prompt) or ","
    response = response.split(",")
    if len(response) != 2:
        response = ["", ""]

    return response


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
    if CodeClass is None:
        return jsonify({"error": "Code implementation unavailable"}), 500
    if DatasetClass is None:
        return jsonify({"error": "Model implementation unavailable"}), 500

    if ENV == "local":
        registry_path = current_app.config.get("REGISTRY_PATH")
        if not registry_path:
            return jsonify({"error": "Server misconfigured: REGISTRY_PATH unset"}), 500

        registry = load_registry(registry_path)
    else:
        registry = load_registry()

    entry = find_model_in_registry(registry, id) or registry.get(id)
    if not entry:
        return jsonify({"error": "Artifact does not exist."}), 404
    
    metadata = entry.get("metadata") or {}
    data = entry.get("data") or {}

    model_url = (data.get("url") or "").strip()
    
    # get dataset and code urls from the registry
    dataset_urls = []
    code_urls = []
    for _, artifact_values in registry.items():
        artifact_type = artifact_values["metadata"]["type"]
        artifact_url = artifact_values["data"]["url"]
        if artifact_type == "dataset":
            dataset_urls.append(artifact_url)
        elif artifact_type == "code":
            code_urls.append(artifact_url)

    api_key = current_app.config.get("API_KEY")

    # prompt the LLM to get the dataset and code URLs
    response = get_dataset_and_code(model_url, dataset_urls, code_urls, api_key)

    dataset_url = ""
    if response[0].startswith(("http://", "https://")):
        dataset_url = response[0]
    
    code_url = ""
    if response[1].startswith(("http://", "https://")):
        code_url = response[1]

    model = ModelClass(model_url=model_url, dataset_url=dataset_url, code_url=code_url)

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

    if ENV == "local":
        save_registry(registry_path, registry)
    else:
        save_registry(data=registry)

    # # Add to audit
    # name = "Name" # Change this later
    # admin = False # Change this later
    # artifact_type = data["metadata"]["type"]
    # artifact_name = data["metadata"]["name"]
    # add_to_audit(name, admin, artifact_type, id, artifact_name, "RATE")

    return jsonify(response), 200