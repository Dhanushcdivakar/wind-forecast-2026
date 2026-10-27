from datetime import datetime, timedelta, timezone
import math

import httpx
import pandas as pd

from app.config import ELEXON_BASE_URL


PERIOD_START = datetime(2026, 1, 1, tzinfo=timezone.utc)
PERIOD_END = datetime(2026, 2, 1, tzinfo=timezone.utc)

CUTOFF_HOUR_UTC = 0


class ElexonError(RuntimeError):
    pass


def _time(value):
    if value is None:
        return None
    parsed = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.to_pydatetime()


def _number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _iso(value):
    return value.astimezone(timezone.utc).isoformat()


async def _stream(client, dataset, params):
    url = f"{ELEXON_BASE_URL}/{dataset}/stream"
    response = await client.get(url, params=params, timeout=60)
    response.raise_for_status()
    data = response.json()
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict):
        records = None
        for key in ("data", "results", "items", "result"):
            if isinstance(data.get(key), list):
                records = data[key]
                break
        if records is None:
            raise ElexonError(
                f"Unexpected response format from {dataset}. "
                f"Response keys: {list(data.keys())}"
            )
    else:
        raise ElexonError(
            f"Unexpected response type from {dataset}: {type(data).__name__}"
        )
    return records


async def elexon_data():
    publication_start = PERIOD_START - timedelta(days=2)

    def iso_z(value):
        return value.isoformat().replace("+00:00", "Z")

    try:
        async with httpx.AsyncClient(headers={"Accept": "application/json"}) as client:
            actuals = await _stream(
                client,
                "FUELHH",
                {
                    "settlementDateFrom": "2026-01-01",
                    "settlementDateTo": "2026-01-31",
                    "fuelType": "WIND",
                },
            )
            forecasts = await _stream(
                client,
                "WINDFOR",
                {
                    "publishDateTimeFrom": iso_z(publication_start),
                    "publishDateTimeTo": iso_z(PERIOD_END),
                },
            )
    except httpx.HTTPStatusError as exc:
        raise ElexonError(
            f"Elexon returned HTTP {exc.response.status_code} "
            f"for {exc.request.url}. "
            f"Response: {exc.response.text[:500]}"
        ) from exc
    except httpx.HTTPError as exc:
        raise ElexonError(f"Could not connect to Elexon: {exc}") from exc
    except ValueError as exc:
        raise ElexonError(f"Could not parse the Elexon response: {exc}") from exc

    valid_actuals = []
    for record in actuals:
        if str(record.get("fuelType", "")).upper() != "WIND":
            continue
        target = _time(record.get("startTime"))
        generation = _number(record.get("generation"))
        if target is None or generation is None:
            continue
        if not PERIOD_START <= target < PERIOD_END:
            continue
        valid_actuals.append(record)

    valid_forecasts = []
    for record in forecasts:
        target = _time(record.get("startTime"))
        published = _time(record.get("publishTime"))
        generation = _number(record.get("generation"))
        if target is None or published is None or generation is None:
            continue
        if not PERIOD_START <= target < PERIOD_END:
            continue
        valid_forecasts.append(record)

    if not valid_actuals:
        raise ElexonError("No valid January 2026 FUELHH wind actuals were returned.")
    if not valid_forecasts:
        raise ElexonError("No valid January 2026 WINDFOR forecasts were returned.")

    return {
        "actuals": valid_actuals,
        "forecasts": valid_forecasts,
        "source": "elexon",
    }


