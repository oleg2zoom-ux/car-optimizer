def depreciated_value(current_value, annual_depr_rate, months):
    years=max(int(months),0)/12; rate=min(max(float(annual_depr_rate),0.0),0.50)
    return max(float(current_value)*((1-rate)**years),0.0)
def annual_km_adjustment(annual_km):
    km=float(annual_km)
    if km<=10000: return -0.004
    if km<=15000: return 0.0
    if km<=20000: return 0.004
    if km<=25000: return 0.008
    return 0.012
def adjusted_depreciation_rate(base_rate, annual_km):
    return min(max(float(base_rate)+annual_km_adjustment(annual_km),0.02),0.35)
def future_value_of_next_vehicle(purchase_price, hold_years, annual_depr_rate, risk_sigma, annual_km):
    rate=adjusted_depreciation_rate(annual_depr_rate, annual_km)
    expected=float(purchase_price)*((1-rate)**int(hold_years))
    return {'expected':max(expected,0.0),'pessimistic':max(expected*(1-float(risk_sigma)),0.0),'optimistic':max(expected*(1+float(risk_sigma)),0.0),'adjusted_rate':rate}
