RISK_TOLERANCE_MULTIPLIER = {
    "נמוכה": 0.65,
    "בינונית": 1.00,
    "גבוהה": 1.45,
}


def monthly_age_risk_penalty(
    age_years: float,
    warranty_years: float,
    parts_support_years: float,
    reliability_risk_factor: float,
    risk_tolerance: str,
) -> float:
    """
    Returns a monthly risk penalty in NIS-equivalent decision units.
    This is not a guaranteed maintenance cost. It is a decision penalty.
    """
    age = float(age_years)
    warranty = float(warranty_years)
    parts = float(parts_support_years)
    reliability = float(reliability_risk_factor)
    tolerance = RISK_TOLERANCE_MULTIPLIER.get(risk_tolerance, 1.0)

    if age <= warranty:
        base = 0
    elif age <= parts:
        base = 120
    elif age <= 10:
        base = 320
    elif age <= 15:
        base = 650
    else:
        base = 1200

    return base * reliability * tolerance


def average_risk_penalty_over_months(
    start_age_years: float,
    months: int,
    warranty_years: float,
    parts_support_years: float,
    reliability_risk_factor: float,
    risk_tolerance: str,
) -> float:
    months = max(int(months), 0)
    if months == 0:
        return 0.0

    total = 0.0
    for m in range(months):
        age = float(start_age_years) + m / 12
        total += monthly_age_risk_penalty(
            age,
            warranty_years,
            parts_support_years,
            reliability_risk_factor,
            risk_tolerance,
        )

    return total / months
