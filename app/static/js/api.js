export async function uploadFile(file) {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch("/api/files/", { method: "POST", body: form });
  return parseResponse(response);
}

export async function uploadSample() {
  const response = await fetch("/static/samples/sample.kml");
  const blob = await response.blob();
  return uploadFile(new File([blob], "sample.kml", { type: "application/vnd.google-earth.kml+xml" }));
}

export async function getFile(id) {
  const response = await fetch(`/api/files/${encodeURIComponent(id)}/`);
  return parseResponse(response);
}

export async function getMeasurements(id, limit = 100, offset = 0) {
  const response = await fetch(`/api/files/${encodeURIComponent(id)}/measurements/?limit=${limit}&offset=${offset}`);
  return parseResponse(response);
}

async function parseResponse(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = data?.error?.message || "Request failed.";
    const error = new Error(message);
    error.code = data?.error?.code || "request_failed";
    throw error;
  }
  return data;
}

