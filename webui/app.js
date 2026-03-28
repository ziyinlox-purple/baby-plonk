const samples = {
  binary: [
    [1, 1, 0, 1, 1],
    [0, 0, 1, 0, 1],
    [1, 0, 0, 0, 1],
  ],
  mixed: [
    [2, 1, 0, 3, 1],
    [0, 0, 1, 0, 1],
    [1, -1, 0, 0, 1],
  ],
};

const selectorKeys = ["q_L", "q_R", "q_M", "q_C", "q_O"];
let editorRows = [];
let suppressRawSync = false;
let livePreviewTimer = null;
let currentLang = "en";

const programInput = document.querySelector("#programInput");
const groupOrderInput = document.querySelector("#groupOrderInput");
const statusLine = document.querySelector("#statusLine");
const generateButton = document.querySelector("#generateButton");
const selectorTableBody = document.querySelector("#selectorTableBody");
const constraintCards = document.querySelector("#constraintCards");
const jsonOutput = document.querySelector("#jsonOutput");
const selectorEditorBody = document.querySelector("#selectorEditorBody");
const addRowButton = document.querySelector("#addRowButton");
const langToggle = document.querySelector("#langToggle");
const floatingTooltip = document.querySelector("#floatingTooltip");

const heroConstraintCount = document.querySelector("#heroConstraintCount");
const heroGroupOrder = document.querySelector("#heroGroupOrder");
const heroPublicCount = document.querySelector("#heroPublicCount");
const metricRows = document.querySelector("#metricRows");
const metricWidth = document.querySelector("#metricWidth");
const metricState = document.querySelector("#metricState");

