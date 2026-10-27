# UK Wind Forecast Analytics (January 2026)

A full-stack decision-support and analytics platform designed for a UK energy utility procuring power on the day-ahead wholesale electricity market. 

The application ingests national wind generation data directly from the official **Elexon BMRS API**, tracks day-ahead forecast vintages, and quantitatively evaluates forecast performance (MAE, RMSE, Bias/MBE) to help trading teams optimize supplemental thermal power procurement.

---

## 🌐 Live Deployed Application

- **Frontend App:** `[Insert your Vercel / Heroku link here]`
- **Backend API:** `[Insert your Backend API link here]`

---

## 📁 Repository Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── __init__.py       # Package initializer
│   │   ├── config.py         # App configuration, Elexon base URL & CORS settings
│   │   ├── main.py           # FastAPI application & REST endpoint definitions
│   │   └── services.py       # Elexon API data streaming, hourly aggregation & error metrics
│   ├── tests/
│   │   ├── test_services.py  # Pytest unit tests for analytics & cutoff selection
│   │   └── pytest.ini        # Pytest configuration
│   ├── Dockerfile            # Container configuration for backend
│   └── requirements.txt      # Python dependencies (FastAPI, httpx, pandas, uvicorn)
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Main React UI with Overview, Analysis, Accuracy & Explorer
│   │   ├── api.js            # API client for backend communication
│   │   ├── main.jsx          # React DOM root entrypoint
│   │   └── styles.css        # Responsive dashboard styling
│   ├── Dockerfile            # Multi-stage production container (Node + Nginx)
│   ├── package.json          # Frontend dependencies (React, Recharts, Lucide)
│   └── vite.config.js        # Vite bundler configuration
├── docker-compose.yml        # Orchestration to run full stack with a single command
└── README.md                 # Project documentation
```

---

## 🚀 How to Run the Application

### Option 1: Using Docker (Recommended)

Make sure Docker and Docker Compose are installed:

```bash
docker compose up --build
```
- Open the web application at: **http://localhost:5173**
- The backend API will be available at: **http://localhost:8000/docs**

---

### Option 2: Running Locally Without Docker

#### Prerequisites
- **Node.js**: v20+
- **Python**: v3.11+

#### 1. Backend Setup
```bash
cd backend
python3 -m venv .venv

# On macOS / Linux:
source .venv/bin/activate
# On Windows (PowerShell):
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
API Documentation will be live at: http://localhost:8000/docs

#### 2. Frontend Setup (in a separate terminal)
```bash
cd frontend
npm install
npm run dev
```
Open your browser at: http://localhost:5173

---

## 🧪 Running Tests

To run the backend unit tests:
```bash
cd backend
pytest -v
```

---

## 📊 Methodology & Data Sources

- **Data Source:** Official Elexon BMRS API (`https://data.elexon.co.uk/bmrs/api/v1/datasets`)
  - **Actual Generation:** Streamed from `FUELHH` filtered by `fuelType == "WIND"`. Half-hourly settlement intervals are averaged into complete hourly actuals.
  - **Forecasts:** Streamed from `WINDFOR` with `publishTime` and `startTime`.
- **Target Period:** January 1, 2026 to January 31, 2026 (744 total hours, 100% complete coverage).
- **Cutoff Decision Rule:** Selects the latest forecast published prior to 00:00 UTC on the delivery date.
- **Accuracy Metrics:**
  - **MAE (Mean Absolute Error):** Average absolute difference between forecast and actual generation.
  - **RMSE (Root Mean Squared Error):** Penalizes larger forecasting errors.
  - **Mean Bias Error (MBE):** Average signed difference (Forecast − Actual). Positive indicates systematic overestimation.

---

## 🤖 AI Assistance Disclosure
AI assistance was utilized to assist in scaffolding and refining parts of this codebase. All calculations, data streaming logic, and architectural designs have been reviewed and verified for correctness.
