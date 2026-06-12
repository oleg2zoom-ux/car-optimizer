# סכמה למסד נתוני רכבים

הקובץ יכול להיות CSV או Excel. כל שורה היא אפשרות רכישה או תצפית שוק.

עמודות חובה: record_id, manufacturer, model, trim, model_year, vehicle_age_years, category, powertrain, ownership_type, km, hand, purchase_price, annual_depr_rate, risk_sigma, source_type, source_confidence.

annual_depr_rate הוא שיעור שחיקה שנתי בין 0 ל-1. risk_sigma הוא טווח סיכון סביב התחזית בין 0 ל-1.

אין לערבב מחיר מבוקש, מחיר טרייד-אין, מחיר מחירון ומחיר עסקה בלי לציין מקור.
