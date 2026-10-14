const nspLabels = { 1: "Норма", 2: "Подозрительный", 3: "Патологический" };
const nspStyles = { 1: "normal", 2: "suspect", 3: "pathological" };
const featureDescriptions = {
  LB: "Базальная частота", AC: "Акцелерации", FM: "Движения плода", UC: "Сокращения матки",
  ASTV: "Доля аномальной краткосрочной вариабельности", MSTV: "Средняя краткосрочная вариабельность",
  ALTV: "Доля аномальной долгосрочной вариабельности", MLTV: "Средняя долгосрочная вариабельность",
  DL: "Лёгкие децелерации", DS: "Выраженные децелерации", DP: "Продолжительные децелерации",
  Min: "Минимум гистограммы", Max: "Максимум гистограммы", Nmax: "Количество пиков", Nzeros: "Количество нулей",
  Mode: "Мода гистограммы", Mean: "Среднее гистограммы", Median: "Медиана гистограммы",
  Variance: "Дисперсия гистограммы", Tendency: "Смещение гистограммы", duration: "Длительность сегмента",
};
const numberFormat = new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 3 });
const timeFormat = new Intl.DateTimeFormat("ru-RU", { hour: "2-digit", minute: "2-digit" });
const dateFormat = new Intl.DateTimeFormat("ru-RU", { day: "2-digit", month: "2-digit" });
const byId = (id) => document.getElementById(id);
const caseSelect = byId("case-select");
const submitButton = byId("submit-button");
const dialog = byId("record-dialog");
let demoCases = [];
let records = [];
let activeRecord = null;
let latestRecordId = null;

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function deleteButton(record) {
  const button = element("button", "delete-button");
  button.type = "button";
  button.setAttribute("aria-label", `Удалить исследование ${record.record_id}`);
  button.title = "Удалить исследование";
  button.innerHTML = trashIcon;
  button.addEventListener("click", (event) => {
    event.stopPropagation();
    deleteRecord(record, button);
  });
  return button;
}

const trashIcon = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 10v7M14 10v7"/></svg>';

async function deleteRecord(record, button) {
  button.disabled = true;
  try {
    await request(`/records/${encodeURIComponent(record.record_id)}`, { method: "DELETE" });
    if (activeRecord?.record_id === record.record_id) {
      dialog.close();
      activeRecord = null;
    }
    await refreshRecords();
  } catch (error) {
    showError(error.message);
  } finally {
    button.disabled = false;
  }
}

function nspBadge(category) {
  return element("span", `badge nsp ${nspStyles[category.code]}`, nspLabels[category.code]);
}

function patternBadge(category) {
  return element("span", "badge pattern", category.label);
}

function comparisonMarker(predicted, reference) {
  const correct = predicted.code === reference.code;
  return element("span", `comparison-marker ${correct ? "correct" : "incorrect"}`, correct ? "✓ Верно" : "× Ошибка");
}

function renderClassification(container, classification, reference = null) {
  const nsp = element("span", "classification-value");
  const pattern = element("span", "classification-value");
  nsp.append(nspBadge(classification.nsp));
  pattern.append(patternBadge(classification.class));
  if (reference) {
    nsp.append(comparisonMarker(classification.nsp, reference.nsp));
    pattern.append(comparisonMarker(classification.class, reference.class));
  }
  container.replaceChildren(nsp, pattern);
}

async function request(path, options = {}) {
  const response = await fetch(path, { ...options, signal: AbortSignal.timeout(10000) });
  if (!response.ok) {
    const body = response.headers.get("content-type")?.includes("application/json") ? await response.json() : {};
    throw new Error(typeof body.detail === "string" ? body.detail : `Не удалось выполнить запрос (${response.status}).`);
  }
  return response.status === 204 ? null : response.json();
}

function showError(message) {
  byId("error-banner").textContent = message;
  byId("error-banner").hidden = false;
}

function updateSelectedCase() {
  const selected = demoCases.find((item) => item.case_id === caseSelect.value);
  renderClassification(byId("case-truth"), selected.reference);
  byId("submit-feedback").textContent = "";
}

async function loadDemoCases() {
  demoCases = await request("/demo/cases");
  caseSelect.replaceChildren(...demoCases.map((item) => {
    const option = element("option", "", `${item.case_id} — ${item.reference.class.label}`);
    option.value = item.case_id;
    return option;
  }));
  caseSelect.disabled = demoCases.length === 0;
  submitButton.disabled = demoCases.length === 0;
  if (demoCases.length) updateSelectedCase();
}

function openRecord(record) {
  activeRecord = record;
  byId("dialog-title").textContent = record.record_id;
  const date = new Date(record.created_at);
  byId("dialog-meta").textContent = `${dateFormat.format(date)} в ${timeFormat.format(date)} · Контрольный ${record.case_id}`;
  renderClassification(byId("dialog-prediction"), record.prediction, byId("show-truth").checked ? record.reference : null);
  renderClassification(byId("dialog-reference"), record.reference);
  byId("dialog-reference-block").hidden = !byId("show-truth").checked;
  byId("dialog-features").replaceChildren(...Object.entries(featureDescriptions).map(([name, description]) => {
    const item = element("div", "feature-item");
    item.append(element("span", "feature-code", name), element("strong", "", (name === "Tendency" ? { "-1": "Влево", 0: "Нет смещения", 1: "Вправо" }[record.features[name]] : numberFormat.format(record.features[name]))), element("p", "", description));
    return item;
  }));
  if (!dialog.open) dialog.showModal();
}

