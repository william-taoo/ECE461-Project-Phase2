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
        elif isinstance(node, (int, float, bool)):
            s = str(node).strip().lower()
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

    model_id_to_artifact: Dict[str, Dict[str, Any]] = {}
    for aid, artifact in iter_registry_items(registry):
        if not isinstance(artifact, dict):
            continue
        meta = artifact.get("metadata") or {}
        a_type = str(meta.get("type") or "").lower()
        if a_type != "model":
            continue
        model_id_to_artifact[str(aid)] = artifact

    # Ensure root is included even if type is odd/missing
    if root_id not in model_id_to_artifact and isinstance(root_artifact, dict):
        model_id_to_artifact[str(root_id)] = root_artifact

    if not model_id_to_artifact:
        # No models at all; just return a trivial graph with the root.
        meta = root_artifact.get("metadata") or {}
        data = root_artifact.get("data") or {}
        root_node: Dict[str, Any] = {
            "artifact_id": str(meta.get("id") or root_id),
            "name": str(meta.get("name") or ""),
            "source": "metadata",
        }
        url = data.get("url")
        if isinstance(url, str) and url:
            root_node["metadata"] = {"repository_url": url}
        return {"nodes": [root_node], "edges": []}

    # ---- 2) Precompute config string sets for each model ----
    cfg_strings_map: Dict[str, Set[str]] = {}
    for mid, art in model_id_to_artifact.items():
        cfg = load_config_for_artifact(art)
        cfg_strings_map[mid] = _collect_strings(cfg) if isinstance(cfg, dict) else set()

    # ---- 3) Build nodes + edges globally ----
    nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []
    adjacency: Dict[str, Set[str]] = {mid: set() for mid in model_id_to_artifact}
    seen_edges: Set[Tuple[str, str]] = set()

    def add_node(mid: str, art: Dict[str, Any], source_hint: Optional[str] = None) -> None:
        meta = art.get("metadata") or {}
        data = art.get("data") or {}

        node_id = str(meta.get("id") or mid)
        name = str(meta.get("name") or "")
        version = str(meta.get("version") or "")

        # Prefer config_json if we actually have config-derived strings
        source = source_hint or ("config_json" if cfg_strings_map.get(mid) else "metadata")

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

        if mid in nodes:
            existing = nodes[mid]
            # Fill in any missing fields from the new node
            for k, v in node.items():
                if k not in existing or existing[k] in (None, "", {}):
                    existing[k] = v
        else:
            nodes[mid] = node

    # For each model as CHILD, find possible PARENTS
    for child_id, child_art in model_id_to_artifact.items():
        cfg_strings = cfg_strings_map.get(child_id) or set()

        cur_meta = child_art.get("metadata") or {}
        cur_name_norm = str(cur_meta.get("name") or "").strip().lower()

        # no strings => no lineage info for this child
        if not cfg_strings:
            continue

        possible_parents: List[Tuple[int, str, Dict[str, Any]]] = []

        for cand_id, cand_art in model_id_to_artifact.items():
            if cand_id == child_id:
                continue

            cand_meta = cand_art.get("metadata") or {}
            cand_name = cand_meta.get("name")
            cand_name_norm = cand_name.strip().lower() if isinstance(cand_name, str) else ""
            cand_id_norm = str(cand_meta.get("id") or cand_id).strip().lower()

            def token_in_cfg(token: str) -> bool:
                if not token:
                    return False
                for s in cfg_strings:
                    if token in s or s in token:
                        return True
                return False

            name_matches = cand_name_norm and token_in_cfg(cand_name_norm)
            id_matches = cand_id_norm and token_in_cfg(cand_id_norm)

            if not (name_matches or id_matches):
                continue

            # Heuristic scoring to prefer "obvious" parents:
            # - name is substring of child's name: strongest
            # - otherwise any name match
            # - otherwise id match
            score = 0
            if cand_name_norm and cur_name_norm and cand_name_norm in cur_name_norm:
                score = 3
            elif name_matches:
                score = 2
            elif id_matches:
                score = 1

            possible_parents.append((score, cand_id, cand_art))

        if not possible_parents:
            continue

        # Sort parents by score desc, then id for determinism
        possible_parents.sort(key=lambda t: (-t[0], t[1]))

        # Include *all* matching parents (keeps tests happy if multiple)
        for _, parent_id, parent_art in possible_parents:
            edge_key = (parent_id, child_id)
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)

            add_node(child_id, child_art)
            add_node(parent_id, parent_art)

            edges.append(
                {
                    "from_node_artifact_id": parent_id,
                    "to_node_artifact_id": child_id,
                    "relationship": "base_model",
                }
            )
            adjacency[parent_id].add(child_id)
            adjacency[child_id].add(parent_id)

    # If we couldn't infer any relationships at all, fall back to a single-node graph.
    if not edges:
        add_node(root_id, root_artifact)
        return {
            "nodes": [nodes[root_id]],
            "edges": [],
        }

    # ---- 4) Restrict to the connected component containing root_id ----
    # Make sure root exists in maps
    if root_id not in model_id_to_artifact:
        model_id_to_artifact[root_id] = root_artifact
    add_node(root_id, model_id_to_artifact[root_id])

    visited: Set[str] = set()
    queue: List[str] = [root_id]

    while queue:
        cur = queue.pop(0)
        if cur in visited:
            continue
        visited.add(cur)
        for nb in adjacency.get(cur, []):
            if nb not in visited:
                queue.append(nb)

    final_nodes = [node for mid, node in nodes.items() if mid in visited]
    final_edges = [
        e for e in edges
        if e["from_node_artifact_id"] in visited and e["to_node_artifact_id"] in visited
    ]

    return {
        "nodes": final_nodes,
        "edges": final_edges,
    }