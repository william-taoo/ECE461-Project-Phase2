import json
import os
from urllib.parse import urlparse
from pathlib import Path
from datetime import datetime, timezone
import boto3
from dotenv import load_dotenv
load_dotenv()

ENV = os.getenv("ENVIRONMENT", "local")

HF_HOSTS = {"huggingface.co", "hf.co"}
CODE_HOSTS = {
    "github.com", "gitlab.com", "bitbucket.org",
    "raw.githubusercontent.com", "gitlabusercontent.com"
}
MODEL_EXTS = (
    ".pt", ".safetensors", ".bin", ".onnx", ".pb", ".tflite",
    ".ckpt", ".gguf", ".ggml", ".zip", ".tar", ".tar.gz", ".whl"
)
AUDIT_ACTIONS = ["CREATE", "UPDATE", "DOWNLOAD", "RATE", "AUDIT"]
AUDIT_DIR = Path("audit_logs")

s3 = boto3.client("s3", region_name="us-east-2")

BUCKET_NAME = "461-phase2-team12"
KEY = "registry.json"

def audit_path(artifact_id: str):
    path = AUDIT_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path / f"{artifact_id}.json"

def add_to_audit(user: str, admin: bool, artifact_type: str, artifact_id: str, artifact_name: str, action: str):
    if action not in AUDIT_ACTIONS:
        return None # Return status 400

    path = audit_path(artifact_id)
    entry = {
        "user": {
            "name": user,
            "admin": admin
        },
        "date": datetime.now(timezone.utc).isoformat() + "Z",
        "artifact": {
            "name": artifact_name,
            "id": artifact_id,
            "type": artifact_type,
        },
        "action": action
    }

    if path.exists():
        with open(path, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(entry)
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def get_audit_entries(artifact_id):
    path = audit_path(artifact_id)

    if not path.exists():
        return None # Return status 404

    with open(path, "r") as f:
        return json.load(f)

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

def load_registry(path):
    """
    Load the registry from S3. If it doesn't exist, return an empty dict.
    """
    print(path)
    if ENV == "local":
        if not os.path.exists(path):
            return {}
        with open(path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=KEY)
        content = response["Body"].read().decode("utf-8")
        return _as_dict(json.loads(content))
    except s3.exceptions.NoSuchKey:
        # Registry file doesn't exist yet
        return {}
    except Exception as e:
        raise RuntimeError(f"Failed to load registry from S3: {e}") from e


def save_registry(path, data):
    """
    Save the registry to S3. Hii
    """
    data = _as_dict(data)

    if ENV == "local":
        dirpath = os.path.dirname(os.path.abspath(path))
        if dirpath and not os.path.exists(dirpath):
            os.makedirs(dirpath, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
        return 

    try:
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=KEY,
            Body=json.dumps(data, indent=4),
            ContentType="application/json"
        )
    except Exception as e:
        raise RuntimeError(f"Failed to save registry to S3: {e}") from e

def iter_registry(registry):
    if isinstance(registry, dict):
        for aid, item in registry.items():
            yield str(aid), item
    elif isinstance(registry, list):
        for item in registry:
            aid = str(item.get("metadata", {}).get("id") or item.get("id") or "")
            yield aid, item

def find_model_in_registry(registry, model_id: str):
    if isinstance(registry, dict):
        return registry.get(model_id)
    for item in registry or []:
        if _extract_id(item) == model_id:
            return item
    return None