const i18n = {
  en: {
    hero_title_prefix: "Directly enter",
    hero_title_suffix: "and visualize each constraint.",
    hero_text:
      "This page is focused on selector-first input. Each row is treated as one selector-form constraint, and the UI turns it into an equation view immediately. It is meant to visualize selector rows, not source-language compilation.",
    stat_constraints: "Constraints",
    stat_group_order: "Group Order",
    stat_binary_rows: "Binary Rows",
    input_kicker: "Selector Input",
    input_title: "Selector-first editor",
    badge_five_values: "5 values per row",
    badge_realtime: "Realtime preview",
    sample_binary: "Binary Sample",
    sample_mixed: "Mixed Sample",
    add_row: "Add Row",
    clear: "Clear",
    selector_rows: "Selector rows",
    selector_rows_help:
      "Raw selector text follows the fixed order q_L, q_R, q_M, q_C, q_O. Accepted formats include: 1 1 0 0 1 or [0, 0, 1, 0, 1].",
    grid_note_prefix: "Each row maps directly to",
    selector_meaning_title: "Selector columns",
    selector_q_l: "coefficient for the left wire term.",
    selector_q_r: "coefficient for the right wire term.",
    selector_q_m: "coefficient for the multiplication term.",
    selector_q_c: "constant term added into the constraint.",
    selector_q_o: "coefficient applied to the output wire term.",
    preview: "Preview",
    action: "Action",
    raw_selector_text: "Raw selector text",
    advanced_options: "Advanced options",
    group_order: "Group order",
    visualize_constraints: "Visualize Constraints",
    copy_selectors: "Copy Selectors",
    results_kicker: "Results",
    results_title: "Visualized constraints",
    equation_meaning_title: "How to read the equation",
    equation_help_1: "Each row is converted into one gate-style equation of the form “expression = 0”.",
    equation_help_2: "The left, right, multiplication, constant, and output terms are assembled directly from the selector values.",
    equation_help_3: "This lets you see how one selector row defines the constraint enforced by the gate.",
    selector_table: "Selector Table",
    equation_cards: "Equation Cards",
    raw_json: "Raw JSON",
    rows: "Rows",
    state: "State",
    equation: "Equation",
    empty_state: "Run the visualizer to inspect selector rows.",
    no_constraints: "No constraints generated yet.",
    status_ready: "Ready.",
    status_loaded: "Loaded the {name} sample.",
    status_visualizing: "Visualizing constraints...",
    status_updated: "Constraint view updated.",
    status_cleared: "Cleared the current selector rows.",
    status_copied: "Copied the current selector rows to the clipboard.",
    status_clipboard_blocked: "Clipboard copy was blocked by the browser.",
    status_raw_incomplete: "Raw selector text is incomplete.",
    state_idle: "Idle",
    state_ready: "Ready",
    state_running: "Running",
    state_error: "Error",
    state_editing: "Editing",
    sample_binary_name: "binary",
    sample_mixed_name: "mixed",
    delete: "Delete",
    binary_row: "Binary Row",
    yes: "Yes",
    no: "No",
    constraint: "Constraint",
    lang_button: "中文",
  },
  zh: {
    hero_title_prefix: "直接输入",
    hero_title_suffix: "并预览每一条约束。",
    hero_text:
      "这个页面重点强调 selector 输入。每一行都会被当作一条 selector 形式的约束，界面会立刻把它转换成方程视图。它主要用于可视化 selector 行，而不是做源码级编译。",
    stat_constraints: "约束数",
    stat_group_order: "群阶",
    stat_binary_rows: "二进制行数",
    input_kicker: "Selector 输入",
    input_title: "Selector 优先编辑器",
    badge_five_values: "每行 5 个值",
    badge_realtime: "实时预览",
    sample_binary: "二进制示例",
    sample_mixed: "混合示例",
    add_row: "新增一行",
    clear: "清空",
    selector_rows: "Selector 行",
    selector_rows_help:
      "Raw selector text 需要遵循固定顺序 q_L, q_R, q_M, q_C, q_O。可接受的格式包括：1 1 0 0 1 或 [0, 0, 1, 0, 1]。",
    grid_note_prefix: "每一行依次对应",
    selector_meaning_title: "Selector 列含义",
    selector_q_l: "左侧 wire 项的系数。",
    selector_q_r: "右侧 wire 项的系数。",
    selector_q_m: "乘法项的系数。",
    selector_q_c: "加入约束中的常数项。",
    selector_q_o: "输出 wire 项前的系数。",
    preview: "预览",
    action: "操作",
    raw_selector_text: "原始 selector 文本",
    advanced_options: "高级选项",
    group_order: "群阶",
    visualize_constraints: "可视化约束",
    copy_selectors: "复制 Selectors",
    results_kicker: "结果区域",
    results_title: "约束可视化结果",
    equation_meaning_title: "如何理解这个等式",
    equation_help_1: "每一行都会被转换成一条 gate 风格的等式，形式是“expression = 0”。",
    equation_help_2: "左项、右项、乘法项、常数项和输出项都会直接由 selector 的值组装出来。",
    equation_help_3: "这样你就能看到一行 selector 是如何定义这条 gate 约束的。",
    selector_table: "Selector 表",
    equation_cards: "等式卡片",
    raw_json: "原始 JSON",
    rows: "行数",
    state: "状态",
    equation: "等式",
    empty_state: "点击可视化后在这里查看 selector 行。",
    no_constraints: "当前还没有生成任何约束。",
    status_ready: "就绪。",
    status_loaded: "已加载 {name} 示例。",
    status_visualizing: "正在生成约束视图...",
    status_updated: "约束视图已更新。",
    status_cleared: "已清空当前 selector 行。",
    status_copied: "已复制当前 selector 行。",
    status_clipboard_blocked: "浏览器阻止了剪贴板复制。",
    status_raw_incomplete: "原始 selector 文本还不完整。",
    state_idle: "空闲",
    state_ready: "就绪",
    state_running: "处理中",
    state_error: "错误",
    state_editing: "编辑中",
    sample_binary_name: "二进制",
    sample_mixed_name: "混合",
    delete: "删除",
    binary_row: "二进制行",
    yes: "是",
    no: "否",
    constraint: "约束",
    lang_button: "EN",
  },
};

