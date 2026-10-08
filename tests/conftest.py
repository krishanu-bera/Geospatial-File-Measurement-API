from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_geo_measure.db")
os.environ.setdefault("UPLOAD_DIR", "test_uploads")
os.environ.setdefault("MAX_UPLOAD_MB", "5")

from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from sample_data.generate_samples import build_samples  # noqa: E402


@pytest.fixture(autouse=True)
def reset_database() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def samples(tmp_path: Path) -> dict[str, Path]:
    return build_samples(tmp_path)

