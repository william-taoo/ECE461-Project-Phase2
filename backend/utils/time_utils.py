def ms_to_seconds(v: int) -> float:
    try:
        return round(float(v) / 1000.0, 3)
    except Exception:
        return 0.0