def priority_adjustment(calc: dict, row: dict, params: dict) -> float:
    priority = params.get("decision_priority", "min_cost")

    source_conf = float(row.get("source_confidence", 0.3) or 0.3)
    needs_review = str(row.get("needs_review", "כן")) == "כן"

    data_penalty = (1 - source_conf) * 250
    if needs_review:
        data_penalty += 180

    if priority == "min_cost":
        return data_penalty

    if priority == "newest_possible":
        age = float(row.get("vehicle_age_years", 0) or 0)
        # New/young vehicles get rewarded, older vehicles penalized.
        return data_penalty + age * 180

    if priority == "most_reliable":
        reliability = float(row.get("reliability_risk_factor", 1.0) or 1.0)
        warranty = float(row.get("warranty_years", 3) or 3)
        age = float(row.get("vehicle_age_years", 0) or 0)
        remaining_warranty = max(warranty - age, 0)
        reliability_penalty = reliability * 420 - remaining_warranty * 55
        return data_penalty + reliability_penalty

    if priority == "best_resale_value":
        depr = float(row.get("annual_depr_rate", 0.12) or 0.12)
        sigma = float(row.get("risk_sigma", 0.15) or 0.15)
        retention = float(calc.get("next_value_retention_ratio", 0.5) or 0.5)
        resale_penalty = depr * 3200 + sigma * 1200 - retention * 500
        return data_penalty + resale_penalty

    return data_penalty
