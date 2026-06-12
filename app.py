import streamlit as st
from car_optimizer.constants import DEFAULTS
from car_optimizer.data_loader import load_market_data, validate_columns, REQUIRED_COLUMNS
from car_optimizer.optimizer import run_timing_optimization

st.set_page_config(page_title="מחשבון תזמון והחלפת רכב", page_icon="🚗", layout="wide")
st.markdown("""
<style>
html, body, [class*="css"] { direction: rtl; text-align: right; }
section[data-testid="stSidebar"] { direction: rtl; text-align: right; }
.stDataFrame, .dataframe { direction: rtl; }
div[data-testid="stMetric"] { direction: rtl; text-align: right; }
</style>
""", unsafe_allow_html=True)

st.title("🚗 מחשבון תזמון והחלפת רכב")
st.caption("גרסה 0.3: בודק האם כדאי להישאר עם הרכב הקיים, מתי למכור אותו, ואיזו קנייה עתידית עומדת באילוצי הון עצמי והחזר חודשי.")
with st.expander("מה השתנה בגרסה הזו?", expanded=False):
    st.write("המודל מתמקד בהחלטת התזמון: להישאר עם הרכב הנוכחי ולשלם הלוואה קיימת, או למכור עכשיו/בעתיד ולהשתמש בכסף כמקדמה לרכב הבא.")
    st.write("עלויות כמו דלק, ביטוח וטיפולים אינן נכנסות לציון המרכזי. הן מופיעות רק בלשונית נפרדת כאופציה עתידית.")
    st.write("סליידרים בעייתיים הוחלפו בשדות מספריים ובבחירות קבועות, כדי שהערכים יהיו גלויים.")

tab_current, tab_next, tab_results, tab_optional, tab_data, tab_help = st.tabs([
    "1. הרכב הקיים", "2. הרכב הבא והאילוצים", "3. תוצאות אופטימיזציה", "4. עלויות נלוות — אופציונלי", "5. נתונים", "עזרה"
])

with tab_current:
    st.subheader("הרכב הקיים והלוואה קיימת")
    c1,c2,c3=st.columns(3)
    with c1:
        current_vehicle_value=st.number_input("שווי מכירה ריאלי של הרכב הקיים היום", min_value=0, value=DEFAULTS['current_vehicle_value'], step=1000)
    with c2:
        current_vehicle_age_years=st.number_input("גיל הרכב הקיים בשנים", min_value=0.0, max_value=30.0, value=float(DEFAULTS['current_vehicle_age_years']), step=0.5)
    with c3:
        max_current_vehicle_age_years=st.number_input("גיל מקסימלי שאתה מוכן להישאר עם הרכב הקיים", min_value=1.0, max_value=30.0, value=float(DEFAULTS['max_current_vehicle_age_years']), step=0.5)
    c4,c5,c6=st.columns(3)
    with c4:
        current_annual_depr_rate_percent=st.number_input("שחיקת מחיר שנתית משוערת של הרכב הקיים (%)", min_value=0.0, max_value=40.0, value=float(DEFAULTS['current_annual_depr_rate_percent']), step=0.5)
    with c5:
        timing_step_months=st.selectbox("רזולוציית בדיקת תזמון מכירה", options=[1,3,6,12], index=2)
    with c6:
        manual_max_wait_months=st.number_input("מקסימום המתנה ידני בחודשים", min_value=0, max_value=180, value=DEFAULTS['manual_max_wait_months'], step=3)
    st.markdown('---')
    has_existing_loan=st.checkbox("יש הלוואה קיימת על הרכב הנוכחי", value=DEFAULTS['has_existing_loan'])
    if has_existing_loan:
        l1,l2,l3,l4=st.columns(4)
        with l1: existing_loan_balance=st.number_input("יתרת הלוואה קיימת", min_value=0, value=DEFAULTS['existing_loan_balance'], step=1000)
        with l2: existing_monthly_payment=st.number_input("החזר חודשי קיים", min_value=0, value=DEFAULTS['existing_monthly_payment'], step=100)
        with l3: existing_remaining_months=st.number_input("חודשים שנותרו בהלוואה הקיימת", min_value=0, max_value=180, value=DEFAULTS['existing_remaining_months'], step=1)
        with l4: existing_interest_rate=st.number_input("ריבית שנתית משוערת בהלוואה הקיימת (%)", min_value=0.0, max_value=25.0, value=float(DEFAULTS['existing_interest_rate']), step=0.25)
    else:
        existing_loan_balance=0; existing_monthly_payment=0; existing_remaining_months=0; existing_interest_rate=0.0
    st.info("המחשבון יבדוק נקודות זמן שונות למכירת הרכב הקיים: עכשיו, בעוד כמה חודשים, ועד גיל/חודש מקסימלי שהגדרת.")