function t(key, vars = {}) {
  let text = i18n[currentLang][key] ?? i18n.en[key] ?? key;
  for (const [name, value] of Object.entries(vars)) {
    text = text.replace(`{${name}}`, value);
  }
  return text;
}

function setStatus(message, state = "Idle") {
  statusLine.textContent = message;
  metricState.textContent = state;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function selectorLabelMarkup(key) {
  const suffix = key.split("_")[1];
  return `q<sub>${escapeHtml(suffix)}</sub>`;
}

function buildEquationPreview(row) {
  const [qL, qR, qM, qC, qO] = row;
  const parts = [];
  if (qL !== 0) parts.push(qL === 1 ? "w_a" : qL === -1 ? "-w_a" : `${qL}·w_a`);
  if (qR !== 0) parts.push(qR === 1 ? "w_b" : qR === -1 ? "-w_b" : `${qR}·w_b`);
  if (qM !== 0) parts.push(qM === 1 ? "w_a·w_b" : qM === -1 ? "-w_a·w_b" : `${qM}·w_a·w_b`);
  if (qC !== 0) parts.push(String(qC));
  if (qO !== 0) parts.push(qO === 1 ? "-w_c" : qO === -1 ? "w_c" : `${-qO}·w_c`);
  if (!parts.length) return "0 = 0";

  let output = parts[0];
  for (const part of parts.slice(1)) {
    if (part.startsWith("-")) output += ` - ${part.slice(1)}`;
    else output += ` + ${part}`;
  }
  return `${output} = 0`;
}

function termLatex(coefficient, term) {
  if (coefficient === 0) return "";
  if (coefficient === 1) return term;
  if (coefficient === -1) return `-${term}`;
  return `${coefficient}${term}`;
}

function buildEquationLatex(row) {
  const [qL, qR, qM, qC, qO] = row;
  const parts = [
    termLatex(qL, "w_a"),
    termLatex(qR, "w_b"),
    termLatex(qM, "w_aw_b"),
    qC === 0 ? "" : String(qC),
    termLatex(-qO, "w_c"),
  ].filter(Boolean);

  if (!parts.length) return "0 = 0";

  let expression = parts[0];
  for (const part of parts.slice(1)) {
    if (part.startsWith("-")) expression += ` - ${part.slice(1)}`;
    else expression += ` + ${part}`;
  }
  return `${expression} = 0`;
}

function mathMarkup(latex) {
  return `\\(${latex}\\)`;
}

function syncRawTextareaFromGrid() {
  suppressRawSync = true;
  programInput.value = editorRows.map((row) => row.join(" ")).join("\n");
  suppressRawSync = false;
}

function renderEditorGrid() {
  selectorEditorBody.innerHTML = editorRows
    .map((row, rowIndex) => {
      const inputs = row
        .map(
          (value, columnIndex) => `
            <td>
              <input
                type="number"
                class="grid-input"
                data-row="${rowIndex}"
                data-col="${columnIndex}"
                value="${value}"
              />
            </td>
          `
        )
        .join("");

      return `
        <tr>
          <td class="row-label">${rowIndex + 1}</td>
          ${inputs}
          <td class="preview-cell">${escapeHtml(buildEquationPreview(row))}</td>
          <td>
            <button class="icon-button" data-delete-row="${rowIndex}">${escapeHtml(t("delete"))}</button>
          </td>
        </tr>
      `;
    })
    .join("");
}

function setEditorRows(rows) {
  editorRows = rows.map((row) => [...row]);
  if (!editorRows.length) editorRows = [[0, 0, 0, 0, 1]];
  renderEditorGrid();
  syncRawTextareaFromGrid();
}

function parseRawSelectors(raw) {
  return raw
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => line.replaceAll(",", " ").split(/\s+/).map((item) => Number(item)));
}

