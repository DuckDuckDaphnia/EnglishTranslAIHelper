// 翻译练习助手 — 前端逻辑
"use strict";

const CELL = 11; // 热力图单元格边长(px),与 style.css 保持一致
const GAP = 3;   // 单元格间距(px)
const STEP = CELL + GAP; // 14px

const API = {
  config: "/api/config",
  evaluate: "/api/evaluate",
  heatmap: "/api/heatmap",
  stats: "/api/stats",
  history: "/api/history",
  corpora: "/api/corpora",
  state: "/api/state",
};

const $ = (id) => document.getElementById(id);

let currentMode = "zh2en";
let currentSource = "";
let currentCorpus = null;
let currentIndex = 0;
let corpusTotal = 0;

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

async function fetchJSON(url, options) {
  const resp = await fetch(url, options);
  let data = {};
  try { data = await resp.json(); } catch (e) { /* 非 JSON 响应 */ }
  if (!resp.ok) throw new Error(data.detail || `请求失败(${resp.status})`);
  return data;
}

function setLoading(on) {
  $("loading").hidden = !on;
  $("submitBtn").disabled = on;
}
function showError(msg) { const el = $("error"); el.textContent = msg; el.hidden = false; }
function clearError() { $("error").hidden = true; }
function hideResult() { $("resultCard").hidden = true; }

async function loadSentence() {
  try {
    const params = new URLSearchParams({ mode: currentMode });
    if (currentCorpus) {
      params.set("corpus", currentCorpus);
      params.set("index", currentIndex);
    }
    const data = await fetchJSON(`/api/sentence?${params.toString()}`);
    currentSource = data.source;
    if (data.total != null) {
      corpusTotal = data.total;
      currentIndex = data.index;
      $("positionInfo").textContent = `第 ${currentIndex + 1} / ${corpusTotal} 题`;
    }
    $("sourceText").textContent = data.source;
    $("directionLabel").textContent =
      currentMode === "zh2en" ? "请把下面的中文翻译成英文" : "请把下面的英文翻译成中文";
    $("userInput").value = "";
    hideResult();
    clearError();
    $("userInput").focus();
    updateCorpusInfo();
  } catch (e) {
    $("sourceText").textContent = "⚠️ " + e.message;
  }
}

function scoreInfo(score) {
  if (score >= 85) return { label: "优秀", cls: "s-good" };
  if (score >= 70) return { label: "良好", cls: "s-ok" };
  if (score >= 60) return { label: "及格", cls: "s-warn" };
  return { label: "需加强", cls: "s-bad" };
}

function renderResult(result) {
  const info = scoreInfo(result.score);
  const scoreEl = $("score");
  scoreEl.textContent = result.score;
  scoreEl.className = "score " + info.cls;
  const labelEl = $("scoreLabel");
  labelEl.textContent = info.label;
  labelEl.className = "score-label " + info.cls;
  $("corrected").textContent = result.corrected || "—";
  $("feedback").textContent = result.feedback || "—";
  renderList("highlights", result.highlights);
  renderList("improvements", result.improvements);
  $("resultCard").hidden = false;
  $("resultCard").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function renderList(id, items) {
  const ul = $(id);
  ul.innerHTML = "";
  if (!items || items.length === 0) {
    const li = document.createElement("li");
    li.textContent = "暂无";
    li.className = "empty";
    ul.appendChild(li);
    return;
  }
  items.forEach((t) => {
    const li = document.createElement("li");
    li.textContent = t;
    ul.appendChild(li);
  });
}

async function submit() {
  const text = $("userInput").value.trim();
  if (!text) { showError("请先输入你的翻译"); return; }
  setLoading(true);
  clearError();
  try {
    const data = await fetchJSON(API.evaluate, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: currentMode, source: currentSource, user_translation: text }),
    });
    renderResult(data.result);
    updateStats(data.stats);
    await Promise.all([loadHeatmap(), loadHistory(), loadStats()]);
  } catch (e) {
    showError(e.message);
  } finally {
    setLoading(false);
  }
}

