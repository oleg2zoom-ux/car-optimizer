from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = ROOT / "data" / "vehicle_reference.csv"
REPLACEMENT_PATH = ROOT / "data" / "replacement_options.csv"

REPLACEMENT_REQUIRED_COLUMNS = [
    "record_id",
    "manufacturer",
    "model",
    "trim",
    "model_year",
    "vehicle_age_years",
    "category",
    "powertrain",
    "ownership_type",
    "purchase_price",
    "annual_depr_rate",
    "risk_sigma",
    "warranty_years",
    "parts_support_years",
    "reliability_risk_factor",
    "source_type",
    "source_confidence",
]

NUMERIC_COLUMNS = [
    "model_year",
    "vehicle_age_years",
    "km",
    "hand",
    "msrp_new",
    "asking_price",
    "deal_price_est",
    "trade_in_price_est",
    "purchase_price",
    "annual_depr_rate",
    "risk_sigma",
    "warranty_years",
    "parts_support_years",
    "reliability_risk_factor",
    "source_confidence",
]


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]

    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "trim" in df.columns:
        df["trim"] = df["trim"].fillna("")

    return df


def load_vehicle_reference() -> pd.DataFrame:
    return normalize_dataframe(pd.read_csv(REFERENCE_PATH))


def load_replacement_options(uploaded_file=None) -> pd.DataFrame:
    if uploaded_file is None:
        df = pd.read_csv(REPLACEMENT_PATH)
    else:
        filename = uploaded_file.name.lower()
        if filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)

    return normalize_dataframe(df)


def validate_replacement_columns(df: pd.DataFrame) -> list[str]:
    errors = []
    missing = [c for c in REPLACEMENT_REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        errors.append("חסרות עמודות חובה: " + ", ".join(missing))

    if "purchase_price" in df.columns and df["purchase_price"].isna().any():
        errors.append("יש שורות ללא purchase_price תקין.")

    for col in ["annual_depr_rate", "risk_sigma", "source_confidence"]:
        if col in df.columns:
            values = df[col].dropna()
            if not values.between(0, 1).all():
                errors.append(f"{col} חייב להיות בין 0 ל-1.")

    return errors
