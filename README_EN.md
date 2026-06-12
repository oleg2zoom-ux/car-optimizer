# Car Purchase Optimization Calculator

A Hebrew Streamlit app for comparing car purchase options using total cost of ownership: purchase price, depreciation, expected resale value, financing, monthly payment limits, cash contribution and running costs.

## Project structure

- `app.py` — Streamlit user interface.
- `car_optimizer/` — finance, valuation, data loading and optimization logic.
- `data/sample_cars.csv` — demo dataset.
- `data/market_samples_template.csv` — template for real market observations.
- `docs/DATA_SCHEMA.md` — data schema documentation.
- `docs/STREAMLIT_DEPLOY.md` — deployment guide.
- `scripts/validate_data.py` — validates CSV/Excel data files.
- `requirements.txt` — Python dependencies.

## Local run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Community Cloud

Create a GitHub repository, upload the project files, then create a new Streamlit app with:

```text
Main file path: app.py
```

## Data note

The included data is for demo only. Replace it with real market observations before making real purchasing decisions.
