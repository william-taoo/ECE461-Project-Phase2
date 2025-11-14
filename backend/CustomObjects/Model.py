import concurrent.futures
import math
from typing import Dict, Any, Tuple, Callable, Optional
from CustomObjects.Dataset import Dataset
from CustomObjects.Code import Code
from CustomObjects.LLMQuerier import LLMQuerier
from collections import Counter
from datetime import datetime, timedelta
import re
from huggingface_hub import HfApi, list_repo_commits
from urllib.parse import urlparse
import time
import os
import subprocess
import tempfile
import requests
import networkx as nx
import json
import matplotlib.pyplot as plt

class Model:
    url: str
    name: str
    category: str
    size_score: Dict[str, float]
    license_score: float
    ramp_up_time: float
    bus_factor: float
    dataset: Dataset
    code: Code
    performance_claims: float
    dataset_and_code_score: float
    net_score: float

    size_score_latency: int
    license_latency: int
    ramp_up_time_latency: int
    bus_factor_latency: int
    performance_claims_latency: int
    dataset_and_code_score_latency: int
    dataset_quality_latency: int
    code_quality_latency: int
    net_score_latency: int

    def __init__(self, model_url: str, dataset_url: str, code_url: str) -> None:
        self.url = model_url
        self.dataset_url = dataset_url
        self.code_url = code_url
        self.name = self.get_name()
        self.category = ''
        self.size_score = {}
        self.license_score = 0.0
        self.ramp_up_time = 0.0
        self.bus_factor = 0.0
        self.dataset = Dataset(dataset_url, model_url) #Contains dataset quality and availability scores
        self.code = Code(code_url) #Contains code quality and availability scores
        self.performance_claims = 0.0
        self.dataset_and_code_score = 0.0
        self.reproducibility = 0.0
        self.reviewedness = 0.0
        self.treescore = 0.0
        self.net_score = 0.0

        self.size_score_latency = 0
        self.license_latency = 0
        self.ramp_up_time_latency = 0
        self.bus_factor_latency = 0
        self.performance_claims_latency = 0
        self.dataset_and_code_score_latency = 0
        self.dataset_quality_latency = 0
        self.code_quality_latency = 0
        self.reproducibility_latency = 0
        self.reviewedness_latency = 0
        self.treescore_latency = 0
        self.net_score_latency = 0


    def get_name(self) -> str:
        """
        Extracts the model name from the URL.
        Returns:
            a string name, or 'unknown-name' if it cannot be determined.
        """
        try:
            parsed_url = urlparse(self.url)
            path_parts = parsed_url.path.strip('/').split('/')
            if len(path_parts) >= 2:
                return path_parts[1]
        except Exception:
            return 'unknown-name'
        return 'unknown-name'

    def get_category(self) -> str:
        if self.url:
            return 'MODEL'
        elif self.dataset_url:
            return 'DATASET'
        elif self.code_url:
            return 'CODE'
        return 'unknown-category'

    def time_metric(self, metric_func: Callable[..., Any], *args: Any, **kwargs: Any) -> Tuple[Any, int]:
        """
        Measure the time taken by a metric function.
        Args:
            metric_func: The metric function to be timed.
            *args: Positional arguments to pass to the metric function.
            **kwargs: Keyword arguments to pass to the metric function.
        Returns:
            A tuple of (result, latency_ms)
        """
        # Return latency of metric functions
        start_time = time.perf_counter()
        result = metric_func(*args, **kwargs)
        end_time = time.perf_counter()
        latency_ms = round((end_time - start_time) * 1000)

        return result, latency_ms

    def get_size(self) -> Dict[str, float]:
        """
        Get the size scores for different devices based on the model's file sizes.
        Returns:
            A dictionary mapping device names to their size scores.
        """
        thresholds: Dict[str, int] = {
            'raspberry_pi': 1 * 1024**3,  # 1 GB
            'jetson_nano': 2 * 1024**3,   # 2 GB
            'desktop_pc': 16 * 1024**3,   # 16 GB
            'aws_server': float('inf')    # no limit
        }
        scores: Dict[str, float] = {}

        try:
            # Parse the URL to get the repository ID
            path_parts = urlparse(self.url).path.strip('/').split('/')
            if len(path_parts) < 2:
                return {}
            repo_id = f"{path_parts[0]}/{path_parts[1]}"

            # Use the HfApi to get model info, which includes file sizes
            api = HfApi()
            model_info = api.model_info(repo_id=repo_id, files_metadata=True)

            # Sum the size of all files in the repository
            total_size = sum(file.size for file in model_info.siblings if file.size is not None)

            # Calculate scores based on the total size
            for device, threshold in thresholds.items():

                if device == 'aws_server':
                    scores[device] = 1.0
                    continue

                if total_size <= threshold:
                    scores[device] = 1.0
                else:
                    # Score decreases linearly to 0 as size approaches 2*threshold
                    score = (2 * threshold - total_size) / threshold
                    scores[device] = max(0.0, score)

            return scores
        except Exception as e:
            return {}


    def get_license(self) -> float:
        """
        Get the license score for the model.
        Returns:
            A float representing the license score (1.0 for compatible licenses, 0.0 otherwise).
        """
        compatible_licenses = ['mit', 'bsd', 'lgpl', 'apache-2.0']
        # Use the HfApi to fetch only the README file
        api = HfApi()

        # Parse the URL to get the repository ID
        path_parts = urlparse(self.url).path.strip('/').split('/')
        if len(path_parts) < 2:
            return 0.0
        repo_id = f"{path_parts[0]}/{path_parts[1]}"

        try:
            model_info = api.model_info(repo_id)
            if model_info.cardData and "license" in model_info.cardData and model_info.cardData["license"].lower() in compatible_licenses:
                return 1.0
            else:
                return 0.0
        except Exception as e:
            pass

        # 1. First, try to find and check a dedicated LICENSE file.
        try:
            license_filepath = api.hf_hub_download(
                repo_id=repo_id,
                filename="LICENSE",
                repo_type="model" # Explicitly state repo type
            )
            with open(license_filepath, 'r', encoding='utf-8') as f:
                license_content = f.read().lower()

            for lic in compatible_licenses:
                if lic in license_content:
                    print("Found compatible license in LICENSE file.")
                    return 1.0

        except Exception as e:
            pass

        # 2. If no LICENSE file, fall back to checking the README for a License section.
        readme_filepath = api.hf_hub_download(repo_id=repo_id, filename="README.md")
        with open(readme_filepath, 'r', encoding='utf-8') as f:
            readme_content = f.read()

        # Find the 'License' section in the fetched content
        match = re.search(r'^#+\s*license\s*$', readme_content, re.IGNORECASE | re.MULTILINE)

        if not match:
            return 0.0

        start_index = match.end()
        next_heading_match = re.search(r'^#+', readme_content[start_index:], re.MULTILINE)

        if next_heading_match:
            end_index = start_index + next_heading_match.start()
            license_text = readme_content[start_index:end_index].lower()
        else:
            license_text = readme_content[start_index:].lower()

        for lic in compatible_licenses:
            if lic in license_text:
                return 1.0

        return 0.0

    def get_popularity_score(self) -> float:
        """
        Get the popularity score for the model.
        Returns:
            A float representing the popularity score (1.0 for high popularity, 0.0 for low popularity).
        """
        try:
            path_parts = urlparse(self.url).path.strip('/').split('/')
            if len(path_parts) < 2:
                return 0.0
            repo_id = f"{path_parts[0]}/{path_parts[1]}"

            api = HfApi()
            model_info = api.model_info(repo_id=repo_id)

            downloads = model_info.downloads or 0
            likes = model_info.likes or 0

            # Normalize scores on a logarithmic scale
            # A score of 1.0 is achieved at 1,000,000 downloads or 1,000 likes
            dwnlds = 100000
            lks = 1000
            download_score = min(1.0, math.log10(downloads + 1) / math.log10(dwnlds))
            like_score = min(1.0, math.log10(likes + 1) / math.log10(lks))

            # Weighted average of the two popularity metrics
            popularity_score = (0.7 * download_score) + (0.3 * like_score)
            return popularity_score

        except Exception as e:
            print(f"Could not fetch popularity info: {e}")
            return 0.0

    def get_ramp_up_time(self, api_key: str) -> float:
        """
        Calculates the ramp up time for a given hugging face model.

        The ramp up time is scored on a scale of 0.0 to 1.0, where 1.0 indicates
        that the model is very easy to get started with, and 0.0 indicates that the model
        is very difficult to get started using.

        Returns:
            A float score between 0.0 and 1.0. Returns 0.0 if the repository
            cannot be cloned or has no recent commits.
        """
        popularity_score = self.get_popularity_score()

        llm_querier = LLMQuerier(endpoint="https://genai.rcac.purdue.edu/api/chat/completions", api_key=api_key)
        prompt = (
            f"Assess the ramp-up time for using the model located at \"{self.url}\". Provide a score between 0 (very difficult) and 1 (very easy). "
            "Ramp up time refers to the time required for a new user to become productive with the model."
            "Calculate ramp-up time based on factors such as documentation quality and clarity, community support, and complexity of the model."
            "If the README or documentation contains only headers without meaningful text return a low score."
            "Provide only the numeric score as output, without any additional text or explanation."
        )
        response = llm_querier.query(prompt=prompt)

        llm_score = float(response) if response else 0.0

        # If we couldn't determine popularity (popularity_score == 0.0),
        # prefer the LLM-only score. This makes the metric usable when HF
        # metadata is unavailable or the API fails (tests typically mock
        # only the LLMQuerier).
        if popularity_score == 0.0:
            return float(llm_score)

        final_score = (0.8 * popularity_score) + (0.2 * llm_score)

        return float(final_score)

    def get_bus_factor(self) -> float:
        """
        Calculates the bus factor for a given Git repository.

        The bus factor is scored on a scale of 0.0 to 1.0. It is based on the
        number of "significant authors" (those with >5% of commits in the last
        year). A score of 1.0 is achieved if there are 5 or more such authors.

        Returns:
            A float score between 0.0 and 1.0. Returns 0.0 if the repository
            cannot be cloned or has no recent commits.
        """
        # Parse the URL to get the repository ID
        path_parts = urlparse(self.url).path.strip('/').split('/')
        if len(path_parts) < 2:
            return 0.0
        repo_id = f"{path_parts[0]}/{path_parts[1]}"

        try:
            # Instantiate the API client and fetch commits
            # api = HfApi()
            commits = list_repo_commits(repo_id=repo_id)

            # Define the time window (last 365 days)
            years = 2.5
            year_limit = datetime.now().astimezone() - timedelta(days=365*years)

            # Filter commits from the last year and get author names
            recent_authors = []
            for commit in commits:
                if commit.created_at > year_limit:
                    for author in commit.authors:
                        recent_authors.append(author)

            if not recent_authors:
                return 0.0

            total_commits = len(recent_authors)

            # Count commits per author
            commit_counts = Counter(recent_authors)

            # Identify significant authors (>4% of commits)
            percent_of_commits = 4.0
            significant_authors_count = 0
            for author, count in commit_counts.items():
                contribution_percentage = (count / total_commits) * 100
                if contribution_percentage > percent_of_commits:
                    significant_authors_count += 1

            # Calculate the final score (capped at 1.0)
            min_total_contributors = 5.0
            score = min(1.0, significant_authors_count / min_total_contributors)
            return score

        except Exception as e:
            return 0.0

    def get_performance_claims(self, api_key: str) -> float:
        """
        Calculates the performance-claims score for the model.

        Score is a single float in [0,1] returned by the LLM.
        The LLM is given the model URL and ask for a numeric-only assessment of how well
        performance/evaluation/benchmarks are documented.
        Returns:
            A float score between 0.0 and 1.0. Returns 0.0 if the repository
            cannot be cloned or has no recent commits.
        """
        llm_querier = LLMQuerier(
            endpoint="https://genai.rcac.purdue.edu/api/chat/completions",
            api_key=api_key,
        )
        prompt = (
            f"Assess the performance documentation for the model located at {self.url}."
            "Provide a score between 0 (no documentation) and 1 (clear, detailed documentation)."
            "Performance documentation refers to evaluation results, benchmarks, or metrics reported in the README."
            "Evaluation results will be in the form of tables, or charts under sections like 'Evaluation', 'Results', 'Benchmarks', or similar."
            "Provide only the numeric score as output, without any additional text or explanation."
        )
        response = llm_querier.query(prompt=prompt)

        if response is None:
            return 0.0

        try:
            return max(0.0, min(1.0, float(response)))
        except Exception:
            return 0.0
        
    def get_reproducibility(self) -> float: 
        """
        Calculates the reproducibility score for the model based on 
        demonstraton code included in the model card.

        The reproducibility is scored on a scale of 0.0 to 1.0. It is based on the
        presence of demo code in the model README. If there is no code or the code 
        doesn't run, the score is 0.0. If it runs, but encounters some error or 
        needs debugged, the score is 0.5. If it runs successfully with no errors, 
        the score is 1.0.

        Returns:
            A float score between 0.0 and 1.0.
        """

        self.reproducibility_score = 0.0
        api = HfApi()

        # parse the URL to get the repository ID
        path_parts = urlparse(self.url).path.strip('/').split('/')
        if len(path_parts) < 2:
            return 0.0
        repo_id = f"{path_parts[0]}/{path_parts[1]}"

        try:
            # extract model README
            readme_path = api.hf_hub_download(repo_id=repo_id, filename="README.md")
            with open(readme_path, "r", encoding="utf-8") as f:
                readme_text = f.read()

            # try to locate demo code in model card
            all_blocks = re.findall(r"```python(.*?)```", readme_text, re.DOTALL)
            if not all_blocks:
                return 0.0

            # filter out code blocks that aren't python
            valid_blocks = []
            for block in all_blocks:
                cleaned_lines = []
                for line in block.splitlines():
                    line = line.strip()
                    # only keep lines that *start* with >>> or ...
                    if re.match(r"^(>>>|\.\.\.)\s?", line):
                        # Remove the REPL prefix before adding
                        line = re.sub(r"^(>>>|\.\.\.)\s?", "", line)
                        cleaned_lines.append(line)
                cleaned = "\n".join(cleaned_lines).strip()

                # Keep code blocks that start with import/from
                if cleaned and re.match(r"^(import|from)\s+\w+", cleaned):
                    valid_blocks.append(cleaned)
            
            # return 0 if no valid demo code is found
            if not valid_blocks:
                return 0.0

            # run the first valid code block
            demo_code = valid_blocks[0].strip()
            
            # create a temp directory to test demo code
            with tempfile.TemporaryDirectory() as tmpdir:
                demo_file = os.path.join(tmpdir, "demo.py")
                with open(demo_file, "w", encoding="utf-8") as f:
                    f.write(demo_code)
                
                # try running the code (timeout after 60 seconds)
                try:
                    result = subprocess.run(
                        ["python3", demo_file],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    # ran successfully -> score = 1.0
                    if result.returncode == 0:
                        self.reproducibility_score = 1.0
                    
                    # run failure -> score = 0.5
                    else:
                        self.reproducibility_score = 0.5
                
                # timeout or other exception/runtime error -> score = 0.5
                except subprocess.TimeoutExpired:
                    self.reproducibility_score = 0.5
                except Exception as e:
                    self.reproducibility_score = 0.5

        # any other exception -> score = 0.0
        except Exception as e:
            self.reproducibility_score = 0.0

        return self.reproducibility_score

    def get_reviewedness(self) -> float:
        """
        Computes the reviewedness metric for the associated GitHub repository.

        Definition: fraction of all *code* (not weights) that was
        introduced via pull requests which had a code review. If there is no
        linked GitHub repository, return -1.0.
        """
        code_url = getattr(self, "code_url", None) or ""
        parsed = urlparse(code_url)
        if "github.com" not in (parsed.netloc or ""):
            return -1

        # get {owner}/{repo}
        try:
            parts = parsed.path.strip("/").split("/")
            owner, repo = parts[0], parts[1].replace(".git", "")
        except Exception:
            return -1.0
        
        session = requests.Session()
        token = os.getenv("GITHUB_TOKEN", "").strip()
        headers = {
            "Accept": "application/vnd.github+json",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        }

        # reviewedness specific helpers to decide whether a file counts as code instead of weights
        code_exts = {
            ".py", ".ipynb", ".js", ".ts", ".jsx", ".tsx",
            ".java", ".c", ".cc", ".cpp", ".h", ".hpp",
            ".go", ".rs", ".rb", ".swift", ".kt", ".m", ".mm",
            ".sh", ".ps1", ".r", ".jl",
            ".yml", ".yaml", ".json", ".toml", ".ini", ".cfg", ".mk",
            ".sql", ".pl"
        }
        non_code_or_weight_exts = {
            ".bin", ".safetensors", ".pt", ".pth", ".onnx",
            ".h5", ".ckpt", ".tflite", ".pb", ".weights",
            ".tar", ".gz", ".zip", ".xz", ".7z", ".rar",
            ".parquet", ".feather", ".arrow", ".npz", ".npy",
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp",
            ".pdf", ".docx", ".pptx", ".xls", ".xlsx",
            ".ipynb_checkpoints",
        }

        def is_code_file(fname: str) -> bool:
            f = fname.lower()
            if any(seg in f for seg in ("/weights/", "/checkpoints/", "/artifacts/", "/models/")):
                return False
            ext = "." + f.rsplit(".", 1)[-1] if "." in f else ""
            if ext in non_code_or_weight_exts:
                return False
            # treat files with a known code/config extension as code
            return ext in code_exts
        
        def get_paginated(url: str, params: dict):
            page = 1
            while True:
                p = {**params, "per_page": 100, "page": page}
                resp = session.get(url, headers=headers, params=p, timeout=15)
                if resp.status_code >= 400:
                    break
                data = resp.json()
                if not data:
                    break
                yield data
                if "link" not in resp.headers or 'rel="next"' not in resp.headers["link"]:
                    break
                page += 1

        base_url = f"https://api.github.com/repos/{owner}/{repo}"
        merged_pr_numbers = []
        try:
            for page in get_paginated(f"{base_url}/pulls", {"state": "closed", "sort": "updated", "direction": "desc"}):
                for pr in page:
                    # pr['merged_at'] present means it was merged
                    if pr.get("merged_at"):
                        merged_pr_numbers.append(pr["number"])
                    # Stop after a reasonable cap to keep runtime bounded
                if len(merged_pr_numbers) >= 400:
                    break
        except Exception:
            return 0.0
        
        if not merged_pr_numbers: # nothing introduced via reviewed PRs
            return 0.0
    
        total_code_additions = 0
        reviewed_code_additions = 0

        # for each merged PR, check reviews and count code additions
        for pr_number in merged_pr_numbers:
            try:
                # look for approved review
                rev_ok = False
                rev_resp = session.get(f"{base_url}/pulls/{pr_number}/reviews", headers=headers, timeout=15)
                if rev_resp.status_code < 400:
                    for r in rev_resp.json():
                        # States: COMMENTED, APPROVED, CHANGES_REQUESTED, DISMISSED
                        if (r.get("state") or "").upper() == "APPROVED":
                            rev_ok = True
                            break
                # add up additions for code files
                pr_files_additions = 0
                for page in get_paginated(f"{base_url}/pulls/{pr_number}/files", {}):
                    for f in page:
                        fname = f.get("filename") or ""
                        if is_code_file(fname):
                            # additions field counts added lines in that file within the PR
                            pr_files_additions += int(f.get("additions") or 0)
                total_code_additions += pr_files_additions
                if rev_ok:
                    reviewed_code_additions += pr_files_additions    

            except Exception:
                continue
        
        if total_code_additions <= 0:
            return 0.0
        
        reviewedness = reviewed_code_additions / float(total_code_additions)
        return max(0.0, min(1.0, reviewedness))

    def get_treescore(self) -> float:
        try:
            g = self.get_lineage_graph()
            if g is None:
                return 0.0

            # Parents are direct predecessors of this node
            parts = urlparse(self.url).path.strip("/").split("/")
            if len(parts) < 2:
                return 0.0
            this_node = f"{parts[0]}/{parts[1]}"

            if this_node not in g:
                return 0.0

            parents = list(g.predecessors(this_node))
            if not parents:
                return 0.0

            parents = parents[:5]

            api_key = os.getenv("API_KEY", "")

            scores: list[float] = []
            for parent_repo in parents:
                # Only score real HF repos, skip architecture tags
                if not self._looks_like_hf_repo(parent_repo):
                    continue

                parent_url = self._to_hf_url(parent_repo)

                try:
                    # Compute child's net score but disable its own TreeScore to avoid recursion
                    parent_model = Model(parent_url, dataset_url="", code_url="")
                    parent_model.get_treescore = lambda: 0.0  # type: ignore[attr-defined]
                    s = float(parent_model.compute_net_score(api_key=api_key))
                    if 0.0 <= s <= 1.0:
                        scores.append(s)
                except Exception:
                    continue

            if not scores:
                return 0.0

            return self._clip01(sum(scores) / len(scores))
        except Exception:
            return 0.0
    
    # Treescore helper functions
    def _clip01(self, x: float) -> float:
        try:
            return max(0.0, min(1.0, float(x)))
        except Exception:
            return 0.0
        
    def _looks_like_hf_repo(self, s: str) -> bool:
        s = (s or "").strip()
        if not s:
            return False
        if "/" in s:
            left, right = s.split("/", 1)
            return bool(left) and bool(right) and all(ch not in right for ch in ("\\", " ", "\t"))
        return "-" in s and " " not in s and "\\" not in s and "/" not in s

    def _to_hf_url(self, repo_id: str) -> str:
        return f"https://huggingface.co/{repo_id.strip()}"

    def _extract_parent_repo_ids_from_config(self, cfg: dict) -> list[str]:
        """
        Pull likely upstream model ids from HF-style config.json.
        This is heuristic but covers the most common fields used by adapters/merges/finetunes.
        """
        candidates: set[str] = set()

        for k in [
            "base_model_name_or_path",
            "base_model",
            "init_model_name_or_path",
            "peft_base_model_id",
            "merge_base_model",
            "source_model", "teacher_model_name_or_path",
            "vision_model_name_or_path", "text_model_name_or_path",
            "llm_model_name_or_path", "model_id",
            "adapter_model_name_or_path",
            "tokenizer_name_or_path",
        ]:
            v = cfg.get(k)
            if isinstance(v, str) and self._looks_like_hf_repo(v):
                candidates.add(v)

        for k in [
            "merge_base_models", "parent_models", "source_models",
            "model_fusion_sources", "models_to_merge",
        ]:
            v = cfg.get(k)
            if isinstance(v, (list, tuple)):
                for item in v:
                    if isinstance(item, str) and self._looks_like_hf_repo(item):
                        candidates.add(item)

        peft_cfg = cfg.get("peft_config") or cfg.get("peft")
        if isinstance(peft_cfg, dict):
            for k in ["base_model_name_or_path", "target_model", "model_id"]:
                v = peft_cfg.get(k)
                if isinstance(v, str) and self._looks_like_hf_repo(v):
                    candidates.add(v)

        # 4) Fallthrough: architectures/model_type are *architectures*, not parents; skip
        return list(candidates)

    def get_lineage_graph(self) -> Optional[nx.DiGraph]:
        self.lineage_graph = None
        api = HfApi()

        parts = urlparse(self.url).path.strip("/").split("/")
        if len(parts) < 2:
            return None
        repo_id = f"{parts[0]}/{parts[1]}"

        try:
            cfg_path = api.hf_hub_download(repo_id=repo_id, filename="config.json")
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            return None

        g: nx.DiGraph = nx.DiGraph()
        this_node = repo_id  # use canonical "org/name" when possible
        g.add_node(this_node)

        # Parents we can actually score
        parent_ids = self._extract_parent_repo_ids_from_config(cfg)
        for p in parent_ids:
            g.add_node(p)
            g.add_edge(p, this_node)

        # (Optional) include architecture hint as a weak parent when no explicit bases exist
        if not parent_ids:
            model_type = cfg.get("model_type")
            if isinstance(model_type, str) and model_type.strip():
                arch_node = f"ARCH::{model_type.strip().lower()}"
                g.add_node(arch_node)
                g.add_edge(arch_node, this_node)

        self.lineage_graph = g
        return self.lineage_graph

    def get_dataset_and_code_score(self) -> float:
        """
        Calculates the dataset and code availability score for the model.
        Returns:
            A float score between 0.0 and 1.0 representing the average of
            dataset_availability and code_availability.
        """
        dataset_availability = getattr(self.dataset, 'dataset_availability', 0.0)
        code_availability = getattr(self.code, 'code_availability', 0.0)

        return (dataset_availability + code_availability) / 2.0


    def compute_net_score(self, api_key: str) -> float:
        """
        Computes the net score for the model by aggregating various metrics.
        Returns:
            A float score between 0.0 and 1.0 representing the net score.
        """
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_size = executor.submit(self.time_metric, self.get_size)
            future_license = executor.submit(self.time_metric, self.get_license)
            future_ramp_up_time = executor.submit(self.time_metric, self.get_ramp_up_time, api_key=api_key)
            future_bus_factor = executor.submit(self.time_metric, self.get_bus_factor)
            future_performance_claims = executor.submit(self.time_metric, self.get_performance_claims, api_key=api_key)
            future_dataset_quality = executor.submit(self.time_metric, self.dataset.get_quality, api_key=api_key)
            future_code_quality = executor.submit(self.time_metric, self.code.get_quality)
            future_dataset_and_code_score = executor.submit(self.time_metric, self.get_dataset_and_code_score)
            future_reproducibility = executor.submit(self.time_metric, self.get_reproducibility)
            future_reviewedness = executor.submit(self.time_metric, self.get_reviewedness)
            future_treescore = executor.submit(self.time_metric, self.get_treescore)

            self.size_score, self.size_score_latency = future_size.result()
            self.license_score, self.license_latency = future_license.result()
            self.ramp_up_time, self.ramp_up_time_latency = future_ramp_up_time.result()
            self.bus_factor, self.bus_factor_latency = future_bus_factor.result()
            self.performance_claims, self.performance_claims_latency = future_performance_claims.result()
            self.dataset.quality, self.dataset_quality_latency = future_dataset_quality.result()
            self.code.quality, self.code_quality_latency = future_code_quality.result()
            self.dataset_and_code_score, self.dataset_and_code_score_latency = future_dataset_and_code_score.result()
            self.reproducibility, self.reproducibility_latency = future_reproducibility.result()
            self.reviewedness, self.reviewedness_latency = future_reviewedness.result()
            self.treescore, self.treescore_latency = future_treescore.result()

        if self.reviewedness is None or float(self.reviewedness) < 0.0:
            self.reviewedness = 0.0
        if self.treescore is None:
            self.treescore = 0.0

        # Example weights, can be adjusted based on importance
        weights: Dict[str, float] = {
            "license": 0.25,
            "ramp_up_time": 0.30,
            "bus_factor": 0.10,
            "dataset_quality": 0.095,
            "code_quality": 0.005,
            "performance_claims": 0.20,
            "dataset_and_code_score": 0.05,
            "reproducibility": 0.08,
            "reviewedness": 0.04,
            "treescore": 0.02,
        }

        self.net_score = (
            weights['license'] * self.license_score +
            weights['ramp_up_time'] * self.ramp_up_time +
            weights['bus_factor'] * self.bus_factor +
            weights['dataset_quality'] * self.dataset.quality +
            weights['code_quality'] * self.code.quality +
            weights['performance_claims'] * self.performance_claims +
            weights['dataset_and_code_score'] * self.dataset_and_code_score +
            weights['reproducibility'] * self.reproducibility +
            weights['reviewedness'] * self.reviewedness +
            weights['treescore'] * self.treescore
        )

        self.net_score_latency = (
            self.size_score_latency +
            self.license_latency +
            self.ramp_up_time_latency +
            self.bus_factor_latency +
            self.performance_claims_latency +
            self.dataset_quality_latency +
            self.code_quality_latency +
            self.dataset_and_code_score_latency +
            self.reproducibility_latency +
            self.reviewedness_latency +
            self.treescore_latency
        )

        return self.net_score