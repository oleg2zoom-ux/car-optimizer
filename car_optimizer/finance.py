def monthly_payment(principal, annual_rate, months):
    principal=max(float(principal),0.0); months=int(months)
    if principal<=0: return 0.0
    if months<=0: raise ValueError('months must be positive')
    r=annual_rate/12/100
    if r==0: return principal/months
    return principal*(r*(1+r)**months)/((1+r)**months-1)
def loan_balance_after_months(principal, annual_rate, monthly_payment_amount, months_elapsed):
    balance=max(float(principal),0.0); payment=max(float(monthly_payment_amount),0.0); r=annual_rate/12/100
    if balance<=0: return 0.0
    if payment<=0: return balance
    for _ in range(max(int(months_elapsed),0)):
        balance=balance+balance*r-payment
        if balance<=0: return 0.0
    return max(balance,0.0)
def interest_paid_during_months(principal, annual_rate, monthly_payment_amount, months_elapsed):
    balance=max(float(principal),0.0); payment=max(float(monthly_payment_amount),0.0); r=annual_rate/12/100; total=0.0
    if balance<=0 or payment<=0: return 0.0
    for _ in range(max(int(months_elapsed),0)):
        interest=balance*r; total+=interest; balance=balance+interest-payment
        if balance<=0: break
    return max(total,0.0)
def total_interest_for_new_loan(principal, annual_rate, months):
    p=monthly_payment(principal, annual_rate, months)
    return max(p*months-max(principal,0.0),0.0)
