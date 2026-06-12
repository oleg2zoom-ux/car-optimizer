from pathlib import Path
import pandas as pd

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "sample_cars.csv"

REQUIRED_COLUMNS = [
    "record_id",
    "manufacturer",
    "model",
    "trim",
    "model_year",
    "category",
    "powertrain",
    "ownership_type",
    "km",
    "hand",
    "purchase_price",
    "annual_depr_rate",
    "risk_sigma",
    "source_type",
    "source_confidence",
]

NUMERIC_COLUMNS = [
    "model_year",
    "km",
    "hand",
    "msrp_new",
    "asking_price",
    "deal_price_est",
    "trade_in_price_est",
    "purchase_price",
    "annual_depr_rate",
    "risk_sigma",
    "source_confidence",
]


def load_market_data(uploaded_file=None) -> pd.DataFrame:
    if uploaded_file is None:
        df = pd.read_csv(DATA_PATH)
    else:
        filename = uploaded_file.name.lower()
        if filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)

    df = normalize_dataframe(df)
    return df


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]

    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "trim" in df.columns:
        df["trim"] = df["trim"].fillna("")

    return df


def validate_columns(df: pd.DataFrame) -> list[str]:
    errors = []
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        errors.append("חסרות עמודות חובה: " + ", ".join(missing))

    if "purchase_price" in df.columns and df["purchase_price"].isna().any():
        errors.append("יש שורות ללא purchase_price תקין.")

    if "annual_depr_rate" in df.columns:
        invalid = df["annual_depr_rate"].dropna()
        if not invalid.between(0, 1).all():
            errors.append("annual_depr_rate חייב להיות בין 0 ל-1.")

    if "risk_sigma" in df.columns:
        invalid = df["risk_sigma"].dropna()
        if not invalid.between(0, 1).all():
            errors.append("risk_sigma חייב להיות בין 0 ל-1.")

    return errors
