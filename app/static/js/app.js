import { getFile, getMeasurements, uploadFile, uploadSample } from "./api.js";
import { initMap, refreshMap, renderMap, selectFeature } from "./map.js";
import { areaValue, download, formatBytes, lengthValue, pageSize, toCsv, toGeoJson } from "./utils.js";

const state = {
  selectedFile: null,
  fileId: null,
  fileInfo: null,
  measurements: null,
  offset: 0,
  areaUnit: "m2",
  lengthUnit: "m",
};

const el = {
  dropZone: document.querySelector("#dropZone"),
  fileInput: document.querySelector("#fileInput"),
  browseButton: document.querySelector("#browseButton"),
  uploadButton: document.querySelector("#uploadButton"),
  sampleButton: document.querySelector("#sampleButton"),
  selectedFile: document.querySelector("#selectedFile"),
  progress: document.querySelector("#progress"),
  alertHost: document.querySelector("#alertHost"),
  liveStatus: document.querySelector("#liveStatus"),
  emptyState: document.querySelector("#emptyState"),
  results: document.querySelector("#results"),
  fileName: document.querySelector("#fileName"),
  fileStatus: document.querySelector("#fileStatus"),
  featureCount: document.querySelector("#featureCount"),
  sourceCrs: document.querySelector("#sourceCrs"),
  fileError: document.querySelector("#fileError"),
  totalArea: document.querySelector("#totalArea"),
  totalLength: document.querySelector("#totalLength"),
  polygonCount: document.querySelector("#polygonCount"),
  lineCount: document.querySelector("#lineCount"),
  pointCount: document.querySelector("#pointCount"),
  unsupportedCount: document.querySelector("#unsupportedCount"),
  areaUnit: document.querySelector("#areaUnit"),
  lengthUnit: document.querySelector("#lengthUnit"),
  tableBody: document.querySelector("#tableBody"),
  textFilter: document.querySelector("#textFilter"),
  typeFilter: document.querySelector("#typeFilter"),
  pageInfo: document.querySelector("#pageInfo"),
  prevButton: document.querySelector("#prevButton"),
  nextButton: document.querySelector("#nextButton"),
  csvButton: document.querySelector("#csvButton"),
  geojsonButton: document.querySelector("#geojsonButton"),
};

initMap((index) => highlightRow(index));
wireEvents();
loadFromHash();

function wireEvents() {
  el.browseButton.addEventListener("click", () => el.fileInput.click());
  el.dropZone.addEventListener("click", () => el.fileInput.click());
  el.dropZone.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") el.fileInput.click();
  });
  el.fileInput.addEventListener("change", () => setSelectedFile(el.fileInput.files[0]));
  ["dragenter", "dragover"].forEach((name) => el.dropZone.addEventListener(name, (event) => {
    event.preventDefault();
    el.dropZone.classList.add("dragging");
  }));
  ["dragleave", "drop"].forEach((name) => el.dropZone.addEventListener(name, () => el.dropZone.classList.remove("dragging")));
  el.dropZone.addEventListener("drop", (event) => {
    event.preventDefault();
    setSelectedFile(event.dataTransfer.files[0]);
  });
  el.uploadButton.addEventListener("click", onUpload);
  el.sampleButton.addEventListener("click", onSample);
  el.areaUnit.addEventListener("change", () => {
    state.areaUnit = el.areaUnit.value;
    renderResults();
  });
  el.lengthUnit.addEventListener("change", () => {
    state.lengthUnit = el.lengthUnit.value;
    renderResults();
  });
  el.textFilter.addEventListener("input", renderTable);
  el.typeFilter.addEventListener("change", renderTable);
  el.prevButton.addEventListener("click", () => changePage(-pageSize));
  el.nextButton.addEventListener("click", () => changePage(pageSize));
  el.csvButton.addEventListener("click", () => download("measurements.csv", "text/csv", toCsv(state.measurements.features)));
  el.geojsonButton.addEventListener("click", () => download("features.geojson", "application/geo+json", toGeoJson(state.measurements.features)));
}

function setSelectedFile(file) {
  clearAlert();
  if (!file) return;
  const suffix = file.name.toLowerCase().split(".").pop();
  if (!["zip", "kml"].includes(suffix)) {
    showAlert("Please choose a .zip Shapefile or .kml file.");
    return;
  }
  state.selectedFile = file;
  el.selectedFile.textContent = `${file.name} (${formatBytes(file.size)})`;
  el.uploadButton.disabled = false;
}

async function onUpload() {
  if (!state.selectedFile) return;
  await runBusy(async () => {
    const info = await uploadFile(state.selectedFile);
    await loadFile(info.id, true);
  }, "Uploading and measuring file...");
}

async function onSample() {
  await runBusy(async () => {
    const info = await uploadSample();
    await loadFile(info.id, true);
  }, "Uploading bundled sample...");
}

