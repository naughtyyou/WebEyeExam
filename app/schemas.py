from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    repo_url: str = Field(..., description="GitHub 仓库 URL，如 https://github.com/owner/repo")


class LanguageStat(BaseModel):
    name: str
    bytes: int
    percentage: float


class RepoMetrics(BaseModel):
    full_name: str
    description: str | None
    html_url: str
    homepage: str | None
    stars: int
    forks: int
    watchers: int
    open_issues: int
    size_kb: int
    default_branch: str
    license: str | None
    created_at: str
    updated_at: str
    pushed_at: str | None
    topics: list[str]
    languages: list[LanguageStat]
    primary_language: str | None
    contributors_count: int | None
    has_wiki: bool
    has_projects: bool
    archived: bool
    disabled: bool


class AIScore(BaseModel):
    overall_score: float = Field(..., ge=0, le=100)
    summary: str
    dimensions: dict[str, float]
    strengths: list[str]
    improvements: list[str]
    ai_available: bool = True
    message: str | None = None


class AnalyzeResponse(BaseModel):
    metrics: RepoMetrics
    ai_score: AIScore | None = None
