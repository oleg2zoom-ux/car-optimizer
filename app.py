import streamlit as st
import pandas as pd

from car_optimizer.data_loader import load_market_data, validate_columns, REQUIRED_COLUMNS
from car_optimizer.finance import monthly_payment, total_interest_paid
from car_optimizer.optimizer import run_optimization
from car_optimizer.constants import DEFAULTS


st.set_page_config(
    page_title="מחשבון אופטימיזציית רכישת רכב",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)


RTL_CSS = """
<style>
html, body, [class*="css"] {
    direction: rtl;
    text-align: right;
}
section[data-testid="stSidebar"] {
    direction: rtl;
    text-align: right;
}
.stDataFrame, .dataframe {
    direction: rtl;
}
div[data-testid="stMetric"] {
    direction: rtl;
    text-align: right;
}
</style>
"""
st.markdown(RTL_CSS, unsafe_allow_html=True)


st.title("🚗 מחשבון אופטימיזציית רכישת רכב")
st.caption(
    "גרסת MVP: השוואת עלות בעלות חודשית צפויה לפי מחיר רכישה, ירידת ערך, "
    "מימון, הון עצמי ועלויות שימוש."
)

with st.sidebar:
    st.header("המצב הכספי שלי")

    current_car_sale = st.number_input(
        "שווי מכירת הרכב הנוכחי",
        min_value=0,
        value=DEFAULTS["current_car_sale"],
        step=1000,
    )

    extra_cash = st.number_input(
        "הון עצמי נוסף שאני מוכן להוסיף",
        min_value=0,
        value=DEFAULTS["extra_cash"],
        step=1000,
    )

    max_monthly_payment = st.number_input(
        "החזר חודשי מקסימלי להלוואה",
        min_value=0,
        value=DEFAULTS["max_monthly_payment"],
        step=100,
    )

    annual_interest_rate = st.number_input(
        "ריבית שנתית משוערת (%)",
        min_value=0.0,
        value=float(DEFAULTS["annual_interest_rate"]),
        step=0.25,
    )

    loan_months = st.slider(
        "תקופת הלוואה בחודשים",
        min_value=12,
        max_value=120,
        value=DEFAULTS["loan_months"],
        step=12,
    )

    hold_years = st.slider(
        "כמה שנים מתכננים להחזיק את הרכב?",
        min_value=1,
        max_value=10,
        value=DEFAULTS["hold_years"],
        step=1,
    )

    annual_km = st.number_input(
        "ק״מ שנתי צפוי",
        min_value=0,
        value=DEFAULTS["annual_km"],
        step=1000,
    )

    st.header("עלויות שימוש חודשיות")

    insurance_monthly = st.number_input(
        "ביטוח חודשי משוער",
        min_value=0,
        value=DEFAULTS["insurance_monthly"],
        step=50,
    )

    maintenance_monthly = st.number_input(
        "תחזוקה, טיפולים וצמיגים — חודשי",
        min_value=0,
        value=DEFAULTS["maintenance_monthly"],
        step=50,
    )

    license_monthly = st.number_input(
        "רישוי חודשי ממוצע",
        min_value=0,
        value=DEFAULTS["license_monthly"],
        step=25,
    )

    energy_monthly = st.number_input(
        "דלק / חשמל חודשי",
        min_value=0,
        value=DEFAULTS["energy_monthly"],
        step=50,
    )


tab_input, tab_results, tab_data, tab_help = st.tabs(
    ["טעינת נתונים וסינון", "תוצאות", "נתונים גולמיים", "עזרה"]
)

