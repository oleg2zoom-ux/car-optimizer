import pandas as pd

from car_optimizer.finance import monthly_payment, required_loan, total_interest_paid
from car_optimizer.valuation_model import future_value_estimate


def monthly_ownership_cost(row: pd.Series, params: dict) -> dict:
    purchase_price = float(row["purchase_price"])
    hold_years = int(params["hold_years"])
    hold_months = hold_years * 12

    fv = future_value_estimate(
        purchase_price=purchase_price,
        hold_years=hold_years,
        annual_depr_rate=float(row["annual_depr_rate"]),
        risk_sigma=float(row["risk_sigma"]),
        annual_km=float(params["annual_km"]),
    )

    loan_amount = required_loan(
        purchase_price=purchase_price,
        current_car_sale=params["current_car_sale"],
        extra_cash=params["extra_cash"],
    )

    payment = monthly_payment(
        principal=loan_amount,
        annual_rate=params["annual_interest_rate"],
        months=params["loan_months"],
    )

    interest_total = total_interest_paid(
        principal=loan_amount,
        annual_rate=params["annual_interest_rate"],
        months=params["loan_months"],
    )

    depreciation_loss = purchase_price - fv["expected"]

    running_monthly = (
        params["insurance_monthly"]
        + params["maintenance_monthly"]
        + params["license_monthly"]
        + params["energy_monthly"]
    )

    total_cost = depreciation_loss + interest_total + running_monthly * hold_months
    ownership_monthly = total_cost / hold_months

    exceeds_payment = payment > params["max_monthly_payment"]
    penalty = max(payment - params["max_monthly_payment"], 0) * 3

    return {
        "future_value_expected": fv["expected"],
        "future_value_pessimistic": fv["pessimistic"],
        "future_value_optimistic": fv["optimistic"],
        "adjusted_depr_rate": fv["adjusted_depr_rate"],
        "loan_amount": loan_amount,
        "monthly_payment": payment,
        "interest_total": interest_total,
        "depreciation_loss": depreciation_loss,
        "running_monthly": running_monthly,
        "ownership_monthly": ownership_monthly,
        "score": ownership_monthly + penalty,
        "passes_payment_limit": not exceeds_payment,
    }


def run_optimization(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    rows = []

    for _, row in df.iterrows():
        calc = monthly_ownership_cost(row, params)

        rows.append(
            {
                "יצרן": row["manufacturer"],
                "דגם": row["model"],
                "רמת גימור": row.get("trim", ""),
                "שנתון": int(row["model_year"]),
                "קטגוריה": row["category"],
                "הנעה": row["powertrain"],
                "סוג בעלות": row["ownership_type"],
                "ק״מ": int(row["km"]) if pd.notna(row["km"]) else None,
                "מחיר רכישה": round(float(row["purchase_price"])),
                "הלוואה נדרשת": round(calc["loan_amount"]),
                "החזר חודשי": round(calc["monthly_payment"]),
                "ריבית כוללת": round(calc["interest_total"]),
                "שווי עתידי צפוי": round(calc["future_value_expected"]),
                "שווי פסימי": round(calc["future_value_pessimistic"]),
                "שווי אופטימי": round(calc["future_value_optimistic"]),
                "שיעור שחיקה מותאם": round(calc["adjusted_depr_rate"] * 100, 2),
                "עלות בעלות חודשית": round(calc["ownership_monthly"]),
                "עובר מגבלת החזר": "כן" if calc["passes_payment_limit"] else "לא",
                "מקור נתון": row["source_type"],
                "אמינות מקור": row["source_confidence"],
                "ציון": round(calc["score"]),
            }
        )

    result = pd.DataFrame(rows)

    if not result.empty:
        result = result.sort_values(["ציון", "עלות בעלות חודשית"], ascending=True)

    return result
