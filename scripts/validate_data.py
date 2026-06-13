import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from car_optimizer.data_loader import validate_replacement_columns, normalize_dataframe


def main(path: str) -> int:
    file_path = Path(path)
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return 1

    if file_path.suffix.lower() in [".xlsx", ".xls"]:
        xls = pd.ExcelFile(file_path)
        sheet_name = "App_Replacement_Options" if "App_Replacement_Options" in xls.sheet_names else xls.sheet_names[0]
        df = pd.read_excel(file_path, sheet_name=sheet_name)
    else:
        df = pd.read_csv(file_path)

    df = normalize_dataframe(df)
    errors = validate_replacement_columns(df)

    if errors:
        print("Validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print(f"OK: {file_path} has {len(df)} rows and valid schema.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/validate_data.py data/replacement_options.csv")
        raise SystemExit(1)

    raise SystemExit(main(sys.argv[1]))
