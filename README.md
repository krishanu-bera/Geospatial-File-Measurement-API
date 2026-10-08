# Geospatial File Measurement API

A simple **FastAPI-based application** that lets you upload **KML files or zipped Shapefiles** and automatically calculates measurements for the geographic features inside them.

The application can calculate:

- 📐 **Area** for polygons
- 📏 **Length** for lines
- 📍 **Location information** for points
- ⚠️ Reports unsupported geometries without stopping the entire upload

It also includes a simple web interface where you can view the uploaded data on a map, check measurements, and export the results.

---

## 🚀 Features

- Upload `.kml` files
- Upload zipped `.shp` Shapefiles
- Calculate polygon area
- Calculate line length
- Keep point features for reference
- Automatically handle different coordinate systems
- Display data on an interactive map
- View measurements in a table
- Highlight features between the map and table
- Change measurement units
- Export results as CSV or GeoJSON
- REST API with Swagger documentation
- SQLite database for storing uploaded files and measurements
- Docker support
- Automated tests and code checks

---

## 🛠️ Technologies Used

### Backend
- Python
- FastAPI
- SQLAlchemy
- SQLite
- GeoPandas
- Pyogrio
- PyProj

### Frontend
- HTML
- CSS
- JavaScript
- Leaflet.js

### Development Tools
- Pytest
- Ruff
- Mypy
- Docker

---

# 📁 Project Structure

```text
project/
│
├── app/
│   ├── main.py
│   ├── api/
│   │   └── files.py
│   ├── services/
│   │   ├── reader.py
│   │   ├── measure.py
│   │   ├── crs.py
│   │   └── processor.py
│   ├── models.py
│   ├── schemas.py
│   └── static/
│       └── ...
│
├── sample_data/
├── tests/
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

### What the main files do

| File | Purpose |
|---|---|
| `main.py` | Starts the FastAPI application |
| `files.py` | Handles file upload and API requests |
| `reader.py` | Reads and validates KML/Shapefile files |
| `measure.py` | Calculates area and length |
| `crs.py` | Handles coordinate systems |
| `processor.py` | Controls the complete upload process |
| `models.py` | Database models |
| `schemas.py` | API response formats |
| `static/` | Web interface |
| `tests/` | Automated tests |

---

# ⚙️ Installation

## 1. Create a virtual environment

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

## 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

## 3. Generate sample files

```powershell
python sample_data\generate_samples.py
```

## 4. Start the server

```powershell
python -m uvicorn app.main:app --reload
```

---

# 🌐 Open the Application

Once the server starts, open:

**Web Interface**

```text
http://127.0.0.1:8000/
```

**Swagger API Documentation**

```text
http://127.0.0.1:8000/docs
```

**Health Check**

```text
http://127.0.0.1:8000/health
```

---

# 🖥️ Using the Web Interface

1. Open `http://127.0.0.1:8000/`
2. Upload a `.kml` file or `.zip` Shapefile.
3. You can also use **Try a sample file**.
4. The application processes the file.
5. View the features on the map.
6. Check the measurements in the table.
7. Change area or length units if needed.
8. Click a table row to highlight the feature on the map.
9. Click a map feature to highlight its table row.
10. Export the results as CSV or GeoJSON.

---

# 📐 How Measurements Work

The application treats different geometry types differently.

| Geometry | Measurement |
|---|---|
| Polygon | Area |
| LineString | Length |
| Point | `NOT_REQUIRED` |
| Unsupported geometry | Reported as unsupported |

For example:

```text
Polygon → 1,000,000 m²
Line    → 1,000 m
Point   → NOT_REQUIRED
```

The application also uses the correct projected coordinate system before calculating measurements so that results are not calculated directly from latitude/longitude degrees.

---

# 🔌 API

## Health Check

### `GET /health`

Checks whether the application is running.

Example response:

```json
{
  "status": "ok"
}
```

---

## Upload a File

### `POST /api/files/`

Upload a KML file or zipped Shapefile.

Example:

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/files/ `
  -F "file=@sample_data/sample.kml"
```

Example response:

```json
{
  "id": "a4d6ecf4-8433-4587-844f-c931ea7a0e5f",
  "filename": "sample.kml",
  "feature_count": 3,
  "crs": "EPSG:4326",
  "status": "COMPLETED",
  "error_message": null
}
```

---

## Get File Information

### `GET /api/files/{id}/`

Returns information about an uploaded file.

Example:

```powershell
curl.exe http://127.0.0.1:8000/api/files/FILE_ID/
```

---

## Get Measurements

### `GET /api/files/{id}/measurements/`

Returns the measurements calculated for the uploaded file.

Example:

```powershell
curl.exe "http://127.0.0.1:8000/api/files/FILE_ID/measurements/?limit=100&offset=0"
```