function updateStats(s) {
  $("todayCount").textContent = s.today_count;
  $("totalCount").textContent = s.total_count;
  $("avgScore").textContent = s.avg_score || "—";
}
async function loadStats() {
  try { updateStats(await fetchJSON(API.stats)); } catch (e) { /* 忽略 */ }
}

/* ---------- 热力图 ---------- */
function levelFor(count) {
  if (count <= 0) return 0;
  if (count <= 2) return 1;
  if (count <= 4) return 2;
  if (count <= 6) return 3;
  return 4;
}

function toKey(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

const MONTH_NAMES = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"];

function renderDayLabels() {
  const days = $("days");
  if (days.childElementCount) return;
  const labels = ["", "周一", "", "周三", "", "周五", ""];
  labels.forEach((t) => {
    const slot = document.createElement("div");
    slot.className = "day-slot";
    slot.textContent = t;
    days.appendChild(slot);
  });
}

function renderHeatmap(data) {
  renderDayLabels();
  const grid = $("grid");
  const months = $("months");
  grid.innerHTML = "";
  months.innerHTML = "";

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const totalDays = 371;
  const start = new Date(today);
  start.setDate(start.getDate() - (totalDays - 1));
  start.setDate(start.getDate() - start.getDay()); // 对齐到周日

  // 按周切分
  const weeks = [];
  let cur = new Date(start);
  while (cur <= today) {
    const week = [];
    for (let i = 0; i < 7; i++) {
      if (cur > today) {
        week.push(null);
      } else {
        const key = toKey(cur);
        const d = data[key] || { count: 0, avg_score: 0 };
        week.push({ key, count: d.count, avg: d.avg_score });
      }
      cur.setDate(cur.getDate() + 1);
    }
    weeks.push(week);
  }

  // 月份标签
  let prevMonth = -1;
  weeks.forEach((week, wi) => {
    const first = week.find((d) => d !== null);
    if (!first) return;
    const m = parseInt(first.key.slice(5, 7), 10);
    if (m !== prevMonth) {
      const label = document.createElement("span");
      label.className = "month-label";
      label.style.left = (wi * STEP) + "px";
      label.textContent = MONTH_NAMES[m - 1];
      months.appendChild(label);
      prevMonth = m;
    }
  });

  // 单元格
  weeks.forEach((week) => {
    const col = document.createElement("div");
    col.className = "heatmap-col";
    week.forEach((day) => {
      const cell = document.createElement("div");
      cell.className = "heatmap-cell";
      if (day) {
        cell.dataset.level = levelFor(day.count);
        cell.dataset.key = day.key;
        cell.dataset.count = day.count;
        cell.dataset.avg = day.avg;
      } else {
        cell.classList.add("placeholder");
      }
      col.appendChild(cell);
    });
    grid.appendChild(col);
  });
}

async function loadHeatmap() {
  try {
    const { data } = await fetchJSON(API.heatmap);
    renderHeatmap(data);
  } catch (e) { /* 忽略 */ }
}

function initTooltip() {
  const tip = document.createElement("div");
  tip.className = "heatmap-tooltip";
  tip.hidden = true;
  document.body.appendChild(tip);

  $("grid").addEventListener("mousemove", (e) => {
    const cell = e.target.closest(".heatmap-cell:not(.placeholder)");
    if (!cell) { tip.hidden = true; return; }
    const count = parseInt(cell.dataset.count, 10);
    const avg = cell.dataset.avg;
    tip.innerHTML =
      `<b>${cell.dataset.key}</b><br>翻译 <b>${count}</b> 次` +
      (count ? `<br>平均分 <b>${avg}</b>` : "");
    tip.hidden = false;
    const pad = 12;
    let x = e.clientX + pad;
    let y = e.clientY + pad;
    const rect = tip.getBoundingClientRect();
    if (x + rect.width > window.innerWidth) x = e.clientX - rect.width - pad;
    if (y + rect.height > window.innerHeight) y = e.clientY - rect.height - pad;
    tip.style.left = x + "px";
    tip.style.top = y + "px";
  });
  $("grid").addEventListener("mouseleave", () => { tip.hidden = true; });
}

/* ---------- 历史记录 ---------- */
async function loadHistory() {
  try {
    const { history } = await fetchJSON(API.history);
    renderHistory(history);
  } catch (e) { /* 忽略 */ }
}

function renderHistory(history) {
  const list = $("historyList");
  list.innerHTML = "";
  if (!history.length) {
    list.innerHTML = '<div class="empty">还没有记录,快去翻译一句吧～</div>';
    return;
  }
  history.forEach((h) => {
    const info = scoreInfo(h.score);
    const item = document.createElement("div");
    item.className = "history-item";
    item.innerHTML = `
      <div class="history-top">
        <span class="badge">${h.mode === "zh2en" ? "中译英" : "英译中"}</span>
        <span class="history-score ${info.cls}">${h.score} 分</span>
        <span class="history-time">${escapeHtml(h.timestamp)}</span>
      </div>
      <div class="history-source">原文:${escapeHtml(h.source)}</div>
      <div class="history-user">你的译文:${escapeHtml(h.user_translation)}</div>
      <div class="history-corrected">标准译文:${escapeHtml(h.corrected)}</div>
    `;
    list.appendChild(item);
  });
}

/* ---------- 配置 ---------- */
async function loadConfig() {
  try {
    const cfg = await fetchJSON(API.config);
    if (!cfg.has_key) {
      const b = $("configBanner");
      b.hidden = false;
      b.textContent = "⚠️ 尚未配置大模型 API Key:请打开项目根目录的 config.json,填入 api_key 后重启服务。";
    }
  } catch (e) { /* 忽略 */ }
}

/* ---------- 语料库选择与进度记忆 ---------- */
async function loadCorpora() {
  try {
    const { corpora, current } = await fetchJSON(API.corpora);
    const sel = $("corpusSelect");
    sel.innerHTML = "";
    if (!corpora.length) {
      const opt = document.createElement("option");
      opt.textContent = "（暂无语料库）";
      sel.appendChild(opt);
      sel.disabled = true;
      return;
    }
    corpora.forEach((c) => {
      const opt = document.createElement("option");
      opt.value = c.id;
      opt.textContent = `${c.name}（${c.count} 题）`;
      sel.appendChild(opt);
    });
    const saved = current && current.corpus ? current.corpus : corpora[0].id;
    if (corpora.some((c) => c.id === saved)) {
      currentCorpus = saved;
      currentIndex = Number(current && current.index) || 0;
    } else {
      currentCorpus = corpora[0].id;
      currentIndex = 0;
    }
    sel.value = currentCorpus;
    updateCorpusInfo();
  } catch (e) { /* 忽略 */ }
}

function saveState() {
  if (!currentCorpus) return;
  fetch(API.state, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ corpus: currentCorpus, index: currentIndex }),
  }).catch(() => {});
}

