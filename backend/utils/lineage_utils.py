from typing import Any, Dict, Iterable, List, Tuple, Set, Optional
import json
import os
from urllib.parse import urlparse
from huggingface_hub import HfApi
from utils.registry_utils import HF_HOSTS

def _hf_repo_id_from_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc not in HF_HOSTS:
        return None

    parts = [p for p in parsed.path.strip("/").split("/") if p]
    if len(parts) < 2:
        return None

    return f"{parts[0]}/{parts[1]}"

def _find_embedded_config(obj: Any) -> Optional[Dict[str, Any]]:
    if isinstance(obj, dict):
        for key in ("config", "config_json"):
            cfg = obj.get(key)
            if isinstance(cfg, dict):
                return cfg

        if "model_type" in obj:
            return obj

        for v in obj.values():
            found = _find_embedded_config(v)
            if found is not None:
                return found

    elif isinstance(obj, (list, tuple, set)):
        for item in obj:
            found = _find_embedded_config(item)
            if found is not None:
                return found

    return None

def _load_config_from_local_path(path: str) -> Optional[Dict[str, Any]]:
    if not isinstance(path, str) or not path:
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg if isinstance(cfg, dict) else None
    except Exception:
        return None
    
def load_config_for_artifact(artifact: Dict[str, Any]) -> Dict[str, Any]:
    metadata = artifact.get("metadata") or {}
    data = artifact.get("data") or {}

    embedded = _find_embedded_config(metadata)
    if embedded is None:
        embedded = _find_embedded_config(data)
    if isinstance(embedded, dict):
        return embedded

    for container in (metadata, data):
        for key in ("config_path", "config_json_path", "config_file"):
            path = container.get(key)
            if isinstance(path, str) and path:
                cfg = _load_config_from_local_path(path)
                if isinstance(cfg, dict):
                    return cfg

    data = artifact.get("data") or {}
    url = data.get("url")
    if isinstance(url, str) and url:
        repo_id = _hf_repo_id_from_url(url)
        if repo_id and HfApi is not None:
            try:
                api = HfApi()
                cfg_path = api.hf_hub_download(repo_id=repo_id, filename="config.json")
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                if isinstance(cfg, dict):
                    return cfg
            except Exception:
                pass

    return metadata if isinstance(metadata, dict) and metadata else None

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
    ) -> Dict[str, Any]:

    id_to_artifact: Dict[str, Dict[str, Any]] = {
        aid: art for aid, art in iter_registry_items(registry)
    }

    nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []

    def add_node_for_artifact(artifact_id: str, artifact: Dict[str, Any], source: str) -> None:
        meta = artifact.get("metadata") or {}
        data = artifact.get("data") or {}

        node_id = str(meta.get("id") or artifact_id)
        name = str(meta.get("name") or "")
        version = str(meta.get("version") or "")

        node: Dict[str, Any] = {
            "artifact_id": node_id,
            "name": name,
            "version": version,
            "source": source,
        }

        lineage_meta: Dict[str, Any] = {}
        url = data.get("url")
        if isinstance(url, str) and url:
            lineage_meta["repository_url"] = url

        if lineage_meta:
            node["metadata"] = lineage_meta

        if artifact_id in nodes:
            existing = nodes[artifact_id]
            for k, v in node.items():
                if k not in existing or existing[k] in (None, "", {}):
                    existing[k] = v
        else:
            nodes[artifact_id] = node

    visited: Set[str] = set()
    queue: List[str] = [root_id]

    while queue:
        current_id = queue.pop(0)
        if current_id in visited:
            continue
        visited.add(current_id)

        if current_id == root_id:
            artifact = root_artifact
        else:
            artifact = id_to_artifact.get(current_id)
            if artifact is None:
                continue

        cfg = load_config_for_artifact(artifact)
        cfg_strings = _collect_strings(cfg) if isinstance(cfg, dict) else set()

        source = "config_json" if cfg_strings else "metadata"
        add_node_for_artifact(current_id, artifact, source=source)

        if not cfg_strings:
            continue

        meta_cur = artifact.get("metadata") or {}
        cur_name_norm = str(meta_cur.get("name") or "").strip().lower()

        possible_parents: List[Tuple[int, str, Dict[str, Any]]] = []

        for candidate_id, candidate in id_to_artifact.items():
            if candidate_id == current_id:
                continue

            meta = candidate.get("metadata") or {}
            cand_type = str(meta.get("type") or "").lower()

            if cand_type != "model":
                continue

            name = meta.get("name")
            cand_name_norm = name.strip().lower() if isinstance(name, str) else ""
            cid_norm = str(meta.get("id") or candidate_id).strip().lower()

            def matches_token(token: str) -> bool:
                return bool(token) and any(token in s or s in token for s in cfg_strings)

            name_matches = cand_name_norm and matches_token(cand_name_norm)
            id_matches = cid_norm and matches_token(cid_norm)

            if not (name_matches or id_matches):
                continue

            score = 0
            if cand_name_norm and cur_name_norm and cand_name_norm in cur_name_norm:
                score = 3
            elif name_matches:
                score = 2
            elif id_matches:
                score = 1

            possible_parents.append((score, candidate_id, candidate))

        if possible_parents:
            possible_parents.sort(key=lambda t: (-t[0], t[1]))
            _, best_parent_id, best_parent_art = possible_parents[0]

            add_node_for_artifact(best_parent_id, best_parent_art, source="config_json")

            edges.append(
                {
                    "from_node_artifact_id": best_parent_id,
                    "to_node_artifact_id": current_id,
                    "relationship": "base_model",
                }
            )

            if best_parent_id not in visited:
                queue.append(best_parent_id)

    if root_id not in nodes:
        add_node_for_artifact(root_id, root_artifact, source="metadata")

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
    }