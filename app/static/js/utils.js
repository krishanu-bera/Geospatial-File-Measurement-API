export const pageSize = 100;

export function formatBytes(bytes) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** i).toFixed(i ? 1 : 0)} ${units[i]}`;
}

export function areaValue(m2, unit) {
  if (m2 == null) return "-";
  const factors = { m2: 1, hectares: 1 / 10000, km2: 1 / 1000000, acres: 0.000247105381 };
  const labels = { m2: "m²", hectares: "ha", km2: "km²", acres: "acres" };
  return `${formatNumber(m2 * factors[unit])} ${labels[unit]}`;
}

export function lengthValue(m, unit) {
  if (m == null) return "-";
  const factors = { m: 1, km: 1 / 1000, miles: 0.000621371, feet: 3.28084 };
  const labels = { m: "m", km: "km", miles: "mi", feet: "ft" };
  return `${formatNumber(m * factors[unit])} ${labels[unit]}`;
}

export function formatNumber(value) {
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 3 }).format(value);
}

export function download(filename, type, content) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function toCsv(features) {
  const header = ["index", "geometry_type", "area_m2", "length_m", "status", "projected_crs_used"];
  const rows = features.map((feature) => header.map((key) => csvCell(feature[key])).join(","));
  return [header.join(","), ...rows].join("\n");
}

export function toGeoJson(features) {
  return JSON.stringify({
    type: "FeatureCollection",
    features: features.filter((f) => f.geometry).map((f) => ({
      type: "Feature",
      geometry: f.geometry,
      properties: { ...f.properties, index: f.index, measurement_status: f.measurement_status },
    })),
  }, null, 2);
}

function csvCell(value) {
  const text = value == null ? "" : String(value);
  return `"${text.replaceAll('"', '""')}"`;
}

