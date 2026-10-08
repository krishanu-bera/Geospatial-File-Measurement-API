from __future__ import annotations

import io
import zipfile
from pathlib import Path

from app.models import UploadedFile


def upload(client, path: Path):
    with path.open("rb") as handle:
        return client.post("/api/files/", files={"file": (path.name, handle)})


def test_health_and_ui(client):
    assert client.get("/health").json() == {"status": "ok"}
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert client.get("/static/css/styles.css").status_code == 200
    assert client.get("/static/samples/sample.kml").status_code == 200


def test_upload_valid_kml(client, samples):
    response = upload(client, samples["kml"])
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["feature_count"] == 3
    measurements = client.get(f"/api/files/{body['id']}/measurements/").json()
    assert measurements["summary"]["polygon_count"] == 1
    assert measurements["summary"]["line_count"] == 1
    assert measurements["summary"]["point_count"] == 1


def test_upload_valid_zipped_shapefile(client, samples):
    response = upload(client, samples["zip"])
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["feature_count"] == 3


def test_unsupported_extension(client):
    response = client.post("/api/files/", files={"file": ("bad.txt", io.BytesIO(b"x"))})
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_format"


def test_empty_file(client):
    response = client.post("/api/files/", files={"file": ("empty.kml", io.BytesIO(b""))})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_file"


def test_corrupt_zip(client):
    response = client.post("/api/files/", files={"file": ("bad.zip", io.BytesIO(b"not a zip"))})
    assert response.status_code == 422


def test_zip_missing_shp(client):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("readme.txt", "no shapefile")
    buffer.seek(0)
    response = client.post("/api/files/", files={"file": ("missing.zip", buffer)})
    assert response.status_code == 422


def test_pagination_and_404(client, samples):
    body = upload(client, samples["kml"]).json()
    response = client.get(f"/api/files/{body['id']}/measurements/?limit=1&offset=1")
    assert response.status_code == 200
    assert response.json()["limit"] == 1
    assert len(response.json()["features"]) == 1
    assert client.get("/api/files/does-not-exist/").status_code == 404


def test_409_for_non_completed_file(client):
    from app.db import SessionLocal

    db = SessionLocal()
    uploaded = UploadedFile(
        id="processing-id",
        filename="pending.kml",
        stored_path="pending.kml",
        status="PROCESSING",
    )
    db.add(uploaded)
    db.commit()
    db.close()
    response = client.get("/api/files/processing-id/measurements/")
    assert response.status_code == 409


def test_oversize_upload(client):
    oversized = io.BytesIO(b"x" * (6 * 1024 * 1024))
    response = client.post("/api/files/", files={"file": ("too-big.kml", oversized)})
    assert response.status_code == 413