function classifyRow(row) {
  const [qL, qR, qM, qC, qO] = row;
  if (qM !== 0) return "Multiplication";
  if (qL !== 0 || qR !== 0 || qC !== 0) return "Linear";
  if (qO !== 0) return "Output";
  return "Empty";
}

function validateRows(rows) {
  if (!rows.length) throw new Error("Please enter at least one selector row.");
  for (const [index, row] of rows.entries()) {
    if (row.length !== 5) {
      throw new Error(`Line ${index + 1} must contain exactly 5 values: q_L q_R q_M q_C q_O.`);
    }
    if (row.some((value) => !Number.isFinite(value))) {
      throw new Error(`Line ${index + 1} contains an invalid number.`);
    }
  }
}

function buildLocalPayload(rows, groupOrderInput) {
  validateRows(rows);

  const groupOrder = groupOrderInput ? Number(groupOrderInput) : rows.length;
  if (!Number.isFinite(groupOrder) || groupOrder < rows.length) {
    throw new Error(`Group order must be at least ${rows.length}.`);
  }

  const activeCounts = Object.fromEntries(selectorKeys.map((key) => [key, 0]));
  const selectors = rows.map((row, index) => {
    const selectorMap = Object.fromEntries(selectorKeys.map((key, keyIndex) => [key, row[keyIndex]]));
    for (const key of selectorKeys) {
      if (selectorMap[key] !== 0) activeCounts[key] += 1;
    }
    return {
      index: index + 1,
      selectors: selectorMap,
      equation: buildEquationPreview(row),
      equation_latex: buildEquationLatex(row),
      binary: row.every((value) => value === 0 || value === 1),
    };
  });

  return {
    summary: {
      constraint_count: rows.length,
      group_order: groupOrder,
      binary_rows: rows.filter((row) => row.every((value) => value === 0 || value === 1)).length,
      active_counts: activeCounts,
    },
    selectors,
  };
}

function scheduleLivePreview() {
  window.clearTimeout(livePreviewTimer);
  livePreviewTimer = window.setTimeout(() => {
    generateSelectors({ silentOnError: true });
  }, 220);
}

function rerenderMath() {
  if (window.MathJax?.typesetPromise) {
    window.MathJax.typesetPromise().catch(() => {});
  }
}

function renderTable(selectors) {
  if (!selectors.length) {
    selectorTableBody.innerHTML =
      `<tr><td colspan="7" class="empty-state">${escapeHtml(t("no_constraints"))}</td></tr>`;
    return;
  }

  selectorTableBody.innerHTML = selectors
    .map(
      (row) => `
        <tr>
          <td>${row.index}</td>
          <td>${row.selectors.q_L}</td>
          <td>${row.selectors.q_R}</td>
          <td>${row.selectors.q_M}</td>
          <td>${row.selectors.q_C}</td>
          <td>${row.selectors.q_O}</td>
          <td class="equation-cell">${mathMarkup(row.equation_latex)}</td>
        </tr>
      `
    )
    .join("");
}

function renderCards(selectors) {
  if (!selectors.length) {
    constraintCards.innerHTML = `<article class="empty-card">${escapeHtml(t("no_constraints"))}</article>`;
    return;
  }

  constraintCards.innerHTML = selectors
    .map(
      (row) => `
        <article class="constraint-card">
          <h3>${escapeHtml(t("constraint"))} ${row.index}</h3>
          <div class="latex-card">${mathMarkup(row.equation_latex)}</div>
          <p class="mono">${escapeHtml(row.equation)}</p>
          <div class="selector-list">
            <div class="selector-item"><span class="math-label">${selectorLabelMarkup("q_L")}</span><strong>${row.selectors.q_L}</strong></div>
            <div class="selector-item"><span class="math-label">${selectorLabelMarkup("q_R")}</span><strong>${row.selectors.q_R}</strong></div>
            <div class="selector-item"><span class="math-label">${selectorLabelMarkup("q_M")}</span><strong>${row.selectors.q_M}</strong></div>
            <div class="selector-item"><span class="math-label">${selectorLabelMarkup("q_C")}</span><strong>${row.selectors.q_C}</strong></div>
            <div class="selector-item"><span class="math-label">${selectorLabelMarkup("q_O")}</span><strong>${row.selectors.q_O}</strong></div>
          </div>
          <div class="selector-item"><span>${escapeHtml(t("binary_row"))}</span><strong>${row.binary ? escapeHtml(t("yes")) : escapeHtml(t("no"))}</strong></div>
        </article>
      `
    )
    .join("");
}