def analyse(raw, cutoff_hour_utc=CUTOFF_HOUR_UTC):
    if not 0 <= cutoff_hour_utc <= 23:
        raise ValueError("cutoff_hour_utc must be between 0 and 23.")

    actual_by_target = {}
    for record in raw.get("actuals", []):
        target = _time(record.get("startTime"))
        generation = _number(record.get("generation"))
        if target is None or generation is None:
            continue
        if not PERIOD_START <= target < PERIOD_END:
            continue
        published = _time(record.get("publishTime"))
        ordering_time = published or datetime.min.replace(tzinfo=timezone.utc)
        existing = actual_by_target.get(target)
        if existing is None or ordering_time > existing["ordering_time"]:
            actual_by_target[target] = {
                "target": target,
                "actual": generation,
                "ordering_time": ordering_time,
                "publish_time": published,
            }

    actual_groups = {}
    for target, record in actual_by_target.items():
        hour = target.replace(minute=0, second=0, microsecond=0)
        actual_groups.setdefault(hour, []).append({"target": target, "actual": record["actual"]})

    hourly_actuals = {}
    hourly_actual_rows = []
    incomplete_actual_hours = 0

    for hour, observations in actual_groups.items():
        expected = {hour, hour + timedelta(minutes=30)}
        observed = {item["target"] for item in observations}
        if not expected.issubset(observed):
            incomplete_actual_hours += 1
            continue
        values = [item["actual"] for item in observations if item["target"] in expected]
        if len(values) != 2:
            incomplete_actual_hours += 1
            continue
        hourly_value = sum(values) / 2
        hourly_actuals[hour] = hourly_value
        hourly_actual_rows.append({
            "start_time": _iso(hour),
            "actual": round(hourly_value, 2),
            "source_intervals": 2,
        })

    forecasts_by_key = {}
    for record in raw.get("forecasts", []):
        target = _time(record.get("startTime"))
        published = _time(record.get("publishTime"))
        generation = _number(record.get("generation"))
        if target is None or published is None or generation is None:
            continue
        if not PERIOD_START <= target < PERIOD_END:
            continue
        key = (target, published)
        forecasts_by_key[key] = {
            "start_time": _iso(target),
            "publish_time": _iso(published),
            "forecast": generation,
            "_target": target,
            "_published": published,
        }

    history = list(forecasts_by_key.values())
    history.sort(key=lambda row: (row["_target"], row["_published"]))

    history_by_target = {}
    for row in history:
        history_by_target.setdefault(row["_target"], []).append(row)

    matched = []
    targets_without_forecasts = 0
    targets_without_actuals = 0

    for target in sorted(hourly_actuals):
        candidates = history_by_target.get(target, [])
        cutoff = target.replace(hour=cutoff_hour_utc, minute=0, second=0, microsecond=0)
        eligible = [row for row in candidates if row["_published"] < cutoff]
        if not eligible:
            targets_without_forecasts += 1
            continue
        selected = max(eligible, key=lambda row: row["_published"])
        if target not in hourly_actuals:
            targets_without_actuals += 1
            continue
        forecast = selected["forecast"]
        actual = hourly_actuals[target]
        error = forecast - actual
        matched.append({
            "start_time": _iso(target),
            "publish_time": selected["publish_time"],
            "forecast": round(forecast, 2),
            "actual": round(actual, 2),
            "error": round(error, 2),
            "absolute_error": round(abs(error), 2),
        })

    matched.sort(key=lambda row: row["start_time"])

    public_history = [
        {
            "start_time": row["start_time"],
            "publish_time": row["publish_time"],
            "forecast": round(row["forecast"], 2),
        }
        for row in history
    ]

    errors = [row["error"] for row in matched]

    def avg(values):
        return round(sum(values) / len(values), 2) if values else None

    mae = avg([abs(error) for error in errors])
    rmse = (
        round(math.sqrt(sum(error ** 2 for error in errors) / len(errors)), 2)
        if errors
        else None
    )
    mbe = avg(errors)

    expected_hourly_intervals = 31 * 24
    matched_count = len(matched)
    coverage = (
        round(matched_count / expected_hourly_intervals * 100, 2)
        if expected_hourly_intervals
        else 0
    )

    metrics = {
        "mae_mw": mae,
        "rmse_mw": rmse,
        "mbe_mw": mbe,
        "matched_intervals": matched_count,
        "actual_intervals": len(actual_by_target),
        "hourly_actual_intervals": len(hourly_actuals),
        "expected_hourly_intervals": expected_hourly_intervals,
        "coverage_pct": coverage,
        "forecast_history_records": len(public_history),
        "incomplete_actual_hours": incomplete_actual_hours,
        "hours_without_eligible_forecasts": targets_without_forecasts,
        "average_actual_mw": avg([row["actual"] for row in hourly_actual_rows]),
        "average_selected_forecast_mw": avg([row["forecast"] for row in matched]),
    }

    return {
        "source": raw.get("source", "unknown"),
        "period": {
            "start": "2026-01-01",
            "end_exclusive": "2026-02-01",
        },
        "decision_rule": (
            f"For each delivery date, select the latest forecast "
            f"published before {cutoff_hour_utc:02d}:00 UTC on that "
            f"date. Actuals are aggregated into hourly averages from "
            f"two half-hourly intervals. Only complete hourly actuals "
            f"are included."
        ),
        "summary": metrics,
        "actuals": hourly_actual_rows,
        "selected_forecasts": matched,
        "forecast_history": public_history,
    }