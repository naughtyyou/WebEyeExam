# Vibe Coding 过程记录

本文档记录使用 AI Coding 工具构建「GitHub 仓库体检」时的核心提示词与迭代思路，供作业加分参考。

## 初始需求提示词

```
在 exam_new 文件夹创建 GitHub 仓库体检工具，无现有源码。
需求：
- Web 页面输入公开 GitHub 仓库 URL
- 分析并可视化：Star、Fork、编程语言分布等
- 加分：AI 项目评分
技术栈：FastAPI + 单页前端，AI 使用 OpenAI 兼容 API
要求核心功能可跑通，并提供完整代码与运行说明。
```

## 架构拆分提示词

```
请设计项目结构：
- FastAPI 提供 /api/analyze 与静态 SPA
- github_client 调用 GitHub REST API（repos、languages、contributors）
- ai_scorer 调用 OpenAI 兼容 chat/completions，返回 JSON 结构化评分
- 未配置 API Key 时用规则引擎 fallback
- 前端 Chart.js：饼图语言分布、柱状图社区指标、雷达图 AI 维度
```

## 实现细节提示词

1. **URL 解析**：支持 `https://github.com/owner/repo` 及带 `.git`、路径参数形式。
2. **错误处理**：404 仓库不存在、403 速率限制，返回中文友好信息。
3. **环境变量**：`GITHUB_TOKEN`、`OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL`。
4. **UI**：深色 GitHub 风格、响应式布局、加载态与错误条。

## 联调与验收

```
启动 python run.py，访问 http://127.0.0.1:8000
测试仓库：https://github.com/fastapi/fastapi
确认：指标卡片、语言饼图、柱状图、元信息、AI/规则评分区块均正常。
```
