import json
import os
from urllib.parse import urlparse

HF_HOSTS = {"huggingface.co", "hf.co"}
CODE_HOSTS = {
    "github.com", "gitlab.com", "bitbucket.org",
    "raw.githubusercontent.com", "gitlabusercontent.com"
}
MODEL_EXTS = (
    ".pt", ".safetensors", ".bin", ".onnx", ".pb", ".tflite",
    ".ckpt", ".gguf", ".ggml", ".zip", ".tar", ".tar.gz", ".whl"
)

def infer_artifact_type(url: str) -> str:
    """
    Return one of: 'model', 'dataset', 'code'
    """
    p = urlparse(url or "")
    if p.scheme not in ("http", "https"):
        raise ValueError("URL must be http(s)")

    host = (p.netloc or "").lower()
    path = (p.path or "").strip("/")

    # Hugging Face
    if host in HF_HOSTS:
        first = path.split("/", 1)[0] if path else ""
        if first == "datasets":
            return "dataset"
        return "model"

    # Common code hosts
    if host in CODE_HOSTS:
        return "code"

    # Generic file servers/buckets: guess by extension
    for ext in MODEL_EXTS:
        if path.endswith(ext):
            return "model"

    # Unknown
    raise ValueError("Could not infer artifact type from URL")

def _extract_id(entry):
    """Support both {id: ...} and {'metadata': {'id': ...}} shapes."""
    if not isinstance(entry, dict):
        return None
    if "id" in entry:
        return entry["id"]
    md = entry.get("metadata", {})
    if isinstance(md, dict) and "id" in md:
        return md["id"]
    return None

def _as_dict(data):
    """
    Normalize registry into a dict keyed by id.
    Accepts legacy list-shaped registries.
    """
    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        out = {}
        for item in data:
            artifact_id = _extract_id(item)
            if artifact_id:
                out[str(artifact_id)] = item
        return out
    return {}

def load_registry(path: str):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def iter_registry(registry):
    if isinstance(registry, dict):
        for aid, item in registry.items():
            yield str(aid), item
    elif isinstance(registry, list):
        for item in registry:
            aid = str(item.get("metadata", {}).get("id") or item.get("id") or "")
            yield aid, item

def save_registry(path: str, data):
    dirpath = os.path.dirname(os.path.abspath(path))
    if dirpath and not os.path.exists(dirpath):
        os.makedirs(dirpath, exist_ok=True)

    data = _as_dict(data)
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def find_model_in_registry(registry, model_id: str):
    if isinstance(registry, dict):
        return registry.get(model_id)
    for item in registry or []:
        if _extract_id(item) == model_id:
            return item
    return None
