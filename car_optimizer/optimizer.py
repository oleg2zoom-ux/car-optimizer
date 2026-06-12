import pandas as pd
from car_optimizer.finance import interest_paid_during_months, loan_balance_after_months, monthly_payment, total_interest_for_new_loan
from car_optimizer.valuation_model import depreciated_value, future_value_of_next_vehicle

def max_wait_months_by_age(params):
    by_age=max(int(round((float(params['max_current_vehicle_age_years'])-float(params['current_vehicle_age_years']))*12)),0)
    return max(min(by_age,int(params['manual_max_wait_months'])),0)
def candidate_wait_months(params):
    max_wait=max_wait_months_by_age(params); step=max(int(params['timing_step_months']),1)
    months=list(range(0,max_wait+1,step))
    if max_wait not in months: months.append(max_wait)
    return sorted(set(months))
def evaluate_option(row, wait_months, params):
    current_now=float(params['current_vehicle_value'])
    sale_value=depreciated_value(current_now, params['current_annual_depr_rate'], wait_months)
    bal=0.0; existing_interest=0.0; paid_current=0.0
    if params['has_existing_loan']:
        paid_months=min(wait_months, int(params['existing_remaining_months']))
        bal=loan_balance_after_months(params['existing_loan_balance'], params['existing_interest_rate'], params['existing_monthly_payment'], paid_months)
        existing_interest=interest_paid_during_months(params['existing_loan_balance'], params['existing_interest_rate'], params['existing_monthly_payment'], paid_months)
        paid_current=paid_months*float(params['existing_monthly_payment'])
    net_equity=sale_value-bal
    price=float(row['purchase_price'])
    cash=float(params['extra_cash_at_purchase'])+net_equity
    if cash>=0:
        next_principal=max(price-cash,0.0); upfront_gap=0.0
    else:
        if params['allow_negative_equity_roll']:
            next_principal=price+abs(cash); upfront_gap=0.0
        else:
            next_principal=price; upfront_gap=abs(cash)
    next_pay=monthly_payment(next_principal, params['next_interest_rate'], params['next_loan_months'])
    next_interest=total_interest_for_new_loan(next_principal, params['next_interest_rate'], params['next_loan_months'])
    fv=future_value_of_next_vehicle(price, params['next_hold_years'], row['annual_depr_rate'], row['risk_sigma'], params['annual_km'])
    current_dep=current_now-sale_value; next_dep=price-fv['expected']
    horizon=max(wait_months+int(params['next_hold_years'])*12,1)
    econ=current_dep+existing_interest+next_dep+next_interest+upfront_gap
    econ_m=econ/horizon
    existing_monthly_if_waiting=float(params['existing_monthly_payment']) if params['has_existing_loan'] and wait_months>0 and params['existing_remaining_months']>0 else 0.0
    peak=max(existing_monthly_if_waiting,next_pay)
    passes=next_pay<=float(params['max_monthly_payment'])
    penalty=0.0
    if not passes: penalty+=(next_pay-float(params['max_monthly_payment']))*5
    if upfront_gap>0: penalty+=upfront_gap/12
    return {'wait_months':wait_months,'timing_label':'למכור עכשיו' if wait_months==0 else f'למכור בעוד {wait_months} חודשים','current_sale_value':sale_value,'existing_balance_at_sale':bal,'net_equity_from_current_car':net_equity,'existing_interest_paid':existing_interest,'current_loan_payments_during_wait':paid_current,'next_loan_principal':next_principal,'next_monthly_payment':next_pay,'next_interest_total':next_interest,'next_future_value':fv['expected'],'next_future_value_pessimistic':fv['pessimistic'],'next_future_value_optimistic':fv['optimistic'],'current_depreciation_cost':current_dep,'next_depreciation_cost':next_dep,'economic_monthly_cost':econ_m,'peak_monthly_payment':peak,'passes_payment_limit':passes,'upfront_gap_not_financed':upfront_gap,'score':econ_m+penalty}
def run_timing_optimization(df, params):
    rows=[]
    for wait in candidate_wait_months(params):
        for _, row in df.iterrows():
            calc=evaluate_option(row, wait, params)
            rows.append({'המלצת תזמון':calc['timing_label'],'חודשי המתנה עד מכירה':calc['wait_months'],'יצרן':row['manufacturer'],'דגם':row['model'],'רמת גימור':row.get('trim',''),'שנתון':int(row['model_year']),'גיל רכב הבא בעת רכישה':int(row['vehicle_age_years']),'קטגוריה':row['category'],'הנעה':row['powertrain'],'מקור/בעלות':row['ownership_type'],'מחיר רכב הבא':round(float(row['purchase_price'])),'שווי רכב קיים בעת מכירה':round(calc['current_sale_value']),'יתרת הלוואה קיימת בעת מכירה':round(calc['existing_balance_at_sale']),'הון נטו מהרכב הקיים':round(calc['net_equity_from_current_car']),'מימון נדרש לרכב הבא':round(calc['next_loan_principal']),'החזר חודשי הבא':round(calc['next_monthly_payment']),'שיא החזר חודשי':round(calc['peak_monthly_payment']),'ריבית כוללת רכב הבא':round(calc['next_interest_total']),'ריבית קיימת בתקופת המתנה':round(calc['existing_interest_paid']),'שווי עתידי צפוי לרכב הבא':round(calc['next_future_value']),'שווי פסימי לרכב הבא':round(calc['next_future_value_pessimistic']),'שווי אופטימי לרכב הבא':round(calc['next_future_value_optimistic']),'שחיקת רכב קיים בתקופת המתנה':round(calc['current_depreciation_cost']),'שחיקת רכב הבא בתקופת אחזקה':round(calc['next_depreciation_cost']),'עלות חודשית כלכלית':round(calc['economic_monthly_cost']),'עומד באילוץ החזר':'כן' if calc['passes_payment_limit'] else 'לא','פער הון לא ממומן':round(calc['upfront_gap_not_financed']),'מקור נתון':row['source_type'],'אמינות מקור':row['source_confidence'],'ציון':round(calc['score'])})
    res=pd.DataFrame(rows)
    if not res.empty: res=res.sort_values(['ציון','עלות חודשית כלכלית'], ascending=True)
    return res
