from flask import Blueprint, request, jsonify, current_app
from utils.registry_utils import (
    load_registry,
    save_registry,
    find_model_in_registry,
    add_to_audit
)
from utils.time_utils import ms_to_seconds
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
except Exception as e:
    ModelClass = None
    CodeClass = None
    DatasetClass = None

rate_bp = Blueprint("rate", __name__)
ENV = os.getenv("ENVIRONMENT", "local")

STOPWORDS = {
    "https", "http", "www", "com", "org",
    "github", "huggingface",
    "repo", "model", "models",
    "dataset", "datasets",
    "tree", "main", "co"
}


def normalize_token(token: str) -> str:
    token = token.lower()

    # Remove non-alphanumeric characters
    token = re.sub(r"[^a-z0-9]+", "", token)

    # Strip leading and trailing digits ONLY
    token = re.sub(r"^\d+|\d+$", "", token)

    return token


def tokenize(text: str) -> Set[str]:
    if not text:
        return set()

    raw = re.split(r"[\/\.]+", text.lower())
    tokens = set()

    for chunk in raw:
        parts = chunk.split("-")
        if len(parts) > 1:
            tokens.add(normalize_token("-".join(parts)))
        for p in parts:
            nt = normalize_token(p)
            if nt and nt not in STOPWORDS:
                tokens.add(nt)

    return tokens


def has_token_match(model_fp, artifact_fp) -> bool:
    model_tokens = model_fp["name_tokens"] | model_fp["url_tokens"]
    artifact_tokens = artifact_fp["name_tokens"] | artifact_fp["url_tokens"]

    overlap = model_tokens & artifact_tokens

    # Require at least 1 non-trivial token
    return any(len(tok) >= 4 for tok in overlap)


def split_hf_repo(parts):
    NON_REPO_SEGMENTS = {"blob", "resolve", "tree", "viewer", "raw"}
    if len(parts) == 1:
        repo = parts[0]
        return None, repo, repo
    if parts[0] == "datasets":
        if len(parts) == 2:
            repo = parts[1]
            return None, repo, repo
        elif len(parts) >= 3:
            second, third = parts[1], parts[2]
            if third in NON_REPO_SEGMENTS:
                repo = second
                return None, repo, repo
            else:
                owner, repo = second, third
                return owner, repo, f"{owner}/{repo}"
    owner, repo = parts[0], parts[1]
    return owner, repo, f"{owner}/{repo}"


def extract_hf_repo_id(url: str) -> Optional[str]:
    try:
        parsed = urlparse(url)
        if "huggingface.co" not in parsed.netloc:
            return None
        parts = parsed.path.strip("/").split("/")
        _, _, repo_id = split_hf_repo(parts)
        return repo_id
    except Exception:
        return None


def extract_github_repo_id(url: str) -> Optional[str]:
    try:
        url = url.replace(".git", "")
        parsed = urlparse(url.replace("git@", "").replace("github.com:", "github.com/"))
        if "github.com" not in parsed.netloc:
            return None
        parts = parsed.path.strip("/").split("/")
        if len(parts) >= 2:
            return f"{parts[0].lower()}/{parts[1].lower()}"
    except Exception:
        return None


def artifact_fingerprint(entry: dict) -> dict:
    meta = entry.get("metadata", {})
    data = entry.get("data", {})

    url = (data.get("url") or "").strip()
    name = (meta.get("name") or "").strip()

    return {
        "name_tokens": tokenize(name),
        "url_tokens": tokenize(url),
        "hf_id": extract_hf_repo_id(url),
        "gh_id": extract_github_repo_id(url),
    }


def find_associated_artifact(registry, model_entry, artifact_type):
    model_fp = artifact_fingerprint(model_entry)

    for artifact_id, artifact in registry.items():
        meta = artifact.get("metadata", {})
        if meta.get("type") != artifact_type:
            continue

        artifact_fp = artifact_fingerprint(artifact)

        # Automatic match if ANY token overlaps
        if has_token_match(model_fp, artifact_fp):
            return artifact

    return None


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
    
    if not model_url:
        return jsonify({"error": "Artifact is missing model url"}), 400
 
    # Look for associated dataset and code
    dataset_entry = find_associated_artifact(registry, entry, "dataset")
    dataset_url = (dataset_entry.get("data", {}).get("url") or "").strip() if dataset_entry else ""

    code_entry = find_associated_artifact(registry, entry, "code")
    code_url = (code_entry.get("data", {}).get("url") or "").strip() if code_entry else ""

    # Now create model with proper URLs
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
