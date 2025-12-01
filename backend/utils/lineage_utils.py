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

    id_to_model: Dict[str, Dict[str, Any]] = {}
    for aid, art in iter_registry_items(registry):
        meta = art.get("metadata") or {}
        if str(meta.get("type") or "").lower() == "model":
            id_to_model[aid] = art

    root_meta = root_artifact.get("metadata") or {}
    if str(root_meta.get("type") or "").lower() == "model":
        id_to_model[root_id] = root_artifact

    if not id_to_model:
        nodes = []
        meta = root_artifact.get("metadata") or {}
        data = root_artifact.get("data") or {}

        node = {
            "artifact_id": str(meta.get("id") or root_id),
            "name": str(meta.get("name") or ""),
            "version": str(meta.get("version") or ""),
            "source": "metadata",
        }
        url = data.get("url")
        if isinstance(url, str) and url:
            node["metadata"] = {"repository_url": url}

        nodes.append(node)
        return {"nodes": nodes, "edges": []}

    candidate_tokens: Dict[str, Tuple[str, str]] = {}
    for cand_id, cand in id_to_model.items():
        meta = cand.get("metadata") or {}
        nm = meta.get("name")
        name_norm = nm.strip().lower() if isinstance(nm, str) else ""
        cid_norm = str(meta.get("id") or cand_id).strip().lower()
        candidate_tokens[cand_id] = (name_norm, cid_norm)

    has_config: Dict[str, bool] = {}
    edges: List[Dict[str, Any]] = []

    for cur_id, cur_art in id_to_model.items():
        cfg = load_config_for_artifact(cur_art)
        cfg_strings = _collect_strings(cfg) if isinstance(cfg, dict) else set()
        has_config[cur_id] = bool(cfg_strings)

        if not cfg_strings:
            continue

        meta_cur = cur_art.get("metadata") or {}
        cur_name_norm = str(meta_cur.get("name") or "").strip().lower()

        possible_parents: List[Tuple[int, str]] = []

        for cand_id, (cand_name_norm, cand_id_norm) in candidate_tokens.items():
            if cand_id == cur_id:
                continue

            def matches_token(token: str) -> bool:
                return bool(token) and any(token in s or s in token for s in cfg_strings)

            name_matches = matches_token(cand_name_norm)
            id_matches = matches_token(cand_id_norm)

            if not (name_matches or id_matches):
                continue

            score = 0
            if cand_name_norm and cur_name_norm and cand_name_norm in cur_name_norm:
                score = 3
            elif name_matches:
                score = 2
            elif id_matches:
                score = 1

            possible_parents.append((score, cand_id))

        if possible_parents:
            possible_parents.sort(key=lambda t: (-t[0], t[1]))
            _, best_parent_id = possible_parents[0]

            edges.append(
                {
                    "from_node_artifact_id": best_parent_id,
                    "to_node_artifact_id": cur_id,
                    "relationship": "base_model",
                }
            )

    neighbors: Dict[str, Set[str]] = {mid: set() for mid in id_to_model.keys()}
    for e in edges:
        u = str(e["from_node_artifact_id"])
        v = str(e["to_node_artifact_id"])
        neighbors.setdefault(u, set()).add(v)
        neighbors.setdefault(v, set()).add(u)

    component: Set[str] = set()
    if root_id in id_to_model:
        queue: List[str] = [root_id]
        while queue:
            nid = queue.pop(0)
            if nid in component:
                continue
            component.add(nid)
            for nbr in neighbors.get(nid, []):
                if nbr not in component:
                    queue.append(nbr)
    else:
        component = {root_id}
        has_config.setdefault(root_id, False)
        id_to_model[root_id] = root_artifact

    nodes: List[Dict[str, Any]] = []
    for nid in component:
        art = id_to_model.get(nid, root_artifact if nid == root_id else None)
        if not art:
            continue

        meta = art.get("metadata") or {}
        data = art.get("data") or {}

        node_id = str(meta.get("id") or nid)
        name = str(meta.get("name") or "")
        version = str(meta.get("version") or "")
        source = "config_json" if has_config.get(nid) else "metadata"

        node: Dict[str, Any] = {
            "artifact_id": node_id,
            "name": name,
            "version": version,
            "source": source,
        }

        url = data.get("url")
        if isinstance(url, str) and url:
            node["metadata"] = {"repository_url": url}

        nodes.append(node)

    comp_ids = {nid for nid in component}
    filtered_edges = [
        e for e in edges
        if str(e["from_node_artifact_id"]) in comp_ids
        and str(e["to_node_artifact_id"]) in comp_ids
    ]

    return {
        "nodes": nodes,
        "edges": filtered_edges,
    }