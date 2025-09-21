import concurrent.futures
from typing import Dict, Optional
from CustomObjects.Dataset import Dataset
from CustomObjects.Code import Code
from CustomObjects.LLMQuerier import LLMQuerier
import git
import tempfile
from collections import Counter
from datetime import datetime, timedelta
import os
import re
from huggingface_hub import HfApi
from huggingface_hub.utils import HfHubHTTPError
from urllib.parse import urlparse

class Model:
    url: str
    size_score: Dict[str, float]
    license: float
    ramp_up_time: float
    bus_factor: float
    dataset: Dataset
    code: Code
    performance_claims: float
    net_score: float

    def __init__(self, model_url: str, dataset_url: str, code_url: str) -> None:
        self.url = model_url
        self.size_score = {}
        self.license = 0.0
        self.ramp_up_time = 0.0
        self.bus_factor = 0.0
        self.dataset = Dataset(dataset_url) #Contains dataset quality and availability scores
        self.code = Code(code_url) #Contains code quality and availability scores
        self.performance_claims = 0.0
        self.net_score = 0.0

    def get_size(self) -> Dict[str, float]:
        thresholds: Dict[str, int] = {
            'raspberry_pi': 1 * 1024**3,  # 1 GB
            'jetson_nano': 4 * 1024**3,   # 4 GB
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
            model_info = api.model_info(repo_id=repo_id)

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
            print(f"An unexpected error occurred while fetching the model size: {e}")
            return {}
    
    
    def get_license(self) -> float:
        compatible_licenses = ['mit', 'bsd', 'lgpl']
        
        # Parse the URL to get the repository ID
        path_parts = urlparse(self.url).path.strip('/').split('/')
        if len(path_parts) < 2:
            return 0.0
        repo_id = f"{path_parts[0]}/{path_parts[1]}"
        
        # Use the HfApi to fetch only the README file
        api = HfApi()
        readme_filepath = api.hf_hub_download(repo_id=repo_id, filename="README.md")
        with open(readme_filepath, 'r', encoding='utf-8') as f:
            readme_content = f.read()
            print(readme_content)

        # Find the 'License' section in the fetched content
        match = re.search(r'^#+\s*license\s*$', readme_content, re.IGNORECASE | re.MULTILINE)
        
        if not match:
            print("No license section found in README.")
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
    
    def get_ramp_up_time(self) -> float:
        """
        Calculates the ramp up time for a given hugging face model.

        The ramp up time is scored on a scale of 0.0 to 1.0, where 1.0 indicates
        that the model is very easy to get started with, and 0.0 indicates that the model 
        is very difficult to get started using.        

        Returns:
            A float score between 0.0 and 1.0. Returns 0.0 if the repository
            cannot be cloned or has no recent commits.
        """
        llm_querier = LLMQuerier(endpoint="https://genai.rcac.purdue.edu/api/chat/completions", api_key="YOUR_API_KEY_HERE")
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
        print(f"Analyzing repository: {self.url}...")
        
        # Use a temporary directory that will be automatically cleaned up
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # 1. Programmatically clone the repository
                print(f"Cloning into temporary directory: {temp_dir}")
                repo = git.Repo.clone_from(self.url, temp_dir, depth=None) # Use depth=None to get full history
                
                # 2. Define the time window (last 365 days)
                one_year_ago = datetime.now() - timedelta(days=365)
                
                # 3. Get authors of commits from the last year
                recent_authors = [
                    commit.author.name
                    for commit in repo.iter_commits()
                    if commit.committed_datetime.replace(tzinfo=None) > one_year_ago
                ]
                
                # If no recent commits, the project is inactive.
                if not recent_authors:
                    print("No recent commits found in the last year.")
                    return 0.0
                    
                total_commits = len(recent_authors)
                print(f"Found {total_commits} commits in the last year.")
                
                # 4. Count commits per author
                commit_counts = Counter(recent_authors)
                
                # 5. Identify significant authors (>5% of commits)
                significant_authors_count = 0
                for author, count in commit_counts.items():
                    contribution_percentage = (count / total_commits) * 100
                    if contribution_percentage > 5.0:
                        significant_authors_count += 1
                        print(f"  - Significant contributor: {author} ({count} commits, {contribution_percentage:.1f}%)")

                # 6. Calculate the final score (capped at 1.0)
                score = min(1.0, significant_authors_count / 20.0)

                repo.close()
                return score

            except git.exc.GitCommandError as e:
                print(f"Error cloning or analyzing repository: {e}")
                return 0.0
    
    def get_performance_claims(self) -> float:
        #TODO implement performance claims assessment logic
        return 1.0
    
    def compute_net_score(self) -> float:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_size: concurrent.futures.Future[Dict[str, float]] = executor.submit(self.get_size)
            future_license: concurrent.futures.Future[float] = executor.submit(self.get_license)
            future_ramp_up_time: concurrent.futures.Future[float] = executor.submit(self.get_ramp_up_time)
            future_bus_factor: concurrent.futures.Future[float] = executor.submit(self.get_bus_factor)
            future_dataset_quality: concurrent.futures.Future[float] = executor.submit(self.dataset.get_quality)
            future_code_quality: concurrent.futures.Future[float] = executor.submit(self.code.get_quality)
            future_performance_claims: concurrent.futures.Future[float] = executor.submit(self.get_performance_claims)

            self.size_score = future_size.result()
            self.license = future_license.result()
            self.ramp_up_time = future_ramp_up_time.result()
            self.bus_factor = future_bus_factor.result()
            self.dataset.quality = future_dataset_quality.result()
            self.code.quality = future_code_quality.result()
            self.performance_claims = future_performance_claims.result()

        # Example weights, can be adjusted based on importance
        weights: Dict[str, float] = {
            'license': 0.25,
            'ramp_up_time': 0.05,
            'bus_factor': 0.15,
            'dataset_quality': 0.195,
            'dataset_availability': 0.025,
            'code_quality': 0.005,
            'code_availability': 0.025,
            'performance_claims': 0.30
        }

        self.net_score = (
            weights['license'] * self.license +
            weights['ramp_up_time'] * self.ramp_up_time +
            weights['bus_factor'] * self.bus_factor +
            weights['dataset_quality'] * self.dataset.quality +
            weights['dataset_availability'] * self.dataset.dataset_availability +
            weights['code_quality'] * self.code.quality +
            weights['code_availability'] * self.code.code_availability +
            weights['performance_claims'] * self.performance_claims
        )

        return self.net_score