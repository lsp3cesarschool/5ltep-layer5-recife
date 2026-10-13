"""Read the public files of the other layers: over HTTPS (GitHub) or from local folders (tests, trials).

Pull architecture: no token is needed to read; GITHUB_TOKEN, when present, only raises the rate
limit of the optional commit lookup. Nothing read here is executed or trusted as instructions.
"""

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

RAW = "https://raw.githubusercontent.com/{repo}/main/{path}"
COMMITS = "https://api.github.com/repos/{repo}/commits?path={path}&per_page=1"
MAX_BYTES = 50 * 1024 * 1024  # a summary is small; refuse anything absurdly large


class Missing(Exception):
    """The file (or the whole repository) does not exist: a structural gap, not an error."""


class Fetcher:
    def __init__(self, roots: dict | None = None, offline: bool = False, token: str | None = None,
                 timeout: int = 60):
        # roots: repository short name -> local folder that mirrors the repository (e.g. fixtures).
        # offline: a repository without a local folder counts as missing (no network at all).
        self.roots = {k: Path(v) for k, v in (roots or {}).items()}
        self.offline = offline
        self.token = token if token is not None else os.environ.get("GITHUB_TOKEN")
        self.timeout = timeout

    def url(self, repo: str, path: str) -> str:
        short = repo.split("/")[1]
        if short in self.roots:
            return (self.roots[short] / path).resolve().as_uri()
        return RAW.format(repo=repo, path=path)

    def get_json(self, repo: str, path: str) -> dict:
        short = repo.split("/")[1]
        if short in self.roots:
            file = self.roots[short] / path
            if not file.is_file():
                raise Missing(f"{repo}/{path}")
            with open(file, encoding="utf-8") as f:
                return json.load(f)
        if self.offline:
            raise Missing(f"{repo}/{path} (offline)")
        request = urllib.request.Request(self.url(repo, path), headers={"User-Agent": "5ltep-layer5"})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as resp:
                data = resp.read(MAX_BYTES + 1)
        except urllib.error.HTTPError as err:
            if err.code == 404:
                raise Missing(f"{repo}/{path}") from err
            raise
        if len(data) > MAX_BYTES:
            raise ValueError(f"{repo}/{path} is larger than {MAX_BYTES} bytes")
        return json.loads(data.decode("utf-8"))

    def last_commit(self, repo: str, path: str) -> dict | None:
        """Latest commit that touched the file (sha, date), or None when unknown (offline, rate limit)."""
        short = repo.split("/")[1]
        if short in self.roots or self.offline:
            return None
        headers = {"User-Agent": "5ltep-layer5", "Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(COMMITS.format(repo=repo, path=path), headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as resp:
                items = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ValueError):
            return None
        if not items:
            return None
        return {"sha": items[0]["sha"], "date": items[0]["commit"]["committer"]["date"]}
