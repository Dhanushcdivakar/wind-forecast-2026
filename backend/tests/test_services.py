from app.services import analyse


def test_metrics_and_bias_direction():
    raw = {
        "actuals": [
            {"startTime": "2026-01-02T12:00:00Z", "generation": 100, "fuelType": "WIND"},
            {"startTime": "2026-01-02T12:30:00Z", "generation": 100, "fuelType": "WIND"},
        ],
        "forecasts": [
            {"startTime": "2026-01-02T12:00:00Z", "publishTime": "2026-01-01T18:00:00Z", "generation": 110},
            {"startTime": "2026-01-02T12:00:00Z", "publishTime": "2026-01-02T01:00:00Z", "generation": 130}
        ]
    }
    result = analyse(raw, cutoff_hour_utc=0)
    assert result["summary"]["mae_mw"] == 10
    assert result["summary"]["mbe_mw"] == 10
    assert result["selected_forecasts"][0]["forecast"] == 110


def test_empty_data():
    result = analyse({"actuals": [], "forecasts": [], "source": "test"})
    assert result["summary"]["matched_intervals"] == 0
    assert result["summary"]["mae_mw"] is None
