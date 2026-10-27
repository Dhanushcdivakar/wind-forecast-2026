from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.services import elexon_data, analyse, ElexonError


app = FastAPI(
    title="Wind Forecast Analytics API",
    description="January 2026 UK national wind generation forecast analytics.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_cache = None


async def get_analysis():
    global _cache

    if _cache is None:
        try:
            raw = await elexon_data()

            if not raw.get("actuals") or not raw.get("forecasts"):
                raise ElexonError(
                    "Elexon returned no actual or forecast records for the requested period."
                )

            _cache = analyse(raw)

        except ElexonError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to retrieve real Elexon data: {exc}",
            ) from exc

    return _cache


@app.get("/api/health")
async def health():
    return {"status": "ok", "data_mode": "elexon"}


@app.get("/api/overview")
async def overview():
    data = await get_analysis()
    return {key: data[key] for key in ("source", "period", "decision_rule", "summary")}


@app.get("/api/generation")
async def generation():
    data = await get_analysis()
    return {key: data[key] for key in ("source", "selected_forecasts", "actuals")}


@app.get("/api/accuracy")
async def accuracy():
    data = await get_analysis()
    return {
        "source": data["source"],
        "decision_rule": data["decision_rule"],
        "summary": data["summary"],
        "observations": data["selected_forecasts"],
    }


@app.get("/api/forecast-history")
async def forecast_history(target_date: Optional[str] = Query(default=None)):
    data = await get_analysis()
    rows = data["forecast_history"]
    if target_date:
        rows = [row for row in rows if row["start_time"].startswith(target_date)]
    return {"source": data["source"], "records": rows}


@app.get("/api/data")
async def data_explorer(target_date: Optional[str] = Query(default=None)):
    data = await get_analysis()
    rows = data["selected_forecasts"]
    if target_date:
        rows = [row for row in rows if row["start_time"].startswith(target_date)]
    return {"source": data["source"], "records": rows}


@app.post("/api/cache/clear")
async def clear_cache():
    global _cache
    _cache = None
    return {"status": "cleared"}