async function loadFromHash() {
  const match = window.location.hash.match(/^#\/files\/([A-Za-z0-9-]+)$/);
  if (match) {
    await runBusy(() => loadFile(match[1], false), "Loading shared file...");
  }
}

async function loadFile(id, updateHash) {
  state.fileId = id;
  state.offset = 0;
  state.fileInfo = await getFile(id);
  if (state.fileInfo.status === "COMPLETED") {
    state.measurements = await getMeasurements(id, pageSize, state.offset);
  } else {
    state.measurements = null;
  }
  if (updateHash) window.location.hash = `#/files/${id}`;
  renderResults();
}

async function changePage(delta) {
  const nextOffset = Math.max(0, state.offset + delta);
  if (!state.fileId || nextOffset === state.offset) return;
  state.offset = nextOffset;
  state.measurements = await getMeasurements(state.fileId, pageSize, state.offset);
  renderResults();
}

async function runBusy(fn, message) {
  try {
    setBusy(true, message);
    await fn();
  } catch (error) {
    showAlert(error.message);
  } finally {
    setBusy(false, "");
  }
}

function setBusy(isBusy, message) {
  el.progress.hidden = !isBusy;
  el.uploadButton.disabled = isBusy || !state.selectedFile;
  el.sampleButton.disabled = isBusy;
  el.liveStatus.textContent = message;
}

function renderResults() {
  if (!state.fileInfo) return;
  el.emptyState.hidden = true;
  el.results.hidden = false;
  refreshMap();
  renderFileInfo();
  if (state.measurements) {
    renderSummary();
    renderTable();
    renderMap(state.measurements.features, { area: state.areaUnit, length: state.lengthUnit }, { area: areaValue, length: lengthValue });
  }
}

function renderFileInfo() {
  const info = state.fileInfo;
  el.fileName.textContent = info.filename;
  el.fileStatus.textContent = info.status;
  el.fileStatus.className = `badge ${info.status.toLowerCase()}`;
  el.featureCount.textContent = info.feature_count;
  el.sourceCrs.textContent = info.crs || "-";
  el.fileError.hidden = !info.error_message;
  el.fileError.textContent = info.error_message || "";
}

function renderSummary() {
  const summary = state.measurements.summary;
  el.totalArea.textContent = areaValue(summary.total_area_m2, state.areaUnit);
  el.totalLength.textContent = lengthValue(summary.total_length_m, state.lengthUnit);
  el.polygonCount.textContent = summary.polygon_count;
  el.lineCount.textContent = summary.line_count;
  el.pointCount.textContent = summary.point_count;
  el.unsupportedCount.textContent = summary.unsupported_count;
  el.prevButton.disabled = state.offset === 0;
  el.nextButton.disabled = state.offset + state.measurements.limit >= state.measurements.total;
  el.pageInfo.textContent = `${state.offset + 1}-${Math.min(state.offset + state.measurements.limit, state.measurements.total)} of ${state.measurements.total}`;
}

function renderTable() {
  const rows = filteredFeatures();
  el.tableBody.replaceChildren(...rows.map(rowElement));
}

function filteredFeatures() {
  const text = el.textFilter.value.trim().toLowerCase();
  const type = el.typeFilter.value;
  return state.measurements.features.filter((feature) => {
    const matchesType = !type || feature.geometry_type.includes(type);
    const haystack = `${feature.index} ${feature.geometry_type} ${JSON.stringify(feature.properties)}`.toLowerCase();
    return matchesType && (!text || haystack.includes(text));
  });
}

function rowElement(feature) {
  const tr = document.createElement("tr");
  tr.dataset.index = feature.index;
  tr.addEventListener("click", () => {
    highlightRow(feature.index);
    selectFeature(feature.index);
  });
  [
    feature.index,
    feature.geometry_type,
    areaValue(feature.area_m2, state.areaUnit),
    lengthValue(feature.length_m, state.lengthUnit),
  ].forEach((value) => tr.appendChild(cell(value)));
  tr.appendChild(statusCell(feature.measurement_status));
  tr.appendChild(cell(feature.projected_crs_used || "-"));
  tr.appendChild(propertiesCell(feature.properties));
  return tr;
}

function cell(value) {
  const td = document.createElement("td");
  td.textContent = value;
  return td;
}

function statusCell(status) {
  const td = document.createElement("td");
  const chip = document.createElement("span");
  chip.className = `chip ${status.toLowerCase()}`;
  chip.title = {
    OK: "Measured successfully.",
    NOT_REQUIRED: "This feature type does not need area or length.",
    UNSUPPORTED: "This geometry type is kept but not measured.",
    ERROR: "This feature had a measurement problem.",
  }[status];
  chip.textContent = status;
  td.appendChild(chip);
  return td;
}

function propertiesCell(properties) {
  const td = document.createElement("td");
  const details = document.createElement("details");
  const summary = document.createElement("summary");
  summary.textContent = "view";
  const box = document.createElement("div");
  box.className = "properties";
  const dl = document.createElement("dl");
  Object.entries(properties || {}).forEach(([key, value]) => {
    const row = document.createElement("div");
    const dt = document.createElement("dt");
    const dd = document.createElement("dd");
    dt.textContent = key;
    dd.textContent = value == null ? "" : String(value);
    row.append(dt, dd);
    dl.appendChild(row);
  });
  box.appendChild(dl);
  details.append(summary, box);
  td.appendChild(details);
  return td;
}

function highlightRow(index) {
  document.querySelectorAll("tbody tr").forEach((row) => row.classList.toggle("active", Number(row.dataset.index) === Number(index)));
}

function showAlert(message) {
  const alert = document.createElement("div");
  alert.className = "alert";
  const text = document.createElement("span");
  text.textContent = message;
  const close = document.createElement("button");
  close.className = "secondary";
  close.type = "button";
  close.textContent = "Dismiss";
  close.addEventListener("click", clearAlert);
  alert.append(text, close);
  el.alertHost.replaceChildren(alert);
}

function clearAlert() {
  el.alertHost.replaceChildren();
}
