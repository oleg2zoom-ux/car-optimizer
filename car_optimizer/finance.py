def monthly_payment(principal: float, annual_rate: float, months: int) -> float:
    """Calculate fixed monthly loan payment using annuity formula."""
    principal = max(float(principal), 0.0)
    months = int(months)

    if principal <= 0:
        return 0.0
    if months <= 0:
        raise ValueError("months must be positive")

    monthly_rate = annual_rate / 12 / 100

    if monthly_rate == 0:
        return principal / months

    return principal * (monthly_rate * (1 + monthly_rate) ** months) / (
        (1 + monthly_rate) ** months - 1
    )


def total_interest_paid(principal: float, annual_rate: float, months: int) -> float:
    payment = monthly_payment(principal, annual_rate, months)
    return max(payment * months - principal, 0.0)


def required_loan(purchase_price: float, current_car_sale: float, extra_cash: float) -> float:
    return max(float(purchase_price) - float(current_car_sale) - float(extra_cash), 0.0)
