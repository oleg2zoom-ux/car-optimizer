from datetime import date

import pandas as pd
import streamlit as st

from car_optimizer.constants import DEFAULTS
from car_optimizer.data_loader import (
    load_replacement_options,
    load_vehicle_reference,
    validate_replacement_columns,
)
from car_optimizer.optimizer import run_owner_first_optimization
from car_optimizer.valuation_model import estimate_current_vehicle_value


st.set_page_config(
    page_title="מחשבון החלטת החלפת רכב",
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
.small-note {
    color: #666;
    font-size: 0.92rem;
}
</style>
"""
st.markdown(RTL_CSS, unsafe_allow_html=True)

today = date.today()

st.title("🚗 מחשבון החלטת החלפת רכב")
st.caption(
    "גרסה 0.4: מתחילים מהרכב הקיים של הבעלים, מזהים רפרנס, מעריכים שווי, "
    "בודקים הלוואה קיימת, חיסכון עתידי, סיכון גיל/אחריות, ומוצאים מועד החלפה אופטימלי."
)

vehicle_ref = load_vehicle_reference()

tab_owner, tab_current_loan, tab_next, tab_results, tab_data, tab_help = st.tabs(
    [
        "1. הרכב הקיים",
        "2. הלוואה וחיסכון",
        "3. הרכב הבא והאילוצים",
        "4. המלצה ותוצאות",
        "5. נתונים",
        "עזרה",
    ]
)

with tab_owner:
    st.subheader("זיהוי הרכב הקיים")

    manufacturers = sorted(vehicle_ref["manufacturer"].dropna().unique().tolist())
    selected_manufacturer = st.selectbox("יצרן", manufacturers)

    models = sorted(
        vehicle_ref.loc[
            vehicle_ref["manufacturer"] == selected_manufacturer, "model"
        ].dropna().unique().tolist()
    )
    selected_model = st.selectbox("דגם", models)

    ref_subset = vehicle_ref[
        (vehicle_ref["manufacturer"] == selected_manufacturer)
        & (vehicle_ref["model"] == selected_model)
    ].copy()

    trims = sorted(ref_subset["trim"].dropna().unique().tolist())
    selected_trim = st.selectbox("רמת גימור / משפחת דגם", trims)

    selected_ref = ref_subset[ref_subset["trim"] == selected_trim].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        current_model_year = st.number_input(
            "שנתון הרכב",
            min_value=1990,
            max_value=today.year + 1,
            value=int(DEFAULTS["current_model_year"]),
            step=1,
        )
    with c2:
        current_km = st.number_input(
            "ק״מ נוכחי",
            min_value=0,
            value=DEFAULTS["current_km"],
            step=5000,
        )
    with c3:
        current_hand = st.number_input(
            "יד",
            min_value=0,
            value=DEFAULTS["current_hand"],
            step=1,
        )
    with c4:
        ownership_type = st.selectbox(
            "סוג בעלות",
            ["Private Used", "Leasing Used", "Rental", "Company"],
            index=0,
        )

    st.markdown("---")
    st.subheader("מחיר רכישה ושווי נוכחי")

    p1, p2, p3 = st.columns(3)
    with p1:
        purchase_year = st.number_input(
            "שנת רכישה אצל הבעלים",
            min_value=1990,
            max_value=today.year,
            value=min(max(int(DEFAULTS["purchase_year"]), 1990), today.year),
            step=1,
        )
    with p2:
        purchase_month = st.selectbox(
            "חודש רכישה",
            options=list(range(1, 13)),
            index=int(DEFAULTS["purchase_month"]) - 1,
        )
    with p3:
        known_purchase_price = st.number_input(
            "מחיר רכישה ידוע, אם יש",
            min_value=0,
            value=DEFAULTS["known_purchase_price"],
            step=1000,
            help="אם לא ידוע — השאר 0. המודל ישתמש במחיר חדש/רפרנס.",
        )

    k1, k2 = st.columns(2)
    with k1:
        known_current_value = st.number_input(
            "שווי שוק ידוע היום, אם יש",
            min_value=0,
            value=DEFAULTS["known_current_value"],
            step=1000,
            help="אם אתה יודע מחירון/מחיר מכירה ריאלי — הזן. אחרת המודל יחשב.",
        )
    with k2:
        current_value_safety_margin = st.number_input(
            "מרווח שמרנות לשווי רכב קיים (%)",
            min_value=0.0,
            max_value=30.0,
            value=float(DEFAULTS["current_value_safety_margin_percent"]),
            step=1.0,
            help="מפחית את שווי הרכב לצורך החלטה שמרנית.",
        )

    current_info = {
        "manufacturer": selected_manufacturer,
        "model": selected_model,
        "trim": selected_trim,
        "model_year": int(current_model_year),
        "km": int(current_km),
        "hand": int(current_hand),
        "ownership_type": ownership_type,
        "purchase_year": int(purchase_year),
        "purchase_month": int(purchase_month),
        "known_purchase_price": float(known_purchase_price),
        "known_current_value": float(known_current_value),
        "current_value_safety_margin": float(current_value_safety_margin) / 100,
        "reference": selected_ref.to_dict(),
    }

    estimated = estimate_current_vehicle_value(current_info, today)

    st.info(
        f"שווי נוכחי משוער לאחר מרווח שמרנות: **{estimated['estimated_value_after_margin']:,.0f} ₪**. "
        f"גיל רכב מחושב: **{estimated['vehicle_age_years']:.1f} שנים**. "
        f"שיטת הערכה: **{estimated['method']}**."
    )

    st.write(
        f"אחריות יצרן לפי רפרנס: **{selected_ref['warranty_years']} שנים**. "
        f"תמיכת חלפים רפרנס: **{selected_ref['parts_support_years']} שנים**. "
        f"מקדם סיכון בסיסי: **{selected_ref['reliability_risk_factor']}**."
    )

with tab_current_loan:
    st.subheader("הלוואה קיימת וחיסכון עד החלפה")

    has_existing_loan = st.checkbox(
        "יש הלוואה קיימת על הרכב",
        value=DEFAULTS["has_existing_loan"],
    )

    if has_existing_loan:
        l1, l2, l3, l4 = st.columns(4)
        with l1:
            existing_loan_balance = st.number_input(
                "יתרת הלוואה קיימת",
                min_value=0,
                value=DEFAULTS["existing_loan_balance"],
                step=1000,
            )
        with l2:
            existing_monthly_payment = st.number_input(
                "החזר חודשי קיים",
                min_value=0,
                value=DEFAULTS["existing_monthly_payment"],
                step=100,
            )
        with l3:
            existing_remaining_months = st.number_input(
                "חודשים שנותרו בהלוואה הקיימת",
                min_value=0,
                max_value=180,
                value=DEFAULTS["existing_remaining_months"],
                step=1,
            )
        with l4:
            existing_interest_rate = st.number_input(
                "ריבית שנתית בהלוואה הקיימת (%)",
                min_value=0.0,
                max_value=25.0,
                value=float(DEFAULTS["existing_interest_rate"]),
                step=0.25,
            )
    else:
        existing_loan_balance = 0
        existing_monthly_payment = 0
        existing_remaining_months = 0
        existing_interest_rate = 0.0

    st.markdown("---")
    st.subheader("חיסכון אפשרי אם לא מחליפים עכשיו")

    s1, s2, s3 = st.columns(3)
    with s1:
        extra_cash_today = st.number_input(
            "הון עצמי זמין היום לרכב הבא",
            min_value=0,
            value=DEFAULTS["extra_cash_today"],
            step=1000,
        )
    with s2:
        monthly_saving_capacity = st.number_input(
            "יכולת חיסכון חודשית נוספת עד הקנייה",
            min_value=0,
            value=DEFAULTS["monthly_saving_capacity"],
            step=100,
            help="חיסכון מעבר להחזר ההלוואה הקיימת.",
        )
    with s3:
        redirect_finished_loan_to_savings = st.checkbox(
            "לאחר סיום ההלוואה הקיימת — להפנות את ההחזר לחיסכון לרכב הבא",
            value=True,
        )

    st.info(
        "אם ההלוואה הקיימת נגמרת לפני מועד ההחלפה, המודל יכול להמליץ להמשיך לחסוך "
        "עוד מספר חודשים כדי להקטין את המימון לרכב הבא."
    )

with tab_next:
    st.subheader("הרכב הבא והאילוצים")

    uploaded_file = st.file_uploader(
        "אפשר להעלות קובץ אפשרויות רכישה CSV/Excel. בלי העלאה — נטען מדגם הדגמה.",
        type=["csv", "xlsx", "xls"],
    )

    replacement_options = load_replacement_options(uploaded_file)
    errors = validate_replacement_columns(replacement_options)

    if errors:
        st.error("קובץ אפשרויות הרכישה אינו מתאים.")
        for err in errors:
            st.write(f"• {err}")
        st.stop()

    n1, n2, n3 = st.columns(3)
    with n1:
        max_monthly_payment = st.number_input(
            "תקרת החזר חודשית לרכב הבא",
            min_value=0,
            value=DEFAULTS["max_monthly_payment"],
            step=100,
        )
    with n2:
        next_interest_rate = st.number_input(
            "ריבית שנתית למימון הרכב הבא (%)",
            min_value=0.0,
            max_value=25.0,
            value=float(DEFAULTS["next_interest_rate"]),
            step=0.25,
        )
    with n3:
        next_loan_months = st.selectbox(
            "תקופת מימון לרכב הבא",
            options=[12, 24, 36, 48, 60, 72, 84, 96, 108, 120],
            index=4,
        )

    n4, n5, n6 = st.columns(3)
    with n4:
        next_hold_years = st.selectbox(
            "כמה שנים להחזיק את הרכב הבא?",
            options=[1, 2, 3, 4, 5, 6, 7, 8, 10],
            index=4,
        )
    with n5:
        max_purchase_price = st.number_input(
            "מחיר רכישה מקסימלי לרכב הבא",
            min_value=0,
            value=DEFAULTS["max_purchase_price"],
            step=5000,
        )
    with n6:
        annual_km = st.number_input(
            "ק״מ שנתי צפוי",
            min_value=0,
            value=DEFAULTS["annual_km"],
            step=1000,
        )

    f1, f2, f3 = st.columns(3)
    with f1:
        purchase_type = st.radio(
            "סוג רכישה",
            ["הכול", "חדש בלבד", "משומש בלבד"],
            horizontal=True,
        )
    with f2:
        max_used_age = st.selectbox(
            "גיל מקסימלי לרכב משומש",
            options=[3, 5, 7, 10, 15],
            index=1,
        )
    with f3:
        risk_tolerance = st.selectbox(
            "רגישות לסיכון גיל/אחריות",
            options=["נמוכה", "בינונית", "גבוהה"],
            index=1,
            help="רגישות גבוהה מענישה יותר רכבים מחוץ לאחריות/מעל 7 שנים.",
        )

    st.markdown("---")
    st.subheader("סינון סוג רכב")

    c1, c2, c3 = st.columns(3)
    with c1:
        categories = sorted(replacement_options["category"].dropna().unique().tolist())
        selected_categories = st.multiselect("קטגוריה", categories, default=categories)
    with c2:
        powertrains = sorted(replacement_options["powertrain"].dropna().unique().tolist())
        selected_powertrains = st.multiselect("הנעה", powertrains, default=powertrains)
    with c3:
        ownerships = sorted(replacement_options["ownership_type"].dropna().unique().tolist())
        selected_ownerships = st.multiselect("מקור/בעלות", ownerships, default=ownerships)

    filtered_options = replacement_options[
        replacement_options["category"].isin(selected_categories)
        & replacement_options["powertrain"].isin(selected_powertrains)
        & replacement_options["ownership_type"].isin(selected_ownerships)
        & (replacement_options["purchase_price"] <= max_purchase_price)
    ].copy()

    if purchase_type == "חדש בלבד":
        filtered_options = filtered_options[filtered_options["vehicle_age_years"] == 0].copy()
    elif purchase_type == "משומש בלבד":
        filtered_options = filtered_options[
            (filtered_options["vehicle_age_years"] > 0)
            & (filtered_options["vehicle_age_years"] <= max_used_age)
        ].copy()
    else:
        filtered_options = filtered_options[
            (filtered_options["vehicle_age_years"] == 0)
            | (
                (filtered_options["vehicle_age_years"] > 0)
                & (filtered_options["vehicle_age_years"] <= max_used_age)
            )
        ].copy()

    st.info(f"לאחר סינון נותרו {len(filtered_options):,} אפשרויות רכישה.")

    t1, t2 = st.columns(2)
    with t1:
        max_wait_months = st.number_input(
            "מקסימום חודשים להמתין לפני החלפה",
            min_value=0,
            max_value=180,
            value=DEFAULTS["max_wait_months"],
            step=3,
        )
    with t2:
        timing_step_months = st.selectbox(
            "כל כמה חודשים לבדוק מועד החלפה",
            options=[1, 3, 6, 12],
            index=2,
        )

with tab_results:
    st.subheader("המלצה")

    params = {
        "today": today,
        "current_info": current_info,
        "current_estimate": estimated,
        "has_existing_loan": bool(has_existing_loan),
        "existing_loan_balance": float(existing_loan_balance),
        "existing_monthly_payment": float(existing_monthly_payment),
        "existing_remaining_months": int(existing_remaining_months),
        "existing_interest_rate": float(existing_interest_rate),
        "extra_cash_today": float(extra_cash_today),
        "monthly_saving_capacity": float(monthly_saving_capacity),
        "redirect_finished_loan_to_savings": bool(redirect_finished_loan_to_savings),
        "max_monthly_payment": float(max_monthly_payment),
        "next_interest_rate": float(next_interest_rate),
        "next_loan_months": int(next_loan_months),
        "next_hold_years": int(next_hold_years),
        "annual_km": float(annual_km),
        "max_used_age": int(max_used_age),
        "risk_tolerance": risk_tolerance,
        "max_wait_months": int(max_wait_months),
        "timing_step_months": int(timing_step_months),
    }

    results = run_owner_first_optimization(filtered_options, params)

    if results.empty:
        st.warning("אין תוצאות לפי האילוצים שנבחרו.")
    else:
        best = results.iloc[0]

        b1, b2, b3, b4 = st.columns(4)
        with b1:
            st.metric("המלצה", best["המלצת פעולה"])
        with b2:
            st.metric("מועד החלפה", best["מועד החלפה"])
        with b3:
            st.metric("רכב הבא", f"{best['יצרן']} {best['דגם']}")
        with b4:
            st.metric("עלות חודשית כלכלית", f"{best['עלות חודשית כלכלית']:,.0f} ₪")

        st.success(best["נימוק המלצה"])

        st.write(
            f"החזר חודשי צפוי לרכב הבא: **{best['החזר חודשי לרכב הבא']:,.0f} ₪**. "
            f"הון עצמי צפוי במועד הקנייה: **{best['הון עצמי צפוי במועד קנייה']:,.0f} ₪**. "
            f"שווי הרכב הקיים במועד מכירה: **{best['שווי רכב קיים במועד מכירה']:,.0f} ₪**."
        )

        if best["עומד בתקרת החזר"] == "כן":
            st.info("האופציה עומדת בתקרת ההחזר החודשית.")
        else:
            st.warning("האופציה אינה עומדת בתקרת ההחזר החודשית ולכן קיבלה קנס בדירוג.")

        st.subheader("טבלת תרחישים")
        st.dataframe(results, use_container_width=True, hide_index=True)

        st.subheader("גרף 15 התרחישים המובילים")
        chart = results.head(15).copy()
        chart["תרחיש"] = (
            chart["מועד החלפה"].astype(str)
            + " | "
            + chart["יצרן"].astype(str)
            + " "
            + chart["דגם"].astype(str)
            + " "
            + chart["שנתון"].astype(str)
        )
        st.bar_chart(chart.set_index("תרחיש")["עלות חודשית כלכלית"])

        csv_bytes = results.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "הורדת תוצאות כ-CSV",
            data=csv_bytes,
            file_name="owner_first_car_optimizer_results.csv",
            mime="text/csv",
        )

with tab_data:
    st.subheader("מאגר רפרנס רכבים")
    st.dataframe(vehicle_ref, use_container_width=True, hide_index=True)

    st.subheader("אפשרויות רכישה")
    st.dataframe(replacement_options, use_container_width=True, hide_index=True)

with tab_help:
    st.subheader("מה המודל עושה?")
    st.write(
        "המודל מתחיל מהרכב הקיים שלך. הוא מעריך שווי נוכחי לפי מחיר ידוע, מחיר רכישה, "
        "מחיר חדש או רפרנס פחת."
    )
    st.write(
        "לאחר מכן הוא בודק נקודות החלפה אפשריות: עכשיו, אחרי סיום הלוואה, אחרי עוד כמה חודשי חיסכון, "
        "ולפי מדרגות גיל/אחריות כגון 3, 5, 7, 10 ו-15 שנים."
    )
    st.write(
        "בכל תרחיש מחושבים: שווי הרכב הקיים במועד המכירה, יתרת הלוואה, הון עצמי זמין, "
        "מימון נדרש לרכב הבא, החזר חודשי, ירידת ערך וסיכון גיל/אחריות."
    )
    st.warning(
        "קנס סיכון גיל/אחריות אינו הוצאה ודאית. זהו רכיב החלטה שמטרתו למנוע מהמודל להמליץ אוטומטית "
        "להחזיק רכב ישן מאוד רק כי הפחת שלו נמוך."
    )