function updateCorpusInfo() {
  const el = $("corpusInfo");
  if (!currentCorpus) { el.textContent = ""; return; }
  const pos = corpusTotal ? ` · 第 ${currentIndex + 1} / ${corpusTotal} 题` : "";
  el.textContent = `语料库:${currentCorpus}${pos}`;
}

/* ---------- 事件绑定 ---------- */
document.querySelectorAll(".mode-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    currentMode = btn.dataset.mode;
    document.querySelectorAll(".mode-btn").forEach((b) => b.classList.toggle("active", b === btn));
    loadSentence();
  });
});
$("nextBtn").addEventListener("click", () => {
  if (!currentCorpus || !corpusTotal) { loadSentence(); return; }
  currentIndex = (currentIndex + 1) % corpusTotal;
  saveState();
  loadSentence();
});
$("prevBtn").addEventListener("click", () => {
  if (!currentCorpus || !corpusTotal) return;
  currentIndex = (currentIndex - 1 + corpusTotal) % corpusTotal;
  saveState();
  loadSentence();
});
$("corpusSelect").addEventListener("change", () => {
  currentCorpus = $("corpusSelect").value;
  currentIndex = 0;
  corpusTotal = 0;
  saveState();
  loadSentence();
});
$("submitBtn").addEventListener("click", submit);
$("userInput").addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") submit();
});

async function init() {
  initTooltip();
  await loadConfig();
  await loadCorpora();
  await loadSentence();
  await Promise.all([loadStats(), loadHeatmap(), loadHistory()]);
}
init();