with tab_input:
    st.subheader("מקור הנתונים")
    uploaded_file = st.file_uploader(
        "אפשר להעלות קובץ CSV או Excel לפי הסכמה. בלי העלאה — המחשבון משתמש במדגם הדגמה.",
        type=["csv", "xlsx", "xls"],
    )

    data = load_market_data(uploaded_file)
    errors = validate_columns(data)

    if errors:
        st.error("הקובץ לא מתאים לסכמה הנדרשת.")
        for err in errors:
            st.write(f"• {err}")
        st.stop()

    st.success(f"נטענו {len(data):,} תצפיות רכב.")

    col1, col2, col3 = st.columns(3)

    with col1:
        categories = sorted(data["category"].dropna().unique().tolist())
        selected_categories = st.multiselect(
            "קטגוריית רכב",
            options=categories,
            default=categories,
        )

    with col2:
        powertrains = sorted(data["powertrain"].dropna().unique().tolist())
        selected_powertrains = st.multiselect(
            "סוג הנעה",
            options=powertrains,
            default=powertrains,
        )

    with col3:
        ownership_types = sorted(data["ownership_type"].dropna().unique().tolist())
        selected_ownerships = st.multiselect(
            "סוג בעלות / מקור",
            options=ownership_types,
            default=ownership_types,
        )

    min_year = int(data["model_year"].min())
    max_year = int(data["model_year"].max())
    default_min_year = max(min_year, max_year - 8)

    year_range = st.slider(
        "טווח שנתונים",
        min_value=min_year,
        max_value=max_year,
        value=(default_min_year, max_year),
        step=1,
    )

    max_purchase_price = st.number_input(
        "מחיר רכישה מקסימלי לבדיקה",
        min_value=0,
        value=int(max(data["purchase_price"].max(), 200000)),
        step=5000,
    )

    filtered = data[
        data["category"].isin(selected_categories)
        & data["powertrain"].isin(selected_powertrains)
        & data["ownership_type"].isin(selected_ownerships)
        & data["model_year"].between(year_range[0], year_range[1])
        & (data["purchase_price"] <= max_purchase_price)
    ].copy()

    st.info(f"לאחר סינון נותרו {len(filtered):,} אפשרויות.")


params = {
    "current_car_sale": current_car_sale,
    "extra_cash": extra_cash,
    "max_monthly_payment": max_monthly_payment,
    "annual_interest_rate": annual_interest_rate,
    "loan_months": loan_months,
    "hold_years": hold_years,
    "annual_km": annual_km,
    "insurance_monthly": insurance_monthly,
    "maintenance_monthly": maintenance_monthly,
    "license_monthly": license_monthly,
    "energy_monthly": energy_monthly,
}

if "filtered" not in locals():
    filtered = data.copy()

results = run_optimization(filtered, params)

with tab_results:
    st.subheader("המלצה כלכלית")

    if results.empty:
        st.warning("אין תוצאות לפי הסינון הנוכחי.")
    else:
        best = results.iloc[0]

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("האופציה המובילה", f"{best['יצרן']} {best['דגם']}")
        with c2:
            st.metric("החזר חודשי", f"{best['החזר חודשי']:,.0f} ₪")
        with c3:
            st.metric("עלות בעלות חודשית", f"{best['עלות בעלות חודשית']:,.0f} ₪")
        with c4:
            st.metric("שווי עתידי צפוי", f"{best['שווי עתידי צפוי']:,.0f} ₪")

        if best["עובר מגבלת החזר"] == "כן":
            st.success("האופציה המובילה עומדת במגבלת ההחזר החודשי שהוגדרה.")
        else:
            st.warning("האופציה המובילה כלכלית, אבל אינה עומדת במגבלת ההחזר החודשי.")

        st.subheader("דירוג אפשרויות")
        st.dataframe(results, use_container_width=True, hide_index=True)

        st.subheader("גרף עלות בעלות חודשית — 15 האפשרויות הראשונות")
        chart = results.head(15).copy()
        chart["שם"] = (
            chart["יצרן"].astype(str)
            + " "
            + chart["דגם"].astype(str)
            + " "
            + chart["שנתון"].astype(str)
        )
        st.bar_chart(chart.set_index("שם")["עלות בעלות חודשית"])

        csv_bytes = results.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "הורדת תוצאות כ-CSV",
            data=csv_bytes,
            file_name="car_optimizer_results.csv",
            mime="text/csv",
        )

with tab_data:
    st.subheader("הנתונים שהמחשבון משתמש בהם")
    st.dataframe(data, use_container_width=True, hide_index=True)

    st.subheader("עמודות חובה")
    st.write(", ".join(REQUIRED_COLUMNS))

with tab_help:
    st.subheader("איך לקרוא את התוצאה?")
    st.write(
        "המחשבון לא בוחר את הרכב הכי יפה או הכי מפנק. הוא מדרג לפי עלות בעלות חודשית צפויה "
        "תחת מגבלות ההון העצמי, הריבית וההחזר החודשי."
    )
    st.write(
        "עלות בעלות חודשית כוללת ירידת ערך צפויה, ריבית מימון ועלויות שוטפות. "
        "שווי עתידי מחושב לפי מקדם שחיקה שנתי וסיכון סטטיסטי."
    )
    st.warning(
        "בגרסה זו הנתונים הם מדגם הדגמה בלבד. לפני החלטת רכישה אמיתית צריך להזין נתוני שוק אמיתיים "
        "ממחירוני רכב, מודעות, טרייד-אין ומקורות נוספים."
    )