function updateSummary(summary) {
  heroConstraintCount.textContent = summary.constraint_count;
  heroGroupOrder.textContent = summary.group_order;
  heroPublicCount.textContent = summary.binary_rows;
  metricRows.textContent = summary.constraint_count;
  metricWidth.textContent = summary.binary_rows;
}

async function generateSelectors({ silentOnError = false } = {}) {
  setStatus(t("status_visualizing"), t("state_running"));
  generateButton.disabled = true;

  try {
    const rows = parseRawSelectors(programInput.value);
    const payload = buildLocalPayload(rows, groupOrderInput.value.trim());

    updateSummary(payload.summary);
    renderTable(payload.selectors);
    renderCards(payload.selectors);
    jsonOutput.textContent = JSON.stringify(payload, null, 2);
    rerenderMath();
    setStatus(t("status_updated"), t("state_ready"));
  } catch (error) {
    renderTable([]);
    renderCards([]);
    jsonOutput.textContent = JSON.stringify({ error: error.message }, null, 2);
    setStatus(error.message, t("state_error"));
    if (!silentOnError) console.error(error);
  } finally {
    generateButton.disabled = false;
  }
}

function applyTranslations() {
  document.body.classList.toggle("lang-en", currentLang === "en");
  document.body.classList.toggle("lang-zh", currentLang === "zh");
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-tooltip]").forEach((node) => {
    node.setAttribute("data-tooltip", t(node.dataset.i18nTooltip));
  });
  document.querySelector(".grid-note").innerHTML = `
    ${escapeHtml(t("grid_note_prefix"))}
    <span class="math-label">q<sub>L</sub></span>,
    <span class="math-label">q<sub>R</sub></span>,
    <span class="math-label">q<sub>M</sub></span>,
    <span class="math-label">q<sub>C</sub></span>,
    <span class="math-label">q<sub>O</sub></span>.
  `;
  programInput.placeholder = `Example:\n1 1 0 1 1\n0 0 1 0 1`;
  document.querySelectorAll("[data-lang-option]").forEach((node) => {
    node.classList.toggle("is-active", node.dataset.langOption === currentLang);
  });
  renderEditorGrid();
  renderCards([]);
}

function hideTooltip() {
  floatingTooltip.hidden = true;
}

function showTooltip(target) {
  const message = target.getAttribute("data-tooltip");
  if (!message) return;
  floatingTooltip.textContent = message;
  floatingTooltip.hidden = false;

  const rect = target.getBoundingClientRect();
  const tooltipRect = floatingTooltip.getBoundingClientRect();
  const top = Math.max(12, rect.top - tooltipRect.height - 10);
  const left = Math.min(
    window.innerWidth - tooltipRect.width - 12,
    Math.max(12, rect.left + rect.width / 2 - tooltipRect.width / 2)
  );

  floatingTooltip.style.left = `${left}px`;
  floatingTooltip.style.top = `${top}px`;
}

document.querySelectorAll("[data-sample]").forEach((button) => {
  button.addEventListener("click", () => {
    setEditorRows(samples[button.dataset.sample]);
    const sampleName = button.dataset.sample === "binary" ? t("sample_binary_name") : t("sample_mixed_name");
    setStatus(t("status_loaded", { name: sampleName }), t("state_ready"));
    scheduleLivePreview();
  });
});

addRowButton.addEventListener("click", () => {
  editorRows.push([0, 0, 0, 0, 1]);
  renderEditorGrid();
  syncRawTextareaFromGrid();
  scheduleLivePreview();
});