function renderRecords() {
  const showTruth = byId("show-truth").checked;
  document.querySelectorAll("th.truth-column").forEach((cell) => { cell.hidden = !showTruth; });
  byId("record-count").textContent = records.length;
  byId("empty-state").hidden = records.length > 0;
  byId("records-table").hidden = records.length === 0;
  for (const [code, id] of [[1, "normal"], [2, "suspect"], [3, "pathological"]]) {
    byId(`count-${id}`).textContent = records.filter((record) => record.prediction.nsp.code === code).length;
  }
  const sorted = [...records].sort((first, second) => {
    if (byId("sort-select").value === "priority") {
      const priority = second.prediction.nsp.code - first.prediction.nsp.code;
      if (priority) return priority;
    }
    return new Date(second.created_at) - new Date(first.created_at);
  });
  byId("records-body").replaceChildren(...sorted.map((record) => {
    const row = element("tr", record.record_id === latestRecordId ? "new-record" : "");
    const idCell = element("td");
    idCell.append(element("button", "record-link", record.record_id), element("div", "record-subtitle", `Контрольный ${record.case_id}`));
    const date = new Date(record.created_at);
    const timeCell = element("td", "time-cell", timeFormat.format(date));
    timeCell.title = date.toLocaleString("ru-RU");
    const priorityCell = element("td");
    priorityCell.append(nspBadge(record.prediction.nsp));
    const patternCell = element("td");
    patternCell.append(patternBadge(record.prediction.class));
    if (showTruth) {
      priorityCell.append(comparisonMarker(record.prediction.nsp, record.reference.nsp));
      patternCell.append(comparisonMarker(record.prediction.class, record.reference.class));
    }
    row.append(idCell, timeCell, priorityCell);
    if (showTruth) {
      const nspCell = element("td", "truth-column");
      nspCell.append(nspBadge(record.reference.nsp));
      row.append(nspCell);
    }
    row.append(patternCell);
    if (showTruth) {
      const classCell = element("td", "truth-column");
      classCell.append(patternBadge(record.reference.class));
      row.append(classCell);
    }
    const actionsCell = element("td", "actions-cell");
    actionsCell.append(deleteButton(record));
    row.append(actionsCell);
    row.addEventListener("click", () => openRecord(record));
    return row;
  }));
  latestRecordId = null;
}

async function refreshRecords() {
  records = await request("/records");
  renderRecords();
  byId("sync-status").textContent = `Обновлено ${timeFormat.format(new Date())}`;
  byId("sync-status").classList.remove("offline");
  byId("error-banner").hidden = true;
}

async function submitDemo(event) {
  event.preventDefault();
  submitButton.disabled = true;
  byId("submit-label").textContent = "Отправляем…";
  byId("submit-feedback").textContent = "";
  try {
    const record = await request("/demo/records", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ case_id: caseSelect.value }),
    });
    latestRecordId = record.record_id;
    await refreshRecords();
    byId("submit-feedback").textContent = `Исследование ${record.record_id} поступило. Результат — в таблице.`;
  } catch (error) {
    showError(error.message);
  } finally {
    byId("submit-label").textContent = "Отправить";
    submitButton.disabled = false;
  }
}

async function pollRecords() {
  try {
    await refreshRecords();
  } catch (error) {
    byId("sync-status").textContent = "Нет соединения";
    byId("sync-status").classList.add("offline");
    showError("Не удалось обновить исследования. Проверьте, запущен ли сервис.");
  }
}

byId("demo-form").addEventListener("submit", submitDemo);
caseSelect.addEventListener("change", updateSelectedCase);
byId("sort-select").addEventListener("change", renderRecords);
byId("show-truth").addEventListener("change", () => {
  renderRecords();
  if (activeRecord) {
    byId("dialog-reference-block").hidden = !byId("show-truth").checked;
    renderClassification(byId("dialog-prediction"), activeRecord.prediction, byId("show-truth").checked ? activeRecord.reference : null);
  }
});
byId("delete-dialog-record").innerHTML = trashIcon;
byId("delete-dialog-record").addEventListener("click", () => deleteRecord(activeRecord, byId("delete-dialog-record")));
byId("close-dialog").addEventListener("click", () => dialog.close());

async function initialize() {
  try {
    await Promise.all([loadDemoCases(), refreshRecords()]);
  } catch (error) {
    showError("Не удалось загрузить страницу. Проверьте, запущен ли сервис, и обновите страницу.");
    byId("sync-status").textContent = "Нет соединения";
    byId("sync-status").classList.add("offline");
  }
  setInterval(pollRecords, 5000);
}
initialize();
