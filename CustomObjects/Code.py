from typing import Optional
from urllib.parse import urlparse
import os
import git
import tempfile

from flake8.api import legacy as flake8  # requires flake8 installed


class Code:
    def __init__(self, code_url) -> None:
        self.code_url = code_url
        # availability: URL present -> 1.0, else 0.0
        # might need to change this later to parse README or files for reference to a dataset instead of relying on url
        self.code_availability: float = 1.0 if code_url else 0.0
        self.quality: float = 0.0

    def count_python_loc(self, root: str) -> int:
        """Count total lines across all .py files under root."""
        total = 0
        for dirpath, _, filenames in os.walk(root):
            for name in filenames:
                if not name.endswith(".py"):
                    continue
                p = os.path.join(dirpath, name)
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as f:
                        for _ in f:
                            total += 1
                except Exception:
                    # unreadable file -> skip
                    continue
        return total

    def run_flake8(self, root: str) -> int:
        """Run flake8 on root and return total error/warning count."""
        style = flake8.get_style_guide(
            quiet=1,
        )
        report = style.check_files([root])
        return int(getattr(report, "total_errors", 0) or 0)

    def get_quality(self) -> float:
        """
        Code quality metric:

          - Clone the repository.
          - Run static analysis (Flake8) on Python files.
          - Let LinesOfCode = total lines across all .py files.
          - Let ErrorCount = total Flake8 issues.

          Score = max(0, 1 - LinesOfCode / (ErrorCount * 5))

          Special cases:
            - If no code_url or unsupported host -> 0.0
            - If clone fails or no Python files -> 0.0
            - If ErrorCount == 0 and there are Python files -> 1.0
        """

        if not self.code_url:
            self.quality = 0.0
            return self.quality
        host = urlparse(self.code_url).netloc.lower()
        if host not in {"github.com", "gitlab.com", "bitbucket.org"}:
            self.quality = 0.0
            return self.quality

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                # shallow clone for speed
                repo = git.Repo.clone_from(self.code_url, tmpdir, depth=1, single_branch=True)
            except Exception:
                self.quality = 0.0
                return self.quality

            try:
                loc = self.count_python_loc(tmpdir)
                if loc == 0:
                    self.quality = 0.0
                    return self.quality

                error_count = self.run_flake8(tmpdir)

                if error_count == 0:
                    self.quality = 1.0
                    return self.quality
                
                # --- DYNAMIC MULTIPLIER LOGIC ---
                # The penalty multiplier changes based on the total lines of code.
                # Smaller projects are penalized more heavily for each error.
                if loc < 500:
                    multiplier = 5   # Very strict for small scripts
                elif loc < 5000:
                    multiplier = 20  # Moderately strict for small projects
                elif loc < 20000:
                    multiplier = 50  # Less strict for medium projects
                else:
                    multiplier = 100 # Lenient for very large projects
                
                score = max(0.0, 1.0 - (loc / (error_count * multiplier)))

                self.quality = float(score)
                return self.quality

            finally:
                try:
                    repo.close()
                except Exception:
                    pass
