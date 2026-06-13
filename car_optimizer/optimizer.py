import pandas as pd

from car_optimizer.finance import (
    interest_paid_during_months,
    loan_balance_after_months,
    monthly_payment,
    total_interest_for_loan,
)
from car_optimizer.priority_model import priority_adjustment
from car_optimizer.risk_model import average_risk_penalty_over_months
from car_optimizer.valuation_model import depreciated_value, future_value_of_next_vehicle


def candidate_wait_months(params: dict) -> list[int]:
    max_wait = int(params["max_wait_months"])
    step = max(int(params["timing_step_months"]), 1)

    candidates = set(range(0, max_wait + 1, step))

    if params["has_existing_loan"]:
        loan_end = int(params["existing_remaining_months"])
        for delta in [0, 3, 6, 12]:
            if 0 <= loan_end + delta <= max_wait:
                candidates.add(loan_end + delta)

    current_age = float(params["current_estimate"]["vehicle_age_years"])
    for age_bucket in [3, 5, 7, 10, 15]:
        months_to_bucket = int(round((age_bucket - current_age) * 12))
        if 0 <= months_to_bucket <= max_wait:
            candidates.add(months_to_bucket)

    warranty = float(params["current_estimate"]["warranty_years"])
    months_to_warranty_end = int(round((warranty - current_age) * 12))
    if 0 <= months_to_warranty_end <= max_wait:
        candidates.add(months_to_warranty_end)

    candidates.add(max_wait)
    return sorted(candidates)


def evaluate_scenario(row: pd.Series, wait_months: int, params: dict) -> dict:
    current_est = params["current_estimate"]
    current_value_today = float(current_est["estimated_value_after_margin"])
    current_depr = float(current_est["annual_depr_rate"])

    current_sale_value = depreciated_value(current_value_today, current_depr, wait_months)

    existing_balance = 0.0
    existing_interest_paid = 0.0

    if params["has_existing_loan"]:
        paid_existing_months = min(wait_months, int(params["existing_remaining_months"]))

        existing_balance = loan_balance_after_months(
            params["existing_loan_balance"],
            params["existing_interest_rate"],
            params["existing_monthly_payment"],
            paid_existing_months,
        )

        existing_interest_paid = interest_paid_during_months(
            params["existing_loan_balance"],
            params["existing_interest_rate"],
            params["existing_monthly_payment"],
            paid_existing_months,
        )

    months_after_loan_finished = 0
    if params["has_existing_loan"]:
        months_after_loan_finished = max(wait_months - int(params["existing_remaining_months"]), 0)

    savings_until_purchase = float(params["monthly_saving_capacity"]) * wait_months

    if params["redirect_finished_loan_to_savings"] and params["has_existing_loan"]:
        savings_until_purchase += float(params["existing_monthly_payment"]) * months_after_loan_finished

    net_equity = current_sale_value - existing_balance
    equity_for_purchase = max(net_equity, 0.0)
    negative_equity = max(-net_equity, 0.0)

    cash_for_purchase = (
        float(params["extra_cash_today"]) + savings_until_purchase + equity_for_purchase
    )

    purchase_price = float(row["purchase_price"])
    next_loan_principal = max(purchase_price + negative_equity - cash_for_purchase, 0.0)

    next_monthly = monthly_payment(
        next_loan_principal,
        params["next_interest_rate"],
        params["next_loan_months"],
    )

    next_interest_total = total_interest_for_loan(
        next_loan_principal,
        params["next_interest_rate"],
        params["next_loan_months"],
    )

    current_risk_monthly = average_risk_penalty_over_months(
        start_age_years=float(current_est["vehicle_age_years"]),
        months=wait_months,
        warranty_years=current_est["warranty_years"],
        parts_support_years=current_est["parts_support_years"],
        reliability_risk_factor=current_est["reliability_risk_factor"],
        risk_tolerance=params["risk_tolerance"],
    )

    next_age_at_purchase = float(row["vehicle_age_years"])
    if row["ownership_type"] != "New":
        next_age_at_purchase += wait_months / 12

    next_hold_months = int(params["next_hold_years"]) * 12

    next_risk_monthly = average_risk_penalty_over_months(
        start_age_years=next_age_at_purchase,
        months=next_hold_months,
        warranty_years=float(row["warranty_years"]),
        parts_support_years=float(row["parts_support_years"]),
        reliability_risk_factor=float(row["reliability_risk_factor"]),
        risk_tolerance=params["risk_tolerance"],
    )

    next_fv = future_value_of_next_vehicle(
        purchase_price=purchase_price,
        hold_years=params["next_hold_years"],
        annual_depr_rate=row["annual_depr_rate"],
        risk_sigma=row["risk_sigma"],
        annual_km=params["annual_km"],
    )

    current_depr_cost = current_value_today - current_sale_value
    next_depr_cost = purchase_price - next_fv["expected"]

    current_risk_total = current_risk_monthly * wait_months
    next_risk_total = next_risk_monthly * next_hold_months

    total_months = max(wait_months + next_hold_months, 1)

    economic_cost = (
        current_depr_cost
        + existing_interest_paid
        + current_risk_total
        + next_depr_cost
        + next_interest_total
        + next_risk_total
    )

    economic_monthly = economic_cost / total_months

    payment_penalty = max(next_monthly - float(params["max_monthly_payment"]), 0.0) * 6

    calc = {
        "next_value_retention_ratio": next_fv["value_retention_ratio"],
    }

    priority_penalty = priority_adjustment(calc, row.to_dict(), params)
    score = economic_monthly + payment_penalty + priority_penalty

    if wait_months == 0:
        timing_label = "עכשיו"
        action = "להחליף עכשיו"
    elif params["has_existing_loan"] and wait_months >= int(params["existing_remaining_months"]):
        timing_label = f"בעוד {wait_months} חודשים"
        action = "להמתין, לסיים הלוואה ולחסוך"
    else:
        timing_label = f"בעוד {wait_months} חודשים"
        action = "להמתין לפני החלפה"

    reason = build_reason(
        action,
        wait_months,
        params,
        current_sale_value,
        existing_balance,
        cash_for_purchase,
        next_monthly,
        economic_monthly,
    )

    return {
        "action": action,
        "timing_label": timing_label,
        "wait_months": wait_months,
        "current_sale_value": current_sale_value,
        "existing_balance": existing_balance,
        "net_equity": net_equity,
        "savings_until_purchase": savings_until_purchase,
        "cash_for_purchase": cash_for_purchase,
        "negative_equity": negative_equity,
        "next_loan_principal": next_loan_principal,
        "next_monthly": next_monthly,
        "next_interest_total": next_interest_total,
        "current_depr_cost": current_depr_cost,
        "next_depr_cost": next_depr_cost,
        "current_risk_monthly": current_risk_monthly,
        "next_risk_monthly": next_risk_monthly,
        "current_risk_total": current_risk_total,
        "next_risk_total": next_risk_total,
        "next_future_value": next_fv["expected"],
        "next_value_retention_ratio": next_fv["value_retention_ratio"],
        "economic_monthly": economic_monthly,
        "passes_payment_limit": next_monthly <= float(params["max_monthly_payment"]),
        "priority_penalty": priority_penalty,
        "score": score,
        "reason": reason,
    }


