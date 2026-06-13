# Data schema

The app reads `data/replacement_options.csv` by default.

Required columns:
- record_id
- manufacturer
- model
- trim
- model_year
- vehicle_age_years
- category
- powertrain
- ownership_type
- km
- hand
- purchase_price
- annual_depr_rate
- risk_sigma
- warranty_years
- parts_support_years
- reliability_risk_factor
- source_type
- source_confidence

Recommended columns:
- importer
- brand
- new_price_reference_ils
- license_fee_ils
- source_url
- needs_review
- notes
- observation_date
