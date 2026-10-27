from typing import Optional

from fastapi import APIRouter, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import CORS_ORIGINS
from app.services import ElexonError, analyse, elexon_data


# --------------------------------------------------
# FastAPI Application
# --------------------------------------------------

app = FastAPI(
    title="Wind Forecast Analytics API",
    description="January 2026 UK national wind generation forecast analytics.",
    version="0.1.0",
)


# --------------------------------------------------
# CORS Configuration
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Vercel Path Middleware
# --------------------------------------------------



# --------------------------------------------------
# Custom 404 Handler
# --------------------------------------------------

@app.exception_handler(404)
async def custom_404(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "detail": "Not Found",
            "scope_path": request.scope.get("path"),
            "x_matched_path": request.headers.get("x-matched-path"),
            "available_routes": [
                getattr(route, "path", str(route))
                for route in app.routes
            ],
        },
    )


# --------------------------------------------------
# Analysis Cache
# --------------------------------------------------

_cache = None


async def get_analysis():
    global _cache

    if _cache is None:
        try:
            raw = await elexon_data()

            if not raw.get("actuals") or not raw.get("forecasts"):
                raise ElexonError(
                    "Elexon returned no actual or forecast records "
                    "for the requested period."
                )

            _cache = analyse(raw)

        except ElexonError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to retrieve real Elexon data: {exc}",
            ) from exc

    return _cache


# --------------------------------------------------
# Root Endpoints
# --------------------------------------------------

@app.get("/")
@app.get("/api")
async def root():
    return {
        "status": "online",
        "service": "Wind Forecast Analytics API",
        "docs": "/docs",
        "health": "/api/health",
        "overview": "/api/overview",
    }


# --------------------------------------------------
# API Router
# All endpoints are registered under /api
# --------------------------------------------------

router = APIRouter()


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "data_mode": "elexon",
    }


@router.get("/overview")
async def overview():
    data = await get_analysis()

    return {
        key: data[key]
        for key in (
            "source",
            "period",
            "decision_rule",
            "summary",
        )
    }


@router.get("/generation")
async def generation():
    data = await get_analysis()

    return {
        key: data[key]
        for key in (
            "source",
            "selected_forecasts",
            "actuals",
        )
    }


@router.get("/accuracy")
async def accuracy():
    data = await get_analysis()

    return {
        "source": data["source"],
        "decision_rule": data["decision_rule"],
        "summary": data["summary"],
        "observations": data["selected_forecasts"],
    }


@router.get("/forecast-history")
async def forecast_history(
    target_date: Optional[str] = Query(default=None),
):
    data = await get_analysis()
    rows = data["forecast_history"]

    if target_date:
        rows = [
            row
            for row in rows
            if row["start_time"].startswith(target_date)
        ]

    return {
        "source": data["source"],
        "records": rows,
    }


@router.get("/data")
async def data_explorer(
    target_date: Optional[str] = Query(default=None),
):
    data = await get_analysis()
    rows = data["selected_forecasts"]

    if target_date:
        rows = [
            row
            for row in rows
            if row["start_time"].startswith(target_date)
        ]

    return {
        "source": data["source"],
        "records": rows,
    }


@router.post("/cache/clear")
async def clear_cache():
    global _cache

    _cache = None

    return {
        "status": "cleared",
    }


# --------------------------------------------------
# Register Router Exactly Once
# --------------------------------------------------

app.include_router(router, prefix="/api")