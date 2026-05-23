let langChart = null;
let barChart = null;

const $ = (id) => document.getElementById(id);

function formatNumber(n) {
  if (n >= 1e6) return (n / 1e6).toFixed(1) + "M";
  if (n >= 1e3) return (n / 1e3).toFixed(1) + "K";
  return String(n);
}

function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("zh-CN", { dateStyle: "medium" });
}

const DIMENSION_LABELS = {
  popularity: "受欢迎度",
  maintenance: "维护活跃度",
  documentation: "文档完善度",
  community: "社区活跃度",
  code_diversity: "代码多样性",
};

function formatDimensionLabel(key) {
  return DIMENSION_LABELS[key] || key.replace(/_/g, " ");
}

function getDimensionData(ai) {
  const dims = ai?.dimensions || {};
  const keys = Object.keys(dims);
  return {
    labels: keys.map(formatDimensionLabel),
    values: keys.map((k) => dims[k]),
  };
}

function destroyCharts() {
  [langChart, barChart].forEach((c) => c?.destroy());
  langChart = barChart = null;
  const barCanvas = $("bar-chart");
  const barEmpty = $("bar-chart-empty");
  if (barCanvas) barCanvas.classList.remove("hidden");
  if (barEmpty) barEmpty.classList.add("hidden");
}

function showError(msg) {
  $("error").textContent = msg;
  $("error").classList.remove("hidden");
}

function hideError() {
  $("error").classList.add("hidden");
}

function renderTopics(topics) {
  const el = $("repo-topics");
  el.innerHTML = "";
  (topics || []).forEach((t) => {
    const span = document.createElement("span");
    span.className = "topic";
    span.textContent = t;
    el.appendChild(span);
  });
}

function renderMeta(m) {
  const items = [
    ["主语言", m.primary_language || "—"],
    ["默认分支", m.default_branch],
    ["License", m.license || "无"],
    ["仓库大小", `${m.size_kb} KB`],
    ["贡献者（约）", m.contributors_count ?? "—"],
    ["创建时间", formatDate(m.created_at)],
    ["最近更新", formatDate(m.updated_at)],
    ["最近推送", formatDate(m.pushed_at)],
    ["已归档", m.archived ? "是" : "否"],
    ["Wiki", m.has_wiki ? "有" : "无"],
  ];
  $("meta-list").innerHTML = items
    .map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`)
    .join("");
}

function renderLangChart(languages) {
  const ctx = $("lang-chart").getContext("2d");
  const labels = languages.map((l) => l.name);
  const data = languages.map((l) => l.bytes);
  const colors = [
    "#58a6ff", "#39d353", "#f0b429", "#f778ba", "#a371f7",
    "#ff7b72", "#79c0ff", "#56d364", "#d2a8ff", "#ffa657",
  ];
  langChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: colors.slice(0, labels.length),
        borderWidth: 0,
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: "right", labels: { color: "#8b949e", boxWidth: 12 } },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const pct = languages[ctx.dataIndex]?.percentage ?? 0;
              return `${ctx.label}: ${pct}%`;
            },
          },
        },
      },
    },
  });
}

function renderAIScoreBarChart(ai) {
  const canvas = $("bar-chart");
  const emptyEl = $("bar-chart-empty");
  const { labels, values } = getDimensionData(ai);

  if (!ai || !values.length) {
    canvas.classList.add("hidden");
    emptyEl.classList.remove("hidden");
    return;
  }

  canvas.classList.remove("hidden");
  emptyEl.classList.add("hidden");

  const colors = ["#58a6ff", "#39d353", "#f0b429", "#f778ba", "#a371f7", "#ffa657"];
  const ctx = canvas.getContext("2d");
  barChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "得分",
        data: values,
        backgroundColor: colors.slice(0, labels.length),
        borderRadius: 6,
      }],
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: { color: "#8b949e" },
          grid: { color: "#21262d" },
        },
        x: { ticks: { color: "#8b949e" }, grid: { display: false } },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.parsed.y} 分`,
          },
        },
      },
    },
  });
}

function renderAI(ai) {
  const section = $("ai-section");
  if (!ai) {
    section.classList.add("hidden");
    return;
  }
  section.classList.remove("hidden");
  $("overall-score").textContent = Math.round(ai.overall_score);
  $("ai-summary").textContent = ai.summary || "";
  const msgEl = $("ai-message");
  if (ai.message) {
    msgEl.textContent = ai.message;
    msgEl.classList.remove("hidden");
  } else {
    msgEl.classList.add("hidden");
  }

  $("ai-strengths").innerHTML = (ai.strengths || [])
    .map((s) => `<li>${s}</li>`)
    .join("") || "<li>—</li>";
  $("ai-improvements").innerHTML = (ai.improvements || [])
    .map((s) => `<li>${s}</li>`)
    .join("") || "<li>—</li>";
}

function renderResults(data) {
  const m = data.metrics;
  $("repo-name").textContent = m.full_name;
  $("repo-desc").textContent = m.description || "暂无描述";
  $("repo-link").href = m.html_url;
  renderTopics(m.topics);

  $("stat-stars").textContent = formatNumber(m.stars);
  $("stat-forks").textContent = formatNumber(m.forks);
  $("stat-watchers").textContent = formatNumber(m.watchers);
  $("stat-issues").textContent = formatNumber(m.open_issues);

  renderMeta(m);
  destroyCharts();
  if (m.languages?.length) renderLangChart(m.languages);
  renderAIScoreBarChart(data.ai_score);
  renderAI(data.ai_score);

  $("results").classList.remove("hidden");
}

$("analyze-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  hideError();
  $("results").classList.add("hidden");
  destroyCharts();

  const url = $("repo-url").value.trim();
  const btn = $("submit-btn");
  btn.disabled = true;
  $("loading").classList.remove("hidden");

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repo_url: url }),
    });
    const body = await res.json();
    if (!res.ok) {
      throw new Error(body.detail || `请求失败 (${res.status})`);
    }
    renderResults(body);
  } catch (err) {
    showError(err.message || "分析失败，请检查 URL 或稍后重试");
  } finally {
    btn.disabled = false;
    $("loading").classList.add("hidden");
  }
});
