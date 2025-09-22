# CustomObjects/Dataset.py
from __future__ import annotations

from typing import Optional
from urllib.parse import urlparse
from huggingface_hub import HfApi
import math
import re

from CustomObjects.LLMQuerier import LLMQuerier

class Dataset:
    def __init__(self, dataset_url, model_url) -> None:
        self.dataset_url = dataset_url
        self.model_url = model_url
        # availability: URL present -> 1.0, else 0.0
        self.dataset_availability: float = 1.0 if dataset_url else 0.0
        self.quality: float = 0.0  # filled by get_quality()

    def hf_popularity_score(self, repo_id: str) -> float:
        """
        Compute a popularity score in [0,1] from HF downloads and likes
        using simple log normalization against fixed baselines.
        """
        downloads = 0
        likes = 0

        # values that may need to change
        # baselines used to calculate popularity of dataset on huggingface - change as needed
        dnld_baseline = 1_000_000   # ~1M downloads → ~1.0
        like_baseline = 10_000    # ~10k likes → ~1.0

        # weight values for the huggingface stats
        dnld_weight = 0.7
        like_weight = 0.3

        try:
            info = HfApi().dataset_info(repo_id=repo_id)
            downloads = getattr(info, "downloads", 0) or 0
            likes = getattr(info, "likes", 0) or 0
            if likes == 0 and getattr(info, "cardData", None):
                likes = info.cardData.get("likes", 0) or 0
        except Exception:
            downloads = 0
            likes = 0

        # log normalization based on stats
        dl_score = 0.0 if dnld_baseline <= 0 else max(
            0.0, min(1.0, math.log1p(max(0.0, float(downloads))) / math.log1p(float(dnld_baseline)))
        )
        like_score = 0.0 if like_baseline <= 0 else max(
            0.0, min(1.0, math.log1p(max(0.0, float(likes))) / math.log1p(float(like_baseline)))
        ) if likes > 0 else 0.0


        return float(dnld_weight * dl_score + like_weight * like_score)

    def extract_training_data_info(self, model_url: str) -> Optional[str]:
        """
        Fetch README.md for a Hugging Face *model* and return the section
        describing training data/datasets. Returns None if not found.
        """
        parsed = urlparse(model_url)
        if "huggingface.co" not in parsed.netloc:
            return None # not a huggingface model

        parts = [p for p in parsed.path.strip("/").split("/") if p]
        if len(parts) < 2:
            return None
        owner, model = parts[0], parts[1]
        repo_id = f"{owner}/{model}"

        try:
            readme_fp = HfApi().hf_hub_download(repo_id=repo_id, filename="README.md")
            with open(readme_fp, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception:
            return None

        # find a heading mentioning data/dataset/training data; slice until next heading
        heading_re = re.compile(r"^(#{1,6})\s*(.+?)\s*$", re.MULTILINE)
        matches = list(heading_re.finditer(text))
        for i, m in enumerate(matches):
            title = m.group(2).strip().lower()
            if any(k in title for k in ("data", "dataset", "training data", "training set", "datasets")):
                start = m.start()
                # end at next heading of same/higher level
                this_level = len(m.group(1))
                end = len(text)
                for j in range(i + 1, len(matches)):
                    if len(matches[j].group(1)) <= this_level:
                        end = matches[j].start()
                        break
                return text[start:end]

        # alternative: grab a contextual chunk around a keyword if no headings found
        m = re.search(r"(training data|dataset[s]?|data set[s]?)", text, re.IGNORECASE)
        if not m:
            return None
        start = max(0, m.start() - 200)
        end = min(len(text), m.end() + 1200)
        return text[start:end]

    def score_with_llm(self, section_text: str) -> Optional[float]:
        """
        Use LLM to score dataset quality from the README snippet.
        Returns float in [0,1] or None.
        """
        llm_querier = LLMQuerier(endpoint="https://genai.rcac.purdue.edu/api/chat/completions", api_key="sk-bed2e8c43f1a4e538f4b66501ede6b0b")
        prompt = (
            "Assess the quality of the dataset used to train this model. "
            "Provide a score between 0 (very low quality) and 1 (very high quality). "
            "Dataset quality refers to characteristics such as variety and coverage of data, "
            "size and scale, and clarity of documentation. "
            "Provide only the numeric score as output, without any additional text or explanation.\n\n"
            f"Training-data excerpt from the model README:\n```\n{section_text}\n```"
        )
        response = llm_querier.query(prompt=prompt)

        if response is None:
            return 0.0

        return float(response)

    # -------------------------
    # Public: compute quality
    # -------------------------
    def get_quality(self) -> float:
        """
        Calculate dataset_quality score from two metrics:
          1) Popularity (if self.dataset_url is an HF dataset)
          2) LLM score from model README (if model_url provided and training section found in README)
        Combine when both exist: 0.5 * LLM + 0.5 * Popularity
        Otherwise use whichever is available.
        """
        # Popularity (HF dataset URL only)
        popularity_score = None
        if self.dataset_url and "huggingface.co/datasets/" in self.dataset_url:
            # extract 'owner/name' inline (keep logic local to get_quality)
            parts = [p for p in urlparse(self.dataset_url).path.strip("/").split("/") if p]
            try:
                i = parts.index("datasets")
                if len(parts) >= i + 3:
                    repo_id = f"{parts[i+1]}/{parts[i+2]}"
                    popularity_score = self.hf_popularity_score(repo_id)
            except ValueError:
                popularity_score = None

        # LLM signal from the model's README
        llm_score: Optional[float] = None
        if self.model_url:
            section = self.extract_training_data_info(self.model_url)
            if section:
                llm_score = self.score_with_llm(section)

        # Combine (simple and explicit)
        if llm_score is not None and popularity_score is not None:
            self.quality = float(0.5 * llm_score + 0.5 * popularity_score)
        elif llm_score is not None:
            self.quality = float(llm_score)
        elif popularity_score is not None:
            self.quality = float(popularity_score)
        else:
            self.quality = 0.0

        # final clamp
        self.quality = max(0.0, min(1.0, self.quality))
        return self.quality
