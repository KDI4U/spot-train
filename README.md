# Spot Train API 🚆

Production-ready REST API for Indian Railways real-time train running status, PNR status enquiry, and train schedules.

---

## 🚀 Features

- **Live Train Running Status**: Real-time location, upcoming stations, delay, and arrival/departure information.
- **PNR Status Enquiry**: Live PNR status fetching and passenger details parsing.
- **Train Schedule Enquiry**: Full route and station-by-station schedule enquiry.
- **Interactive Documentation**: Built-in Swagger UI (`/docs`) and ReDoc (`/redoc`).
- **High Performance**: Optimized memory-based parsing without redundant disk I/O.
- **Production Ready**: Includes CORS middleware, environment-based configuration, Docker support, and automated test suite.

---

## 📁 Project Structure

```
SPOT_TRAIN/
├── app.py                      # FastAPI application entrypoint
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── Dockerfile                  # Production container definition
├── docker-compose.yml          # Docker Compose orchestration
├── run.bat                     # Windows standalone runner
├── train_status/               # Core application package
│   ├── routes/                 # API route controllers
│   │   ├── train_routes.py
│   │   ├── pnr_routes.py
│   │   └── enquiry_train_routes.py
│   ├── services/               # Business logic & upstream services
│   │   ├── train_service.py
│   │   ├── pnr_service.py
│   │   ├── ntes_service.py
│   │   └── enquiry_train_service.py
│   ├── parsers/                # HTML and JSON response parsers
│   │   ├── train_parser.py
│   │   ├── pnr_parser.py
│   │   └── enquiry_train_parser.py
│   ├── schemas/                # Pydantic request/response schemas
│   │   ├── pnr_schema.py
│   │   └── enquiry_train_schema.py
│   └── utils/                  # Constants and helpers
│       └── constants.py
└── tests/                      # Automated test suite
    ├── test_app.py
    ├── test_train.py
    └── test_pnr.py
```

---

## 🛠️ Quick Start

### 1. Prerequisites
- Python 3.10+
- Git

### 2. Setup Virtual Environment
```bash
# Clone the repository
git clone https://github.com/Urmila-International-Services-Pvt-ltd/railway_api.git
cd railway_api

# Create and activate virtual environment
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and add your credentials:
```bash
cp .env.example .env
```

```env
MMT_AUTHORIZATION=your_authorization_token_here
PORT=8001
HOST=127.0.0.1
```

### 4. Run Server
```bash
# Using Python
python app.py

# Or using Uvicorn directly
uvicorn app:app --host 127.0.0.1 --port 8001 --reload

# Or on Windows, double-click run.bat
```

Open browser at:
- **API Documentation (Swagger UI)**: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
- **ReDoc UI**: [http://127.0.0.1:8001/redoc](http://127.0.0.1:8001/redoc)
- **Health Check**: [http://127.0.0.1:8001/health](http://127.0.0.1:8001/health)

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | API status & welcome message |
| `GET` | `/health` | Service health check |
| `GET` | `/api/v1/train/spot/{train_no}?journey_date=DD-MM-YYYY` | Live running status of a train |
| `GET` | `/api/v1/train/test` | Train service health check |
| `POST` | `/api/v1/pnr/status` | Live PNR status enquiry |
| `GET` | `/api/v1/pnr/test` | PNR service health check |
| `POST` | `/enquiry/train/schedule` | Train timetable & schedule |

---

## 🧪 Running Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build -d

# View logs
docker-compose logs -f
```
