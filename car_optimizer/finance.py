def monthly_payment(principal: float, annual_rate: float, months: int) -> float:
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


def loan_balance_after_months(
    principal: float,
    annual_rate: float,
    monthly_payment_amount: float,
    months_elapsed: int,
) -> float:
    balance = max(float(principal), 0.0)
    payment = max(float(monthly_payment_amount), 0.0)
    months_elapsed = max(int(months_elapsed), 0)
    monthly_rate = annual_rate / 12 / 100

    if balance <= 0:
        return 0.0
    if payment <= 0:
        return balance

    for _ in range(months_elapsed):
        interest = balance * monthly_rate
        balance = balance + interest - payment
        if balance <= 0:
            return 0.0

    return max(balance, 0.0)


def interest_paid_during_months(
    principal: float,
    annual_rate: float,
    monthly_payment_amount: float,
    months_elapsed: int,
) -> float:
    balance = max(float(principal), 0.0)
    payment = max(float(monthly_payment_amount), 0.0)
    months_elapsed = max(int(months_elapsed), 0)
    monthly_rate = annual_rate / 12 / 100
    total_interest = 0.0

    if balance <= 0 or payment <= 0:
        return 0.0

    for _ in range(months_elapsed):
        interest = balance * monthly_rate
        total_interest += interest
        balance = balance + interest - payment
        if balance <= 0:
            break

    return max(total_interest, 0.0)


def total_interest_for_loan(principal: float, annual_rate: float, months: int) -> float:
    payment = monthly_payment(principal, annual_rate, months)
    return max(payment * months - max(principal, 0.0), 0.0)
