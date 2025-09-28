import concurrent.futures
from typing import Dict, Any, Tuple, Callable
from CustomObjects.Dataset import Dataset
from CustomObjects.Code import Code
from CustomObjects.LLMQuerier import LLMQuerier
from collections import Counter
from datetime import datetime, timedelta
import re
from huggingface_hub import HfApi, list_repo_commits
from urllib.parse import urlparse
import time

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
        self.name = ''
        self.category = ''
        self.size_score = {}
        self.license_score = 0.0
        self.ramp_up_time = 0.0
        self.bus_factor = 0.0
        self.dataset = Dataset(dataset_url, model_url) #Contains dataset quality and availability scores
        self.code = Code(code_url) #Contains code quality and availability scores
        self.performance_claims = 0.0
        self.dataset_and_code_score = 0.0
        self.net_score = 0.0

        self.size_score_latency = 0
        self.license_latency = 0
        self.ramp_up_time_latency = 0
        self.bus_factor_latency = 0
        self.performance_claims_latency = 0
        self.dataset_and_code_score_latency = 0
        self.dataset_quality_latency = 0
        self.code_quality_latency = 0
        self.net_score_latency = 0

    def get_name(self) -> str:
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
    
    def _time_metric(self, metric_func: Callable[..., Any], *args: Any, **kwargs: Any) -> Tuple[Any, int]:
        # Return latency of metric functions
        start_time = time.perf_counter()
        result = metric_func(*args, **kwargs)
        end_time = time.perf_counter()
        latency_ms = round((end_time - start_time) * 1000)
        return result, latency_ms

    def get_size(self) -> Dict[str, float]:
        thresholds: Dict[str, int] = {
            'raspberry_pi': 1 * 1024**3,  # 1 GB
            'jetson_nano': 2 * 1024**3,   # 2 GB
            'desktop_pc': 16 * 1024**3,  # 16 GB
            'aws_server': float('inf')       # no limit
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
        llm_querier = LLMQuerier(endpoint="https://genai.rcac.purdue.edu/api/chat/completions", api_key=api_key)
        prompt = (
            f"Assess the ramp-up time for using the model located at {self.url}. Provide a score between 0 (very difficult) and 1 (very easy). "
            "Ramp up time refers to the time required for a new user to become productive with the model."
            "Calculate ramp-up time based on factors such as documentation quality and clarity, community support, and complexity of the model."
            "Provide only the numeric score as output, without any additional text or explanation."
        )
        response = llm_querier.query(prompt=prompt)

        if response is None:
            return 0.0

        return float(response)

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
            return {}
        repo_id = f"{path_parts[0]}/{path_parts[1]}"

        try:
            # 1. Instantiate the API client and fetch commits
            api = HfApi()
            commits = list_repo_commits(repo_id=repo_id)
            
            # 2. Define the time window (last 365 days)
            years = 2.5
            year_limit = datetime.now().astimezone() - timedelta(days=365*years)
            
            # 3. Filter commits from the last year and get author names
            recent_authors = []
            for commit in commits:
                if commit.created_at > year_limit:
                    for author in commit.authors:
                        recent_authors.append(author)
            
            if not recent_authors:
                return 0.0
                
            total_commits = len(recent_authors)
            
            # 4. Count commits per author
            commit_counts = Counter(recent_authors)
            
            # 5. Identify significant authors (>4% of commits)
            percent_of_commits = 4.0
            significant_authors_count = 0
            for author, count in commit_counts.items():
                contribution_percentage = (count / total_commits) * 100
                if contribution_percentage > percent_of_commits:
                    significant_authors_count += 1

            # 6. Calculate the final score (capped at 1.0)
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
        """
        llm_querier = LLMQuerier(
            endpoint="https://genai.rcac.purdue.edu/api/chat/completions",
            api_key=api_key,
        )
        prompt = (
            f"Assess the performance documentation for the model located at {self.url}. "
            "Provide a score between 0 (no documentation) and 1 (clear, detailed documentation)."
            "Performance documentation refers to evaluation results, benchmarks, or metrics reported in the README. "
            "Provide only the numeric score as output, without any additional text or explanation."
        )
        response = llm_querier.query(prompt=prompt)

        if response is None:
            return 0.0

        try:
            return max(0.0, min(1.0, float(response)))
        except Exception:
            return 0.0

    def get_dataset_and_code_score(self) -> float:
        """
        Averages the dataset and code availability scores.

        """
        dataset_availability = getattr(self.dataset, 'dataset_availability', 0.0)
        code_availability = getattr(self.code, 'code_availability', 0.0)
        
        return (dataset_availability + code_availability) / 2.0


    def compute_net_score(self, api_key: str) -> float:

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_size = executor.submit(self._time_metric, self.get_size)
            future_license = executor.submit(self._time_metric, self.get_license)
            future_ramp_up_time = executor.submit(self._time_metric, self.get_ramp_up_time, api_key=api_key)
            future_bus_factor = executor.submit(self._time_metric, self.get_bus_factor)
            future_performance_claims = executor.submit(self._time_metric, self.get_performance_claims, api_key=api_key)
            future_dataset_quality = executor.submit(self._time_metric, self.dataset.get_quality, api_key=api_key)
            future_code_quality = executor.submit(self._time_metric, self.code.get_quality)
            future_dataset_and_code_score = executor.submit(self._time_metric, self.get_dataset_and_code_score)

            self.size_score, self.size_score_latency = future_size.result()
            self.license_score, self.license_latency = future_license.result()
            self.ramp_up_time, self.ramp_up_time_latency = future_ramp_up_time.result()
            self.bus_factor, self.bus_factor_latency = future_bus_factor.result()
            self.performance_claims, self.performance_claims_latency = future_performance_claims.result()
            self.dataset.quality, self.dataset_quality_latency = future_dataset_quality.result()
            self.code.quality, self.code_quality_latency = future_code_quality.result()
            self.dataset_and_code_score, self.dataset_and_code_score_latency = future_dataset_and_code_score.result()

        # Example weights, can be adjusted based on importance
        weights: Dict[str, float] = {
            'license': 0.25,
            'ramp_up_time': 0.30,
            'bus_factor': 0.10,
            'dataset_quality': 0.095,
            'code_quality': 0.005,
            'performance_claims': 0.20,
            'dataset_and_code_score': 0.05
        }

        self.net_score = (
            weights['license'] * self.license_score +
            weights['ramp_up_time'] * self.ramp_up_time +
            weights['bus_factor'] * self.bus_factor +
            weights['dataset_quality'] * self.dataset.quality +
            weights['code_quality'] * self.code.quality +
            weights['performance_claims'] * self.performance_claims +
            weights['dataset_and_code_score'] * self.dataset_and_code_score
        )

        self.net_score_latency = (
            self.size_score_latency +
            self.license_latency +
            self.ramp_up_time_latency +
            self.bus_factor_latency +
            self.performance_claims_latency +
            self.dataset_quality_latency +
            self.code_quality_latency +
            self.dataset_and_code_score_latency
        )

        return self.net_score