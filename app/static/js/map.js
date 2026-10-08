let map;
let layerGroup;
const layersByIndex = new Map();
let selectedLayer;

export function initMap(onSelect) {
  map = L.map("map", { scrollWheelZoom: true }).setView([20, 0], 2);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);
  layerGroup = L.layerGroup().addTo(map);
  map.on("popupopen", (event) => {
    const index = event.popup?._source?.feature?.properties?.index;
    if (index != null) onSelect(index);
  });
}

export function renderMap(features, units, formatters) {
  layerGroup.clearLayers();
  layersByIndex.clear();
  selectedLayer = null;
  const valid = features.filter((feature) => feature.geometry?.type && feature.geometry?.coordinates);
  const renderLimit = valid.length > 2000 ? 2000 : valid.length;
  const collection = {
    type: "FeatureCollection",
    features: valid.slice(0, renderLimit).map((feature) => ({
      type: "Feature",
      geometry: feature.geometry,
      properties: feature,
    })),
  };
  const geoLayer = L.geoJSON(collection, {
    style: styleFor,
    pointToLayer: (feature, latlng) => L.circleMarker(latlng, { radius: 7, ...styleFor(feature) }),
    onEachFeature: (feature, layer) => {
      const props = feature.properties;
      layersByIndex.set(props.index, layer);
      layer.bindPopup(popupText(props, units, formatters));
      layer.on("click", () => selectFeature(props.index));
    },
  }).addTo(layerGroup);
  refreshMap();
  if (valid.length) {
    const bounds = geoLayer.getBounds();
    if (bounds.isValid()) map.fitBounds(bounds.pad(0.15));
  }
}

export function refreshMap() {
  requestAnimationFrame(() => {
    map.invalidateSize();
  });
}

export function selectFeature(index) {
  const layer = layersByIndex.get(index);
  if (!layer) return;
  if (selectedLayer?.setStyle) selectedLayer.setStyle(styleFor(selectedLayer.feature));
  selectedLayer = layer;
  if (layer.setStyle) layer.setStyle({ color: "#e11d48", weight: 5, fillOpacity: 0.35 });
  if (layer.getBounds) map.fitBounds(layer.getBounds().pad(0.4));
  else if (layer.getLatLng) map.setView(layer.getLatLng(), Math.max(map.getZoom(), 15));
  layer.openPopup();
}

function styleFor(feature) {
  const type = feature.properties.geometry_type || "";
  if (type.includes("Polygon")) return { color: "#2f855a", fillColor: "#68d391", weight: 2, fillOpacity: 0.28 };
  if (type.includes("Line")) return { color: "#2563eb", weight: 4 };
  if (type.includes("Point")) return { color: "#d97706", fillColor: "#fbbf24", weight: 2, fillOpacity: 0.9 };
  return { color: "#b42318", weight: 3 };
}

function popupText(feature, units, formatters) {
  const lines = [
    `#${feature.index} ${feature.geometry_type}`,
    `Area: ${formatters.area(feature.area_m2, units.area)}`,
    `Length: ${formatters.length(feature.length_m, units.length)}`,
    `Status: ${feature.measurement_status}`,
    `Projected CRS: ${feature.projected_crs_used || "-"}`,
  ];
  return lines.map((line) => escapeHtml(line)).join("<br>");
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[ch]));
}
