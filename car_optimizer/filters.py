import pandas as pd

CATEGORY_GROUPS = {
    "מיני": [
        "מיני",
        "סופר מיני",
        "מיני / פנאי קטן",
    ],
    "משפחתי": [
        "משפחתית",
        "משפחתית קומפקטית",
        "משפחתית גדולה",
        "משפחתית חשמלית",
        "יוקרה קומפקטית",
    ],
    "פנאי שטח": [
        "קרוסאובר",
        "פנאי",
        "שטח",
        "SUV",
        "טנדר",
        "מסחרי/משפחתי",
        "יוקרה / קרוסאובר",
        "קרוסאובר חשמלי",
    ],
}


def apply_high_level_category_filter(
    df: pd.DataFrame,
    high_level_category: str,
    category_column: str = "category",
) -> pd.DataFrame:
    if df.empty or category_column not in df.columns:
        return df.copy()

    terms = CATEGORY_GROUPS.get(high_level_category, [])
    if not terms:
        return df.copy()

    pattern = "|".join(terms)
    mask = df[category_column].fillna("").astype(str).str.contains(pattern, regex=True)
    return df[mask].copy()
