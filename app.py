from datetime import date

import streamlit as st

from car_optimizer.constants import DEFAULTS, PRIORITY_LABELS
from car_optimizer.data_loader import (
    load_replacement_options,
    load_vehicle_reference,
    validate_replacement_columns,
)
from car_optimizer.filters import apply_high_level_category_filter
from car_optimizer.optimizer import run_owner_first_optimization
from car_optimizer.valuation_model import estimate_current_vehicle_value


st.set_page_config(
    page_title="מחשבון החלפת רכב — Owner First",
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
    "v0.7 — מתחילים מבחירת קטגוריה ועדיפות החלטה, ואז הרכב הקיים, הלוואה, חיסכון, "
    "רכב הבא, אילוץ החזר חודשי ומיון התרחישים."
)

vehicle_ref = load_vehicle_reference()

tab_strategy, tab_owner, tab_current_loan, tab_next, tab_results, tab_data, tab_help = st.tabs(
    [
        "1. קטגוריה ועדיפות",
        "2. הרכב הקיים",
        "3. הלוואה וחיסכון",
        "4. הרכב הבא והאילוצים",
        "5. המלצה ותוצאות",
        "6. נתונים",
        "עזרה",
    ]
)

with tab_strategy:
    st.subheader("בחירת קטגוריה ראשית ועדיפות חישוב")

    s1, s2, s3 = st.columns(3)

    with s1:
        high_level_category = st.radio(
            "איזו קטגוריית רכב אתה מחפש?",
            options=["מיני", "משפחתי", "פנאי שטח"],
            index=2,
            help="הסינון הזה מתבצע לפני כל חישוב אחר.",
        )

    with s2:
        decision_priority_label = st.selectbox(
            "מה עדיפות המיון?",
            options=list(PRIORITY_LABELS.keys()),
            index=0,
        )
        decision_priority = PRIORITY_LABELS[decision_priority_label]

    with s3:
        min_source_confidence = st.slider(
            "רמת אמינות מינימלית לנתוני מחיר",
            min_value=0.0,
            max_value=1.0,
            value=0.50,
            step=0.05,
            help="0.85 ומעלה = מחירים מאומתים יחסית. 0.50 מאפשר גם seed רחב יותר.",
        )

    include_needs_review = st.checkbox(
        "להציג גם שורות מחיר שדורשות אימות",
        value=True,
        help="כדאי להשאיר פעיל לבדיקות רחבות, אבל בהחלטת רכישה אמיתית עדיף לסנן אותן.",
    )

    st.info(
        f"המודל יסנן קודם את קטגוריית **{high_level_category}** ואז ימיין לפי עדיפות: "
        f"**{decision_priority_label}**."
    )

    if include_needs_review:
        st.warning(
            "שים לב: חלק גדול ממאגר v0.6 הוא seed להרחבת הנתונים ומסומן needs_review='כן'. "
            "המודל נותן קנס לשורות כאלה, אבל הן עדיין מופיעות אם מאפשרים אותן."
        )

with tab_owner:
    st.subheader("זיהוי הרכב הקיים")

    filtered_ref = apply_high_level_category_filter(vehicle_ref, high_level_category, category_column="category")
    if filtered_ref.empty:
        st.warning("אין רכב רפרנס בקטגוריה שנבחרה. מוצג כל המאגר.")
        filtered_ref = vehicle_ref.copy()

    manufacturers = sorted(filtered_ref["manufacturer"].dropna().astype(str).unique().tolist())
    selected_manufacturer = st.selectbox("יצרן / מותג", manufacturers)

    models = sorted(
        filtered_ref.loc[
            filtered_ref["manufacturer"].astype(str) == selected_manufacturer, "model"
        ].dropna().astype(str).unique().tolist()
    )
    selected_model = st.selectbox("דגם", models)

    ref_subset = filtered_ref[
        (filtered_ref["manufacturer"].astype(str) == selected_manufacturer)
        & (filtered_ref["model"].astype(str) == selected_model)
    ].copy()

    trims = sorted(ref_subset["trim"].fillna("").astype(str).unique().tolist())
    selected_trim = st.selectbox("רמת גימור / משפחת דגם", trims)

    selected_ref = ref_subset[ref_subset["trim"].fillna("").astype(str) == selected_trim].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        current_model_year = st.number_input(
            "שנתון הרכב",
            min_value=1990,
            max_value=today.year + 1,
            value=min(max(int(DEFAULTS["current_model_year"]), 1990), today.year + 1),
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
            help="אם יש לך מחירון/מחיר מכירה ריאלי — הזן. אחרת המודל יחשב.",
        )
    with k2:
        current_value_safety_margin = st.number_input(
            "מרווח שמרנות לשווי רכב קיים (%)",
            min_value=0.0,
            max_value=30.0,
            value=float(DEFAULTS["current_value_safety_margin_percent"]),
            step=1.0,
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
        f"שווי נוכחי משוער לאחר שמרנות: **{estimated['estimated_value_after_margin']:,.0f} ₪**. "
        f"גיל רכב מחושב: **{estimated['vehicle_age_years']:.1f} שנים**. "
        f"שיטת הערכה: **{estimated['method']}**."
    )

    st.write(
        f"אחריות יצרן ברפרנס: **{estimated['warranty_years']:.0f} שנים**. "
        f"תמיכת חלפים ברפרנס: **{estimated['parts_support_years']:.0f} שנים**. "
        f"מקדם סיכון: **{estimated['reliability_risk_factor']}**."
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
        )
    with s3:
        redirect_finished_loan_to_savings = st.checkbox(
            "אחרי סיום ההלוואה — להפנות את ההחזר לחיסכון לרכב הבא",
            value=True,
        )

