import sys
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from car_optimizer.data_loader import normalize_dataframe, validate_columns
def main(path):
    p=Path(path)
    if not p.exists(): print(f'File not found: {p}'); return 1
    df=pd.read_excel(p) if p.suffix.lower() in ['.xlsx','.xls'] else pd.read_csv(p)
    df=normalize_dataframe(df); errors=validate_columns(df)
    if errors:
        print('Validation failed:')
        for e in errors: print('- '+e)
        return 1
    print(f'OK: {p} has {len(df)} rows and valid schema.'); return 0
if __name__=='__main__':
    if len(sys.argv)!=2:
        print('Usage: python scripts/validate_data.py data/sample_cars.csv'); raise SystemExit(1)
    raise SystemExit(main(sys.argv[1]))
