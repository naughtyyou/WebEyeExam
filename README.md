# GitHub 仓库体检工具

在 48 小时内完成的公开 GitHub 仓库分析 Web 应用：输入仓库 URL，拉取 Stars、Forks、语言分布等指标并可视化展示，可选 **OpenAI 兼容 API** 进行 AI 项目评分。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + httpx |
| 前端 | 单页 HTML/CSS/JS + Chart.js |
| 数据源 | GitHub REST API |
| AI 评分 | OpenAI 兼容 Chat Completions API |

## 功能

- 解析并校验 GitHub 公开仓库 URL
- 展示 Stars、Forks、Watchers、Open Issues
- 编程语言分布（饼图）与社区指标（柱状图）
- 仓库元信息：License、分支、时间线、Topics 等
- **AI 评分**（配置 API Key 后）：综合分、五维雷达图、优势与改进建议
- 未配置 API 时自动使用规则引擎给出参考分

## 快速开始

### 1. 环境要求

- **Python 3.10+**（推荐 3.11；系统默认若为 3.7，请用 `py -3.11`）
- 可访问 `api.github.com`（可选配置 `GITHUB_TOKEN` 提高限额）
- AI 评分需配置 OpenAI 兼容服务（如 OpenAI、DeepSeek、通义等）

### 2. 安装依赖

```bash
cd exam_new

# Windows 多版本 Python 时推荐：
py -3.11 -m venv .venv
# 或：python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
copy .env.example .env   # Windows
# cp .env.example .env   # Linux/macOS
```

编辑 `.env`：

```env
# 可选，未设置时 GitHub API 约 60 次/小时
GITHUB_TOKEN=ghp_xxxx

# AI 评分（可选；不配置则使用规则评分）
OPENAI_API_KEY=sk-xxxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

PORT=8000
```

**国内/OpenAI 代理示例（DeepSeek）：**

```env
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
OPENAI_API_KEY=your-deepseek-key
```

### 4. 启动服务

```bash
python run.py
```

也可双击 Windows 脚本：`start.bat`

> `run.py` 会自动切换到项目 `.venv`（当系统 `python` 为 3.7 等未装依赖时）。若 8000 端口被占用会自动尝试下一端口，终端会打印实际访问地址。

浏览器打开终端提示的地址（默认 **http://127.0.0.1:8000**）

示例仓库：`https://github.com/fastapi/fastapi`

### 5. API 文档

- Swagger UI：http://127.0.0.1:8000/docs
- 健康检查：`GET /api/health`
- 分析接口：`POST /api/analyze`，Body：`{"repo_url": "https://github.com/owner/repo"}`

## 项目结构

```
exam_new/
├── app/
│   ├── main.py           # FastAPI 入口与路由
│   ├── config.py         # 环境配置
│   ├── schemas.py        # 请求/响应模型
│   ├── github_client.py  # GitHub API 封装
│   ├── ai_scorer.py      # AI / 规则评分
│   └── static/           # 单页前端
│       ├── index.html
│       ├── style.css
│       └── app.js
├── requirements.txt
├── run.py
├── .env.example
└── README.md
```

## 提交说明

可将本目录 `exam_new` 整体打包或推送到 GitHub 仓库提交作业。核心代码均在 `exam_new` 内，无外部依赖源码。

## Vibe Coding 提示词

详见 [VIBE_CODING.md](./VIBE_CODING.md)（作业加分项：开发过程提示词记录）。

## 许可证

MIT（作业项目，可自由使用与修改）