def build_reason(
    action: str,
    wait_months: int,
    params: dict,
    current_sale_value: float,
    existing_balance: float,
    cash_for_purchase: float,
    next_monthly: float,
    economic_monthly: float,
) -> str:
    if wait_months == 0:
        return (
            f"המודל מצא שכדאי לשקול החלפה מיידית: שווי הרכב הקיים מספיק כמקדמה, "
            f"וההחזר הצפוי הוא כ-{next_monthly:,.0f} ₪."
        )

    if params["has_existing_loan"] and wait_months >= int(params["existing_remaining_months"]):
        return (
            f"המודל מעדיף להמתין עד אחרי סיום ההלוואה הקיימת או מעט אחריה. "
            f"במועד זה שווי הרכב המשוער הוא כ-{current_sale_value:,.0f} ₪, "
            f"יתרת ההלוואה כ-{existing_balance:,.0f} ₪, "
            f"והון צפוי לקנייה כ-{cash_for_purchase:,.0f} ₪."
        )

    return (
        f"המודל ממליץ להמתין {wait_months} חודשים כדי לשפר את ההון העצמי/התזמון. "
        f"העלות החודשית הכלכלית בתרחיש זה היא כ-{economic_monthly:,.0f} ₪."
    )


def run_owner_first_optimization(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    rows = []

    for wait_months in candidate_wait_months(params):
        for _, row in df.iterrows():
            calc = evaluate_scenario(row, wait_months, params)

            source_conf = row.get("source_confidence", 0)
            needs_review = row.get("needs_review", "")

            rows.append(
                {
                    "המלצת פעולה": calc["action"],
                    "מועד החלפה": calc["timing_label"],
                    "חודשי המתנה": calc["wait_months"],
                    "יצרן": row["manufacturer"],
                    "דגם": row["model"],
                    "רמת גימור": row["trim"],
                    "שנתון": int(row["model_year"]),
                    "גיל רכב הבא בעת רכישה": round(float(row["vehicle_age_years"]) + (0 if row["ownership_type"] == "New" else calc["wait_months"] / 12), 1),
                    "קטגוריה": row["category"],
                    "הנעה": row["powertrain"],
                    "מקור/בעלות": row["ownership_type"],
                    "מחיר רכב הבא": round(float(row["purchase_price"])),
                    "שווי רכב קיים במועד מכירה": round(calc["current_sale_value"]),
                    "יתרת הלוואה קיימת במועד מכירה": round(calc["existing_balance"]),
                    "הון נטו מהרכב הקיים": round(calc["net_equity"]),
                    "חיסכון עד מועד קנייה": round(calc["savings_until_purchase"]),
                    "הון עצמי צפוי במועד קנייה": round(calc["cash_for_purchase"]),
                    "מימון נדרש לרכב הבא": round(calc["next_loan_principal"]),
                    "החזר חודשי לרכב הבא": round(calc["next_monthly"]),
                    "ריבית כוללת לרכב הבא": round(calc["next_interest_total"]),
                    "שחיקת רכב קיים עד מכירה": round(calc["current_depr_cost"]),
                    "שחיקת רכב הבא בתקופת אחזקה": round(calc["next_depr_cost"]),
                    "קנס סיכון חודשי רכב קיים": round(calc["current_risk_monthly"]),
                    "קנס סיכון חודשי רכב הבא": round(calc["next_risk_monthly"]),
                    "שווי עתידי צפוי רכב הבא": round(calc["next_future_value"]),
                    "יחס שמירת ערך": round(calc["next_value_retention_ratio"], 3),
                    "עלות חודשית כלכלית": round(calc["economic_monthly"]),
                    "קנס/בונוס עדיפות": round(calc["priority_penalty"]),
                    "ציון עדיפות": round(calc["score"]),
                    "עומד בתקרת החזר": "כן" if calc["passes_payment_limit"] else "לא",
                    "אמינות מקור": source_conf,
                    "דורש אימות": needs_review,
                    "נימוק המלצה": calc["reason"],
                }
            )

    result = pd.DataFrame(rows)
    if not result.empty:
        result = result.sort_values(["ציון עדיפות", "עלות חודשית כלכלית"], ascending=True)

    return result
