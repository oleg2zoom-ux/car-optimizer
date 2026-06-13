from datetime import date


def month_diff(from_year: int, from_month: int, to_date: date) -> int:
    return max((to_date.year - int(from_year)) * 12 + (to_date.month - int(from_month)), 0)


def vehicle_age_years_from_model_year(model_year: int, today: date) -> float:
    return max(today.year - int(model_year), 0)


def depreciated_value(current_value: float, annual_depr_rate: float, months: int) -> float:
    years = max(int(months), 0) / 12
    rate = min(max(float(annual_depr_rate), 0.0), 0.50)
    return max(float(current_value) * ((1 - rate) ** years), 0.0)


def annual_km_adjustment(annual_km: float) -> float:
    annual_km = float(annual_km)

    if annual_km <= 10000:
        return -0.004
    if annual_km <= 15000:
        return 0.000
    if annual_km <= 20000:
        return 0.004
    if annual_km <= 25000:
        return 0.008
    return 0.012


def adjusted_depreciation_rate(base_rate: float, annual_km: float) -> float:
    return min(max(float(base_rate) + annual_km_adjustment(annual_km), 0.02), 0.35)


def estimate_current_vehicle_value(current_info: dict, today: date) -> dict:
    ref = current_info["reference"]

    model_year = int(current_info["model_year"])
    vehicle_age = vehicle_age_years_from_model_year(model_year, today)

    known_current_value = float(current_info.get("known_current_value", 0))
    known_purchase_price = float(current_info.get("known_purchase_price", 0))
    safety_margin = float(current_info.get("current_value_safety_margin", 0))

    base_depr = float(ref.get("annual_depr_rate", 0.10))
    msrp_ref = float(ref.get("msrp_reference", ref.get("new_price_reference_ils", ref.get("purchase_price", 0))))

    if known_current_value > 0:
        estimated = known_current_value
        method = "שווי נוכחי ידוע שהוזן על ידי המשתמש"
    elif known_purchase_price > 0:
        months_owned = month_diff(
            current_info["purchase_year"],
            current_info["purchase_month"],
            today,
        )
        estimated = depreciated_value(known_purchase_price, base_depr, months_owned)
        method = "פחת ממחיר רכישה ידוע"
    else:
        estimated = depreciated_value(msrp_ref, base_depr, int(vehicle_age * 12))
        method = "פחת ממחיר חדש/רפרנס"

    km = float(current_info.get("km", 0))
    expected_km = max(vehicle_age * 17000, 1)
    km_ratio = km / expected_km

    if km_ratio > 1.25:
        estimated *= 0.92
    elif km_ratio > 1.10:
        estimated *= 0.96
    elif km_ratio < 0.75:
        estimated *= 1.04

    hand = int(current_info.get("hand", 1))
    if hand >= 3:
        estimated *= 0.95
    elif hand == 2:
        estimated *= 0.98

    ownership = current_info.get("ownership_type", "Private Used")
    if ownership == "Leasing Used":
        estimated *= 0.92
    elif ownership == "Rental":
        estimated *= 0.86
    elif ownership == "Company":
        estimated *= 0.90

    estimated_after_margin = estimated * (1 - safety_margin)

    return {
        "estimated_value": max(estimated, 0.0),
        "estimated_value_after_margin": max(estimated_after_margin, 0.0),
        "vehicle_age_years": vehicle_age,
        "method": method,
        "annual_depr_rate": base_depr,
        "warranty_years": float(ref.get("warranty_years", 3)),
        "parts_support_years": float(ref.get("parts_support_years", 7)),
        "reliability_risk_factor": float(ref.get("reliability_risk_factor", 1.0)),
    }


def future_value_of_next_vehicle(
    purchase_price: float,
    hold_years: int,
    annual_depr_rate: float,
    risk_sigma: float,
    annual_km: float,
) -> dict:
    rate = adjusted_depreciation_rate(annual_depr_rate, annual_km)
    expected = float(purchase_price) * ((1 - rate) ** int(hold_years))
    pessimistic = expected * (1 - float(risk_sigma))
    optimistic = expected * (1 + float(risk_sigma))

    return {
        "expected": max(expected, 0.0),
        "pessimistic": max(pessimistic, 0.0),
        "optimistic": max(optimistic, 0.0),
        "adjusted_rate": rate,
        "value_retention_ratio": max(expected, 0.0) / max(float(purchase_price), 1.0),
    }
