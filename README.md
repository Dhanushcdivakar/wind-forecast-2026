UK Wind Forecast Analytics (January 2026)

A full-stack decision-support and analytics platform designed for a UK energy utility procuring electricity through the day-ahead wholesale market.

The application retrieves national wind generation data from the official Elexon BMRS API, selects eligible day-ahead forecast vintages, and quantitatively evaluates forecast performance using Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), and Mean Bias Error (MBE). These insights help energy procurement teams understand forecast uncertainty when planning supplemental electricity purchases.

🌐 Live Deployed Application

- Frontend Application: https://wind-forecast-six.vercel.app/
- Backend API: https://wind-forecast-2026.vercel.app/
- Interactive API Documentation: https://wind-forecast-2026.vercel.app/docs

📁 Repository Components

The repository is organized into the following main components.

Backend — backend/

The backend is implemented in Python using FastAPI.

- app/ — Contains the FastAPI application, configuration, REST endpoints, Elexon data retrieval, and forecast analytics.
- api/ — Contains the Vercel serverless entry point.
- tests/ — Contains backend unit tests for analytics and forecast selection.
- requirements.txt — Lists Python dependencies.
- Dockerfile — Defines the backend Docker image.
- vercel.json — Configures the backend Vercel deployment.
- pytest.ini — Contains Pytest configuration.
- .env.example — Provides an example of environment variable configuration.

Frontend — frontend/

The frontend is implemented using React and Vite.

- src/ — Contains the React application, API client, and styling.
- package.json — Defines frontend dependencies and npm scripts.
- vite.config.js — Configures Vite.
- Dockerfile — Builds the frontend and serves the production files using Nginx.
- vercel.json — Configures frontend routing for Vercel.

Root-Level Configuration

- docker-compose.yml — Defines the frontend and backend services for local execution.
- .gitignore — Excludes generated files, local environments, and sensitive configuration from Git tracking.
- README.md — Documents the project, setup instructions, methodology, and deployment details.

🚀 Running the Application with Docker

Prerequisites

- Docker
- Docker Compose

Start the application

Run the following command from the repository root:

docker compose up --build

Once the containers are running, access the application at:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Interactive API documentation: http://localhost:8000/docs

To stop the containers, press Ctrl+C and run:

docker compose down

Docker architecture

- Backend: Uses Python 3.12 and Uvicorn to run the FastAPI application.
- Frontend: Uses Node.js to build the React + Vite application and Nginx to serve the production files.
- Docker Compose: Configures the frontend and backend services, environment variables, port mappings, and startup order.

The Docker Compose configuration uses http://localhost:8000 for local browser-to-backend API requests. The deployed frontend uses the separately deployed Vercel backend.

💻 Running Locally Without Docker

Prerequisites

- Node.js 20 or later
- Python 3.11 or later

1. Start the backend

From the repository root:

cd backend
python3 -m venv .venv

Activate the virtual environment.

macOS/Linux:

source .venv/bin/activate

Windows PowerShell:

.venv\Scripts\Activate.ps1

Install the dependencies:

pip install -r requirements.txt

Start the FastAPI application:

uvicorn app.main:app --reload --port 8000

The backend will be available at:

http://localhost:8000

Interactive API documentation:

http://localhost:8000/docs

2. Start the frontend

Open a separate terminal from the repository root:

cd frontend
npm install
npm run dev

Open the frontend at:

http://localhost:5173

Ensure the frontend API configuration points to the appropriate backend:

- Local development: http://localhost:8000
- Deployed application: https://wind-forecast-2026.vercel.app

🧪 Running Tests

The backend includes unit tests implemented with Pytest.

From the repository root:

cd backend
pytest -v

📊 Methodology and Data Sources

Data source

The application uses the official Elexon BMRS API:

https://data.elexon.co.uk/bmrs/api/v1/datasets

Actual wind generation

- Dataset: FUELHH
- Filter: fuelType = WIND
- Source resolution: Half-hourly settlement intervals.
- Processing: Two half-hourly actual generation values are averaged to produce each complete hourly actual.

Forecasted wind generation

- Dataset: WINDFOR
- startTime: Target time for the forecast.
- publishTime: Time at which the forecast was published.
- generation: Forecast wind generation in MW.

Evaluation period

- Start date: January 1, 2026
- End date: January 31, 2026
- Expected hourly intervals: 744

Forecast selection rule

For each delivery date, the application selects the latest forecast published before 00:00 UTC on that delivery date.

This rule restricts the evaluation to forecasts available before the delivery day, reflecting the information available at the day-ahead purchasing decision cutoff.

Forecast accuracy metrics

Mean Absolute Error (MAE)

Measures the average absolute difference between forecast and actual generation.

Root Mean Squared Error (RMSE)

Penalizes larger forecasting errors more heavily than MAE.

Mean Bias Error (MBE)

Measures the average signed difference:

MBE = Forecast − Actual

- Positive MBE indicates systematic overestimation.
- Negative MBE indicates systematic underestimation.
- MBE near zero indicates low average signed bias, although individual errors may still be large.

January 2026 evaluation results

The deployed backend returned the following results:

Metric Result
MAE 1,935.73 MW
RMSE 2,406.10 MW
MBE +1,713.72 MW
Matched hourly intervals 744
Expected hourly intervals 744
Coverage 100%
Average actual generation 11,580.74 MW
Average selected forecast 13,294.46 MW
Incomplete actual hours 0
Hours without eligible forecasts 0

The positive MBE indicates that the selected forecasts overestimated actual wind generation on average during the evaluation period.

🤖 AI Assistance Disclosure

AI tools were used to assist with scaffolding, debugging, implementation guidance, and refinement of parts of the codebase. The application was tested during development.