with tab_next:
    st.subheader("הרכב הבא, מימון ואילוצים")
    uploaded_file=st.file_uploader("אפשר להעלות CSV/Excel של נתוני שוק. בלי העלאה — נטען מדגם הדגמה.", type=['csv','xlsx','xls'])
    market_data=load_market_data(uploaded_file)
    errors=validate_columns(market_data)
    if errors:
        st.error("קובץ הנתונים לא מתאים לסכמה.")
        for e in errors: st.write('• '+e)
        st.stop()
    st.success(f"נטענו {len(market_data):,} אפשרויות רכב מהמאגר.")
    m1,m2,m3,m4=st.columns(4)
    with m1: extra_cash_at_purchase=st.number_input("הון עצמי נוסף לרכב הבא", min_value=0, value=DEFAULTS['extra_cash_at_purchase'], step=1000)
    with m2: max_monthly_payment=st.number_input("תקרת החזר חודשית לרכב הבא", min_value=0, value=DEFAULTS['max_monthly_payment'], step=100)
    with m3: next_interest_rate=st.number_input("ריבית שנתית למימון הרכב הבא (%)", min_value=0.0, max_value=25.0, value=float(DEFAULTS['next_interest_rate']), step=0.25)
    with m4: next_loan_months=st.selectbox("תקופת מימון לרכב הבא", options=[12,24,36,48,60,72,84,96,108,120], index=4)
    h1,h2,h3=st.columns(3)
    with h1: next_hold_years=st.selectbox("כמה שנים להחזיק את הרכב הבא?", options=[1,2,3,4,5,6,7,8,10], index=4)
    with h2: max_purchase_price=st.number_input("מחיר רכישה מקסימלי לרכב הבא", min_value=0, value=DEFAULTS['max_purchase_price'], step=5000)
    with h3: annual_km=st.number_input("ק״מ שנתי צפוי", min_value=0, value=DEFAULTS['annual_km'], step=1000, help="משפיע רק על שחיקת מחיר. לא מחושב דלק.")
    st.markdown('---')
    st.subheader("העדפות לרכב הבא")
    f1,f2,f3=st.columns(3)
    with f1: purchase_type=st.radio("סוג רכישה", options=["הכול","חדש בלבד","משומש בלבד"], index=0, horizontal=True)
    with f2: max_used_age=st.selectbox("גיל מקסימלי לרכב משומש שאפשר לקנות", options=[3,5,7,10,15], index=1)
    with f3: allow_negative_equity_roll=st.checkbox("לאפשר גלגול יתרת הלוואה שלילית למימון הבא", value=True)
    c1,c2,c3=st.columns(3)
    with c1:
        cats=sorted(market_data['category'].dropna().unique().tolist())
        selected_categories=st.multiselect("קטגוריית רכב", options=cats, default=cats)
    with c2:
        powers=sorted(market_data['powertrain'].dropna().unique().tolist())
        selected_powertrains=st.multiselect("סוג הנעה", options=powers, default=powers)
    with c3:
        owns=sorted(market_data['ownership_type'].dropna().unique().tolist())
        selected_ownership_types=st.multiselect("מקור/סוג בעלות", options=owns, default=owns)
    filtered_data=market_data[
        market_data['category'].isin(selected_categories) & market_data['powertrain'].isin(selected_powertrains) & market_data['ownership_type'].isin(selected_ownership_types) & (market_data['purchase_price']<=max_purchase_price)
    ].copy()
    if purchase_type=="חדש בלבד": filtered_data=filtered_data[filtered_data['vehicle_age_years']==0].copy()
    elif purchase_type=="משומש בלבד": filtered_data=filtered_data[(filtered_data['vehicle_age_years']>0)&(filtered_data['vehicle_age_years']<=max_used_age)].copy()
    else: filtered_data=filtered_data[(filtered_data['vehicle_age_years']==0)|((filtered_data['vehicle_age_years']>0)&(filtered_data['vehicle_age_years']<=max_used_age))].copy()
    st.info(f"לאחר סינון נותרו {len(filtered_data):,} אפשרויות רכב לבדיקה.")

