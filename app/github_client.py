import re
from typing import Any
from urllib.parse import urlparse

import httpx

from app.config import get_settings
from app.schemas import LanguageStat, RepoMetrics

GITHUB_API = "https://api.github.com"
REPO_URL_PATTERN = re.compile(
    r"^https?://(?:www\.)?github\.com/([^/]+)/([^/]+?)(?:\.git)?/?(?:#.*)?$",
    re.IGNORECASE,
)


class GitHubError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def parse_repo_url(url: str) -> tuple[str, str]:
    url = url.strip()
    match = REPO_URL_PATTERN.match(url)
    if match:
        owner, repo = match.group(1), match.group(2)
        return owner, repo.rstrip("/")

    parsed = urlparse(url)
    if parsed.netloc.lower().replace("www.", "") == "github.com":
        parts = [p for p in parsed.path.strip("/").split("/") if p]
        if len(parts) >= 2:
            return parts[0], parts[1].replace(".git", "")

    raise GitHubError("无效的 GitHub 仓库 URL，示例：https://github.com/torvalds/linux")


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "github-repo-health-check",
    }
    token = get_settings().github_token
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def _get(client: httpx.AsyncClient, path: str) -> Any:
    resp = await client.get(f"{GITHUB_API}{path}", headers=_headers())
    if resp.status_code == 404:
        raise GitHubError("仓库不存在或不是公开仓库", 404)
    if resp.status_code == 403:
        detail = resp.json().get("message", "API 速率限制或权限不足")
        raise GitHubError(f"GitHub API 错误：{detail}", 403)
    if resp.status_code != 200:
        raise GitHubError(f"GitHub API 请求失败 ({resp.status_code})", resp.status_code)
    return resp.json()


def _build_languages(raw: dict[str, int]) -> list[LanguageStat]:
    total = sum(raw.values()) or 1
    items = sorted(raw.items(), key=lambda x: x[1], reverse=True)
    return [
        LanguageStat(
            name=name,
            bytes=size,
            percentage=round(size / total * 100, 2),
        )
        for name, size in items
    ]


async def fetch_repo_metrics(repo_url: str) -> RepoMetrics:
    owner, repo = parse_repo_url(repo_url)

    async with httpx.AsyncClient(timeout=30.0) as client:
        data = await _get(client, f"/repos/{owner}/{repo}")
        languages_raw = await _get(client, f"/repos/{owner}/{repo}/languages")

        contributors_count: int | None = None
        try:
            resp = await client.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/contributors",
                headers=_headers(),
                params={"per_page": 1, "anon": "true"},
                timeout=8.0,
            )
            if resp.status_code == 200:
                link = resp.headers.get("Link", "")
                m = re.search(r'page=(\d+)>; rel="last"', link)
                contributors_count = int(m.group(1)) if m else len(resp.json())
        except (httpx.HTTPError, httpx.TimeoutException):
            contributors_count = None

    license_name = None
    if data.get("license"):
        license_name = data["license"].get("spdx_id") or data["license"].get("name")

    languages = _build_languages(languages_raw)
    primary = languages[0].name if languages else data.get("language")

    return RepoMetrics(
        full_name=data["full_name"],
        description=data.get("description"),
        html_url=data["html_url"],
        homepage=data.get("homepage") or None,
        stars=data["stargazers_count"],
        forks=data["forks_count"],
        watchers=data["watchers_count"],
        open_issues=data["open_issues_count"],
        size_kb=data["size"],
        default_branch=data["default_branch"],
        license=license_name,
        created_at=data["created_at"],
        updated_at=data["updated_at"],
        pushed_at=data.get("pushed_at"),
        topics=data.get("topics") or [],
        languages=languages,
        primary_language=primary,
        contributors_count=contributors_count,
        has_wiki=data.get("has_wiki", False),
        has_projects=data.get("has_projects", False),
        archived=data.get("archived", False),
        disabled=data.get("disabled", False),
    )
