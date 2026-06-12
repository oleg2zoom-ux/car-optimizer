def annual_km_adjustment(annual_km: float) -> float:
    """
    Simple depreciation adjustment based on annual mileage.
    This is a placeholder heuristic for MVP.
    """
    annual_km = float(annual_km)

    if annual_km <= 10000:
        return -0.004
    if annual_km <= 15000:
        return 0.0
    if annual_km <= 20000:
        return 0.004
    if annual_km <= 25000:
        return 0.008
    return 0.012


def adjusted_depreciation_rate(base_rate: float, annual_km: float) -> float:
    rate = float(base_rate) + annual_km_adjustment(annual_km)
    return min(max(rate, 0.02), 0.35)


def future_value_estimate(
    purchase_price: float,
    hold_years: int,
    annual_depr_rate: float,
    risk_sigma: float,
    annual_km: float,
) -> dict:
    """
    Estimate future value using compound annual depreciation.
    Returns expected, pessimistic, optimistic.
    """
    rate = adjusted_depreciation_rate(annual_depr_rate, annual_km)
    expected = float(purchase_price) * ((1 - rate) ** int(hold_years))

    pessimistic = expected * (1 - float(risk_sigma))
    optimistic = expected * (1 + float(risk_sigma))

    return {
        "expected": max(expected, 0.0),
        "pessimistic": max(pessimistic, 0.0),
        "optimistic": max(optimistic, 0.0),
        "adjusted_depr_rate": rate,
    }
