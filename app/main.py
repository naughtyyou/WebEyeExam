from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.ai_scorer import score_repo
from app.config import get_settings
from app.github_client import GitHubError, fetch_repo_metrics
from app.schemas import AnalyzeRequest, AnalyzeResponse

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="GitHub 仓库体检",
    description="分析公开 GitHub 仓库指标并可视化展示，支持 AI 评分",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def index():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "GitHub 仓库体检 API", "docs": "/docs"}


@app.get("/api/health")
async def health():
    settings = get_settings()
    return {
        "status": "ok",
        "github_token_configured": bool(settings.github_token),
        "ai_configured": bool(settings.openai_api_key),
    }


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(body: AnalyzeRequest):
    try:
        metrics = await fetch_repo_metrics(body.repo_url)
    except GitHubError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e

    ai_score = await score_repo(metrics)
    return AnalyzeResponse(metrics=metrics, ai_score=ai_score)
