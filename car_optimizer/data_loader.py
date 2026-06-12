from pathlib import Path
import pandas as pd
from car_optimizer.constants import CURRENT_YEAR
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "sample_cars.csv"
REQUIRED_COLUMNS = ["record_id","manufacturer","model","trim","model_year","category","powertrain","ownership_type","km","hand","purchase_price","annual_depr_rate","risk_sigma","source_type","source_confidence"]
NUMERIC_COLUMNS = ["model_year","vehicle_age_years","km","hand","msrp_new","asking_price","deal_price_est","trade_in_price_est","purchase_price","annual_depr_rate","risk_sigma","source_confidence"]
def load_market_data(uploaded_file=None):
    if uploaded_file is None:
        df=pd.read_csv(DATA_PATH)
    else:
        name=uploaded_file.name.lower()
        df=pd.read_excel(uploaded_file) if name.endswith((".xlsx",".xls")) else pd.read_csv(uploaded_file)
    return normalize_dataframe(df)
def normalize_dataframe(df):
    df=df.copy(); df.columns=[str(c).strip() for c in df.columns]
    for col in NUMERIC_COLUMNS:
        if col in df.columns: df[col]=pd.to_numeric(df[col], errors='coerce')
    if 'vehicle_age_years' not in df.columns and 'model_year' in df.columns:
        df['vehicle_age_years']=CURRENT_YEAR-df['model_year']
    if 'trim' in df.columns: df['trim']=df['trim'].fillna('')
    if 'source_confidence' in df.columns: df['source_confidence']=df['source_confidence'].fillna(0.3)
    return df
def validate_columns(df):
    errors=[]; missing=[c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing: errors.append('חסרות עמודות חובה: '+', '.join(missing))
    if 'purchase_price' in df.columns and df['purchase_price'].isna().any(): errors.append('יש שורות ללא purchase_price תקין.')
    if 'annual_depr_rate' in df.columns:
        valid=df['annual_depr_rate'].dropna()
        if not valid.between(0,1).all(): errors.append('annual_depr_rate חייב להיות בין 0 ל-1.')
    if 'risk_sigma' in df.columns:
        valid=df['risk_sigma'].dropna()
        if not valid.between(0,1).all(): errors.append('risk_sigma חייב להיות בין 0 ל-1.')
    return errors
