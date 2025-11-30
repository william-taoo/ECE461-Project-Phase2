from typing import Any, Dict, Iterable, List, Tuple, Set
import json
from urllib.parse import urlparse
from huggingface_hub import HfApi
from utils.registry_utils import HF_HOSTS

class LineageComputationError(Exception):
    pass

def _hf_repo_id_from_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc not in HF_HOSTS:
        raise LineageComputationError("Artifact is not hosted on HuggingFace.")

    parts = [p for p in parsed.path.strip("/").split("/") if p]
    if len(parts) < 2:
        raise LineageComputationError("Could not determine HuggingFace repo_id from URL.")

    return f"{parts[0]}/{parts[1]}"

def load_config_for_artifact(artifact: Dict[str, Any]) -> Dict[str, Any]:
    data = artifact.get("data") or {}
    url = data.get("url")
    if not isinstance(url, str) or not url:
        raise LineageComputationError("Artifact is missing data.url")

    repo_id = _hf_repo_id_from_url(url)

    try:
        api = HfApi()
        cfg_path = api.hf_hub_download(repo_id=repo_id, filename="config.json")
    except Exception as e:
        raise LineageComputationError(f"Could not download config.json for {repo_id}") from e

    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception as e:
        raise LineageComputationError("Malformed or unreadable config.json") from e

    if not isinstance(cfg, dict):
        raise LineageComputationError("config.json is not a JSON object")

    return cfg

def _collect_strings(obj: Any) -> Set[str]:
    found: Set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, str):
            s = node.strip().lower()
            if s:
                found.add(s)
        elif isinstance(node, dict):
            for k, v in node.items():
                walk(k)
                walk(v)
        elif isinstance(node, (list, tuple, set)):
            for item in node:
                walk(item)

    walk(obj)
    return found

def iter_registry_items(registry: Any) -> Iterable[Tuple[str, Dict[str, Any]]]:
    if isinstance(registry, dict):
        for aid, artifact in registry.items():
            if isinstance(artifact, dict):
                yield str(aid), artifact
        return

    # Fallback for list-style registries (older formats)
    for artifact in registry or []:
        if not isinstance(artifact, dict):
            continue
        meta = artifact.get("metadata") or {}
        aid = meta.get("id")
        if not aid:
            continue
        yield str(aid), artifact

def build_lineage_graph(
    registry: Any,
    root_id: str,
    root_artifact: Dict[str, Any],
    config: Dict[str, Any],
    ) -> Dict[str, Any]:

    nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []
    def add_node_for_artifact(artifact_id: str, artifact: Dict[str, Any]) -> None:
        meta = artifact.get("metadata") or {}
        data = artifact.get("data") or {}

        node_id = str(meta.get("id") or artifact_id)
        name = str(meta.get("name") or "")

        node: Dict[str, Any] = {
            "node": node_id,
            "artifact_id": node_id,
            "name": name,
            "source": "config_json",
        }

        version = meta.get("version")
        if version is not None:
            node["version"] = str(version)

        lineage_meta: Dict[str, Any] = {}
        url = data.get("url")
        if isinstance(url, str) and url:
            lineage_meta["repository_url"] = url

        if lineage_meta:
            node["metadata"] = lineage_meta

        nodes[str(artifact_id)] = node
    
    add_node_for_artifact(root_id, root_artifact)
    config_strings = _collect_strings(config)
    for candidate_id, candidate in iter_registry_items(registry):
        if candidate_id == root_id:
            continue

        meta = candidate.get("metadata") or {}
        name = meta.get("name")
        if not isinstance(name, str) or not name.strip():
            continue

        name_norm = name.strip().lower()
        if not name_norm:
            continue

        if name_norm in config_strings:
            if candidate_id not in nodes:
                add_node_for_artifact(candidate_id, candidate)

            candidate_type = str(meta.get("type") or "").lower()
            if candidate_type == "dataset":
                relationship = "fine_tuning_dataset"
            else:
                relationship = "base_model"

            edges.append(
                {
                    "from_node_artifact_id": candidate_id,  # upstream
                    "to_node_artifact_id": root_id,        # this model
                    "relationship": relationship,
                }
            )

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
    }