params={
    'current_vehicle_value':current_vehicle_value,
    'current_vehicle_age_years':current_vehicle_age_years,
    'max_current_vehicle_age_years':max_current_vehicle_age_years,
    'current_annual_depr_rate':current_annual_depr_rate_percent/100,
    'timing_step_months':timing_step_months,
    'manual_max_wait_months':manual_max_wait_months,
    'has_existing_loan':has_existing_loan,
    'existing_loan_balance':existing_loan_balance,
    'existing_monthly_payment':existing_monthly_payment,
    'existing_remaining_months':existing_remaining_months,
    'existing_interest_rate':existing_interest_rate,
    'extra_cash_at_purchase':extra_cash_at_purchase,
    'max_monthly_payment':max_monthly_payment,
    'next_interest_rate':next_interest_rate,
    'next_loan_months':next_loan_months,
    'next_hold_years':next_hold_years,
    'annual_km':annual_km,
    'allow_negative_equity_roll':allow_negative_equity_roll,
}

with tab_results:
    st.subheader("תוצאות אופטימיזציה")
    results=run_timing_optimization(filtered_data, params)
    if results.empty:
        st.warning("אין תוצאות לפי האילוצים והסינונים הנוכחיים.")
    else:
        best=results.iloc[0]
        r1,r2,r3,r4=st.columns(4)
        with r1: st.metric("המלצת תזמון", best['המלצת תזמון'])
        with r2: st.metric("הרכב הבא", f"{best['יצרן']} {best['דגם']}")
        with r3: st.metric("החזר חודשי לרכב הבא", f"{best['החזר חודשי הבא']:,.0f} ₪")
        with r4: st.metric("עלות חודשית כלכלית", f"{best['עלות חודשית כלכלית']:,.0f} ₪")
        st.write(f"נקודת המכירה המומלצת לפי המודל: **{best['חודשי המתנה עד מכירה']} חודשים**. שווי מכירה צפוי של הרכב הקיים אז: **{best['שווי רכב קיים בעת מכירה']:,.0f} ₪**.")
        if best['עומד באילוץ החזר']=='כן': st.success("האפשרות המובילה עומדת בתקרת ההחזר החודשי שהגדרת.")
        else: st.warning("האפשרות המובילה כלכלית, אך אינה עומדת בתקרת ההחזר החודשי.")
        st.subheader("דירוג מלא")
        st.dataframe(results, use_container_width=True, hide_index=True)
        st.subheader("גרף — האפשרויות הזולות ביותר לפי עלות חודשית כלכלית")
        chart=results.head(15).copy(); chart['שם']=chart['המלצת תזמון'].astype(str)+' | '+chart['יצרן'].astype(str)+' '+chart['דגם'].astype(str)+' '+chart['שנתון'].astype(str)
        st.bar_chart(chart.set_index('שם')['עלות חודשית כלכלית'])
        st.download_button("הורדת התוצאות כ-CSV", data=results.to_csv(index=False).encode('utf-8-sig'), file_name='car_timing_optimizer_results.csv', mime='text/csv')

with tab_optional:
    st.subheader("עלויות נלוות — לא חלק מהאופטימיזציה הראשית")
    st.write("כאן אפשר בעתיד להוסיף ביטוח, דלק, חשמל, טיפולים, צמיגים ואגרות. בגרסה הזו הן לא נכנסות לציון המרכזי, בהתאם לבקשתך.")
    st.info("הסיבה: בהחלטת תזמון מכירה וקנייה רצינו להתמקד בשחיקת מחיר, הלוואה, תשלום חודשי ותזמון.")
with tab_data:
    st.subheader("הנתונים שהאפליקציה משתמשת בהם")
    st.dataframe(market_data, use_container_width=True, hide_index=True)
    st.subheader("עמודות חובה")
    st.write(', '.join(REQUIRED_COLUMNS))
with tab_help:
    st.subheader("מה המודל עושה?")
    st.write("המודל עובר על נקודות זמן אפשריות למכירת הרכב הקיים: עכשיו, בעוד כמה חודשים, ועד מגבלת הגיל/המתנה שהוגדרה.")
    st.write("בכל נקודת זמן הוא מעריך את שווי הרכב הקיים, יתרת ההלוואה שתישאר, ההון שישמש כמקדמה, ואת ההחזר החודשי על הרכב הבא.")
    st.write("לאחר מכן הוא מדרג כל שילוב של תזמון מכירה + רכב הבא לפי עלות חודשית כלכלית, עם קנס כבד לאפשרויות שעוברות את תקרת ההחזר.")
    st.warning("הנתונים במדגם הם הדגמה בלבד. כדי להפוך את המחשבון לכלי החלטה אמיתי, צריך להזין נתוני שוק אמיתיים.")