The response contains:

- File information
- Total area
- Total length
- Number of polygons
- Number of lines
- Number of points
- Unsupported feature count
- Individual feature measurements
- Geometry information
- Coordinate system information

---

# ❌ Error Handling

The API returns clear errors when something goes wrong.

Common status codes:

| Code | Meaning |
|---|---|
| `400` | Invalid or empty upload |
| `404` | File not found |
| `409` | File is still being processed |
| `413` | File is too large |
| `415` | Unsupported file type |
| `422` | File is corrupted or cannot be read |

Example:

```json
{
  "error": {
    "code": "unsupported_format",
    "message": "Only .zip Shapefiles and .kml files are supported."
  }
}
```

---

# ⚙️ Configuration

Create a `.env` file using `.env.example` as a template.

```text
UPLOAD_DIR=uploads
MAX_UPLOAD_MB=50
DATABASE_URL=sqlite:///./geo_measure.db
CORS_ORIGINS=
LOG_LEVEL=INFO
```

### Configuration options

| Setting | Description | Default |
|---|---|---|
| `UPLOAD_DIR` | Where uploaded files are stored | `uploads` |
| `MAX_UPLOAD_MB` | Maximum upload size | `50 MB` |
| `DATABASE_URL` | Database connection | SQLite |
| `CORS_ORIGINS` | Allowed frontend origins | Disabled |
| `LOG_LEVEL` | Logging level | `INFO` |

---

# 🧪 Running Tests

Run the automated tests:

```powershell
python -m pytest
```

Check code quality:

```powershell
ruff check .
```

Check type hints:

```powershell
mypy app --follow-imports=skip
```

---

# 🐳 Running With Docker

Build the Docker image:

```powershell
docker build -t geo-measure-api .
```

Run the application:

```powershell
docker run --rm -p 8000:8000 --env-file .env.example geo-measure-api
```

Then open:

```text
http://127.0.0.1:8000/
```

---

# 🗺️ How the Application Works

The overall process is:

```text
Upload File
     ↓
Validate File
     ↓
Read KML / Shapefile
     ↓
Extract Features
     ↓
Identify Geometry
     ↓
Select Suitable Coordinate System
     ↓
Calculate Area / Length
     ↓
Save Results
     ↓
Display Results on Map and Table
```

---

# 🏗️ Architecture

The application has four main parts:

### 1. File Upload

FastAPI receives the uploaded KML or zipped Shapefile.

### 2. File Processing

GeoPandas and Pyogrio read the geographic data.

### 3. Measurement

The application calculates:

- Polygon → Area
- Line → Length
- Point → No measurement required

PyProj is used to handle coordinate systems and geospatial calculations.

### 4. Frontend

The browser displays the results using Leaflet.

Users can:

- View features on the map
- Check measurements
- Change units
- Select features
- Export results

---

# 📊 Coordinate Systems

Geospatial files can use different coordinate systems.

The application automatically selects a suitable projected coordinate system before calculating area and length.

For example:

```text
Latitude / Longitude
        ↓
Suitable Projected CRS
        ↓
Area / Length Calculation
```

This prevents incorrect calculations caused by measuring distances directly in latitude/longitude degrees.

For files without a `.prj` file, the application assumes:

```text
EPSG:4326
```

and records this assumption in the feature information.

---

# ⚠️ Limitations

Currently:

- Processing is synchronous.
- Very large files may take longer to process.
- UTM is most accurate for local and regional data.
- Very large areas may have some projection distortion.
- Shapefiles without `.prj` files require the application to assume EPSG:4326.
- A single Shapefile layer normally contains one geometry type, so the mixed Polygon/Line/Point example is provided as KML.

---

# 🔮 Future Improvements

Possible future improvements include:

- Background/async file processing
- Celery or RQ task queue
- PostgreSQL + PostGIS
- User authentication
- Rate limiting
- GeoJSON support
- GeoPackage support
- Better handling of very large files
- CI/CD pipeline
- Map clustering
- More detailed validation reports

---

# ✅ Quick Verification

After starting the server, run:

```powershell
curl.exe http://127.0.0.1:8000/health
```

Upload a sample KML:

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/files/ `
  -F "file=@sample_data/sample.kml"
```

Upload a sample Shapefile:

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/files/ `
  -F "file=@sample_data/sample_shapefile.zip"
```

Run tests:

```powershell
python -m pytest
```

Run code checks:

```powershell
ruff check .
```

---

# 🎯 Project Summary

This project provides a simple way to **upload geographic files and automatically measure their features**.

It combines:

**FastAPI + GeoPandas + PyProj + SQLAlchemy + SQLite + Leaflet**

The main goal is to make geospatial measurement easy for both **developers through the REST API** and **non-technical users through the web interface**.