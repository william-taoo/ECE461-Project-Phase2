from huggingface_hub import HfApi
import requests
from urllib.parse import urlparse
import os
import time

def normalize_hf_url(url: str) -> str:
    if url.startswith("hf://"):
        return "https://huggingface.co/" + url[len("hf://"):]
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if not host.endswith("huggingface.co"):
        raise ValueError("Invalid repository URL: must point to huggingface.co")
    path = parsed.path.strip("/")
    if not path:
        raise ValueError("Invalid repository URL: missing path")
    return f"https://huggingface.co/{path}"

def normalize_github_url(url: str) -> str:
    if url.endswith(".git"):
        url = url[:-4]
    url = url.replace("git@", "").replace("https://", "").replace("http://", "")
    url = url.replace("github.com:", "github.com/")
    parts = url.split("github.com/")[1].split("/")
    owner = parts[0]
    repo = parts[1]
    return f"https://api.github.com/repos/{owner}/{repo}"

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

def is_unset(value):
    return value is None

def get_artifact_size(url: str, artifact_type: str) -> int:
    """
    Returns the total size in bytes of a Hugging Face or GitHub repository.
    """
    # Hugging Face
    if "huggingface.co" in url:
        url = normalize_hf_url(url)
        parsed = urlparse(url)
        parts = parsed.path.strip("/").split("/")
        api = HfApi()
        owner, repo, repo_id = split_hf_repo(parts)
        total = 0
        try:
            if artifact_type == "dataset":
                info = api.dataset_info(repo_id, files_metadata=True)
            else:
                info = api.model_info(repo_id, files_metadata=True)
            for f in info.siblings or []:
                size = getattr(f, "size", 0)
                if is_unset(size):
                    continue
                total += size
            return total
        except Exception:
            return 0

    # GitHub
    if "github.com" in url:
        api_url = normalize_github_url(url)
        headers = {}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        retries = 3
        for attempt in range(retries):
            try:
                r = requests.get(api_url, headers=headers, timeout=10)
                r.raise_for_status()
                data = r.json()
                return int(data.get("size", 0)) * 1024  # KB → bytes
            except requests.exceptions.HTTPError as e:
                if r.status_code == 403 and attempt < retries - 1:
                    time.sleep(2 ** attempt)  # exponential backoff
                    continue
                raise
            except Exception:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return 0

    return 0
