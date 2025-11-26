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


def normalize_github_url(url: str) -> str:
    # Remove .git
    if url.endswith(".git"):
        url = url[:-4]

    # Normalize structure
    url = url.replace("git@", "").replace("https://", "").replace("http://", "")
    url = url.replace("github.com:", "github.com/")

    # Split after github.com/
    parts = url.split("github.com/")[1].split("/")

    owner = parts[0]
    repo = parts[1]

    # Ignore branch paths / tree / blob / main / folder etc.
    return f"https://api.github.com/repos/{owner}/{repo}"


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


def is_unset(value):
    return type(value).__name__ == "_Unset"


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

        total = 0
        for f in info.siblings:
            size = f.size
            if size is None or is_unset(size):
                continue
            total += size
        return total

    # GitHub
    if host == "github.com":
        api_url = normalize_github_url(url)
        r = requests.get(api_url, timeout=5)
        r.raise_for_status()
        data = r.json()
        return data["size"] / 1024   # GitHub reports KB → bytes

    # return 0 if unsupported type (not GitHub or Hugging Face)
    return 0