with tab_next:
    st.subheader("הרכב הבא והאילוצים")

    uploaded_file = st.file_uploader(
        "אפשר להעלות CSV/Excel של אפשרויות רכישה. בלי העלאה — נטען המאגר המצורף v0.6.",
        type=["csv", "xlsx", "xls"],
    )

    replacement_options = load_replacement_options(uploaded_file)
    errors = validate_replacement_columns(replacement_options)

    if errors:
        st.error("קובץ אפשרויות הרכישה אינו מתאים.")
        for err in errors:
            st.write(f"• {err}")
        st.stop()

    replacement_options = apply_high_level_category_filter(
        replacement_options,
        high_level_category,
        category_column="category",
    )

    if "source_confidence" in replacement_options.columns:
        replacement_options = replacement_options[
            replacement_options["source_confidence"].fillna(0) >= min_source_confidence
        ].copy()

    if not include_needs_review and "needs_review" in replacement_options.columns:
        replacement_options = replacement_options[
            replacement_options["needs_review"].fillna("כן").astype(str) != "כן"
        ].copy()

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
        )

    st.markdown("---")
    st.subheader("סינון נוסף")

    c1, c2, c3 = st.columns(3)
    with c1:
        categories = sorted(replacement_options["category"].dropna().astype(str).unique().tolist())
        selected_categories = st.multiselect("קטגוריה מפורטת", categories, default=categories)
    with c2:
        powertrains = sorted(replacement_options["powertrain"].dropna().astype(str).unique().tolist())
        selected_powertrains = st.multiselect("הנעה", powertrains, default=powertrains)
    with c3:
        ownerships = sorted(replacement_options["ownership_type"].dropna().astype(str).unique().tolist())
        selected_ownerships = st.multiselect("מקור/בעלות", ownerships, default=ownerships)

    filtered_options = replacement_options[
        replacement_options["category"].astype(str).isin(selected_categories)
        & replacement_options["powertrain"].astype(str).isin(selected_powertrains)
        & replacement_options["ownership_type"].astype(str).isin(selected_ownerships)
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

    st.info(f"לאחר כל הסינונים נותרו {len(filtered_options):,} אפשרויות רכישה.")

with tab_results:
    st.subheader("המלצה ותוצאות")

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
        "decision_priority": decision_priority,
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
            f"עדיפות מיון: **{decision_priority_label}**. "
            f"החזר חודשי צפוי לרכב הבא: **{best['החזר חודשי לרכב הבא']:,.0f} ₪**. "
            f"הון עצמי צפוי במועד הקנייה: **{best['הון עצמי צפוי במועד קנייה']:,.0f} ₪**."
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
        st.bar_chart(chart.set_index("תרחיש")["ציון עדיפות"])

        csv_bytes = results.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "הורדת תוצאות כ-CSV",
            data=csv_bytes,
            file_name="owner_first_car_optimizer_results_v0_7.csv",
            mime="text/csv",
        )

with tab_data:
    st.subheader("מאגר רפרנס לרכב קיים")
    st.dataframe(vehicle_ref, use_container_width=True, hide_index=True)

    st.subheader("אפשרויות רכישה")
    st.dataframe(load_replacement_options(None), use_container_width=True, hide_index=True)

with tab_help:
    st.subheader("איך המיון עובד?")
    st.write(
        "המודל תמיד מחשב קודם עלות חודשית כלכלית, החזר חודשי, שווי רכב קיים, יתרת הלוואה, "
        "הון עצמי צפוי, שווי עתידי וסיכון גיל/אחריות."
    )
    st.write(
        "לאחר מכן הוא משנה את הציון לפי עדיפות המשתמש: חדש ככל האפשר, אמין ביותר, "
        "או שמירת ערך עתידית."
    )
    st.write(
        "שורות מחיר עם needs_review='כן' מקבלות קנס בדירוג. אם רוצים החלטה שמרנית, "
        "אפשר להוריד אותן באמצעות הסינון במסך הראשון."
    )