selectorEditorBody.addEventListener("input", (event) => {
  const target = event.target;
  if (!target.matches(".grid-input")) return;

  const rowIndex = Number(target.dataset.row);
  const colIndex = Number(target.dataset.col);
  const parsed = Number(target.value);
  editorRows[rowIndex][colIndex] = Number.isFinite(parsed) ? parsed : 0;
  renderEditorGrid();
  syncRawTextareaFromGrid();
  scheduleLivePreview();
});

selectorEditorBody.addEventListener("click", (event) => {
  const target = event.target;
  if (!target.matches("[data-delete-row]")) return;

  const rowIndex = Number(target.dataset.deleteRow);
  editorRows.splice(rowIndex, 1);
  if (!editorRows.length) editorRows.push([0, 0, 0, 0, 1]);
  renderEditorGrid();
  syncRawTextareaFromGrid();
  scheduleLivePreview();
});

programInput.addEventListener("input", () => {
  if (suppressRawSync) return;
  try {
    const parsedRows = parseRawSelectors(programInput.value);
    if (parsedRows.length && parsedRows.every((row) => row.length === 5 && row.every(Number.isFinite))) {
      editorRows = parsedRows;
      renderEditorGrid();
      scheduleLivePreview();
    }
  } catch (_error) {
    setStatus(t("status_raw_incomplete"), t("state_editing"));
  }
});

document.querySelector("#clearSelectors").addEventListener("click", () => {
  setEditorRows([[0, 0, 0, 0, 1]]);
  renderTable([]);
  renderCards([]);
  jsonOutput.textContent = JSON.stringify({ summary: null, selectors: [] }, null, 2);
  heroConstraintCount.textContent = "0";
  heroGroupOrder.textContent = "0";
  heroPublicCount.textContent = "0";
  metricRows.textContent = "0";
  metricWidth.textContent = "0";
  setStatus(t("status_cleared"), t("state_idle"));
});

document.querySelector("#copyProgramButton").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(programInput.value);
    setStatus(t("status_copied"), t("state_ready"));
  } catch (_error) {
    setStatus(t("status_clipboard_blocked"), t("state_idle"));
  }
});

generateButton.addEventListener("click", () => generateSelectors());
groupOrderInput.addEventListener("input", scheduleLivePreview);

document.addEventListener("keydown", (event) => {
  const isSubmitShortcut = (event.ctrlKey || event.metaKey) && event.key === "Enter";
  if (isSubmitShortcut) {
    event.preventDefault();
    generateSelectors();
  }
});

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((item) => item.classList.remove("is-active"));
    document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.remove("is-active"));
    tab.classList.add("is-active");
    document.querySelector(`[data-panel="${tab.dataset.tab}"]`).classList.add("is-active");
  });
});

langToggle.addEventListener("click", () => {
  currentLang = currentLang === "en" ? "zh" : "en";
  applyTranslations();
  setStatus(t("status_ready"), t("state_idle"));
  scheduleLivePreview();
});

document.addEventListener("mouseover", (event) => {
  const target = event.target.closest(".info-badge");
  if (!target) return;
  showTooltip(target);
});

document.addEventListener("mouseout", (event) => {
  const target = event.target.closest(".info-badge");
  if (!target) return;
  hideTooltip();
});

document.addEventListener("focusin", (event) => {
  const target = event.target.closest(".info-badge");
  if (!target) return;
  showTooltip(target);
});

document.addEventListener("focusout", (event) => {
  const target = event.target.closest(".info-badge");
  if (!target) return;
  hideTooltip();
});

window.addEventListener("scroll", hideTooltip, true);
window.addEventListener("resize", hideTooltip);

setEditorRows(samples.binary);
jsonOutput.textContent = JSON.stringify({ summary: null, selectors: [] }, null, 2);
applyTranslations();
setStatus(t("status_ready"), t("state_idle"));
scheduleLivePreview();
