from huggingface_hub import HfApi
import requests
from urllib.parse import urlparse


def normalize_hf_url(url: str) -> str:
    """
    Normalize Hugging Face URLs and allow single-segment repos.
    """
    if url.startswith("hf://"):
        return "https://huggingface.co/" + url[len("hf://"):]

    parsed = urlparse(url)

    if parsed.netloc != "huggingface.co":
        raise ValueError("Invalid repository URL: must point to huggingface.co")

    path = parsed.path.strip("/")
    if path == "":
        raise ValueError("Invalid repository URL: missing path")

    return f"https://huggingface.co/{path}"


def split_hf_repo(parts):
    """
    Correctly split Hugging Face repo paths.
    Handles:
      ["repo"]
      ["owner", "repo"]
      ["datasets", "repo"]
      ["datasets", "owner", "repo"]
    Returns (owner, repo, repo_id)
    """

    # Case 1: single-segment repo
    if len(parts) == 1:
        repo = parts[0]
        return None, repo, repo   # repo_id = repo

    # Case 2: datasets/<repo>
    if parts[0] == "datasets":
        if len(parts) == 2:
            repo = parts[1]
            return None, repo, repo
        else:
            owner, repo = parts[1], parts[2]
            return owner, repo, f"{owner}/{repo}"

    # Case 3: normal owner/repo
    owner, repo = parts[0], parts[1]
    return owner, repo, f"{owner}/{repo}"


def get_artifact_size(url: str, artifact_type: str) -> int:
    """
    Returns artifact size in bytes.
    Now correctly supports single-segment HF repos.
    """

    # Normalize if model
    if "huggingface.co" in url:
        url = normalize_hf_url(url)

    parsed = urlparse(url)
    host = parsed.netloc
    parts = parsed.path.strip("/").split("/")

    # HuggingFace
    if host == "huggingface.co":
        api = HfApi()

        owner, repo, repo_id = split_hf_repo(parts)

        if artifact_type == "dataset":
            info = api.dataset_info(repo_id, files_metadata=True)
        else:
            info = api.model_info(repo_id, files_metadata=True)


        if not info.siblings:
            raise ValueError("No files found in repository")

        return sum(f.size for f in info.siblings if f.size)

    # GitHub
    if host == "github.com":
        owner, repo = parts[0], parts[1]
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        r = requests.get(api_url, timeout=5)
        r.raise_for_status()
        data = r.json()
        return data["size"] / 1024   # GitHub reports KB → bytes

    raise ValueError("Unsupported host (must be GitHub or Hugging Face)")
