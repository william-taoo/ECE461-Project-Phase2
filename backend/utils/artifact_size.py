from huggingface_hub import HfApi
import requests
from urllib.parse import urlparse

def get_artifact_size(url: str, artifact_type: str) -> int:
    """
    Returns artifact size in bytes.
    Supports Hugging Face models + datasets and GitHub repos.
    """

    # deconstruct URL
    parsed = urlparse(url)
    host = parsed.netloc
    parts = parsed.path.strip("/").split("/")

    if len(parts) < 2:
        raise ValueError("Invalid repository URL")

    # Hugging Face models and datasets
    if "huggingface.co" in host:
        api = HfApi()

        # check if dataset
        if parts[0] == "datasets" and artifact_type == "dataset":
            if len(parts) < 3:
                raise ValueError("Invalid HF dataset URL")
            owner, repo = parts[1], parts[2]
            info = api.dataset_info(repo_id=f"{owner}/{repo}", files_metadata=True)
            files = info.siblings

        # check if code
        elif artifact_type == "model":
            owner, repo = parts[0], parts[1]
            info = api.model_info(repo_id=f"{owner}/{repo}", files_metadata=True)
            files = info.siblings
        
        else:
            raise ValueError("Hugging Face artifact not dataset or model")

        if files:
            total_size = sum(f.size for f in files if f.size)
            return total_size
        else:
            raise ValueError("Could not get files")

    # GitHub
    if "github.com" in host:
        owner, repo = parts[0], parts[1]
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        r = requests.get(api_url, timeout=5)
        r.raise_for_status()
        data = r.json()

        if "size" not in data:
            raise ValueError("Could not determine size from GitHub API")

        # GitHub size = KB, return bytes
        return data["size"] / 1024

    raise ValueError("Unsupported host (must be GitHub or Hugging Face)")