import json
import re

import httpx

from app.config import get_settings
from app.schemas import AIScore, RepoMetrics

SYSTEM_PROMPT = """你是一位开源项目评审专家。根据提供的 GitHub 仓库指标，给出客观、简洁的项目健康度评分。
必须以 JSON 格式回复，不要包含 markdown 代码块，结构如下：
{
  "overall_score": 0-100 的浮点数,
  "summary": "一两句话总评",
  "dimensions": {
    "popularity": 0-100,
    "maintenance": 0-100,
    "documentation": 0-100,
    "community": 0-100,
    "code_diversity": 0-100
  },
  "strengths": ["优点1", "优点2"],
  "improvements": ["改进建议1", "改进建议2"]
}
评分应结合 stars、forks、issues、更新时间、license、topics、语言分布等综合判断。"""


def _metrics_context(metrics: RepoMetrics) -> str:
    lang_summary = ", ".join(
        f"{l.name} {l.percentage}%" for l in metrics.languages[:8]
    )
    return f"""仓库：{metrics.full_name}
描述：{metrics.description or "无"}
Stars：{metrics.stars}，Forks：{metrics.forks}，Watchers：{metrics.watchers}
Open Issues：{metrics.open_issues}，Contributors（约）：{metrics.contributors_count or "未知"}
主语言：{metrics.primary_language or "未知"}
语言分布：{lang_summary or "无数据"}
License：{metrics.license or "无"}
Topics：{", ".join(metrics.topics) or "无"}
创建：{metrics.created_at}，最近推送：{metrics.pushed_at or "未知"}
已归档：{metrics.archived}，有 Wiki：{metrics.has_wiki}
仓库大小(KB)：{metrics.size_kb}"""


def _parse_ai_json(content: str) -> dict:
    text = content.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    return json.loads(text)


def _fallback_score(metrics: RepoMetrics) -> AIScore:
    """未配置 API 时基于规则的简易评分。"""
    pop = min(100, (metrics.stars / 100) * 10 + (metrics.forks / 50) * 10)
    maint = 50
    if metrics.pushed_at:
        maint = 70
    if metrics.archived:
        maint = 20
    doc = 40 + (20 if metrics.description else 0) + (15 if metrics.has_wiki else 0)
    comm = min(100, (metrics.open_issues / 10) * 5 + 30)
    div = min(100, len(metrics.languages) * 15) if metrics.languages else 30
    dims = {
        "popularity": round(pop, 1),
        "maintenance": round(maint, 1),
        "documentation": round(doc, 1),
        "community": round(comm, 1),
        "code_diversity": round(div, 1),
    }
    overall = round(sum(dims.values()) / len(dims), 1)
    return AIScore(
        overall_score=overall,
        summary="基于规则计算的参考评分（未启用 AI API）。配置 OPENAI_API_KEY 后可获得 AI 深度评分。",
        dimensions=dims,
        strengths=["社区关注度尚可"] if metrics.stars > 100 else ["项目结构可继续观察"],
        improvements=["建议完善 README 与文档"] if not metrics.description else ["保持定期维护与发布"],
        ai_available=False,
        message="未配置 OpenAI 兼容 API，已使用规则评分",
    )


async def score_repo(metrics: RepoMetrics) -> AIScore:
    settings = get_settings()
    if not settings.openai_api_key:
        return _fallback_score(metrics)

    user_content = _metrics_context(metrics)
    payload = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.3,
    }

    url = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                return AIScore(
                    overall_score=0,
                    summary="AI 评分请求失败",
                    dimensions={},
                    strengths=[],
                    improvements=[],
                    ai_available=False,
                    message=f"API 错误 {resp.status_code}: {resp.text[:200]}",
                )
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            parsed = _parse_ai_json(content)
            return AIScore(
                overall_score=float(parsed["overall_score"]),
                summary=str(parsed.get("summary", "")),
                dimensions={k: float(v) for k, v in parsed.get("dimensions", {}).items()},
                strengths=list(parsed.get("strengths", [])),
                improvements=list(parsed.get("improvements", [])),
                ai_available=True,
            )
    except (httpx.HTTPError, json.JSONDecodeError, KeyError, ValueError) as e:
        fallback = _fallback_score(metrics)
        fallback.message = f"AI 解析失败，已回退规则评分：{e}"
        return fallback
