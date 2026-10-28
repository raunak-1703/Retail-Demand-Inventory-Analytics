# Generated outputs (local only)

Run `python scripts/prepare_data.py`, then `python scripts/validate_data.py`.
Daily fact: `retail_sales.csv` (product-store-date grain).
Dimensions: `dim_date.csv`, `dim_product.csv`, `dim_store.csv`.
Planning facts: `inventory_planning.csv` (product-store),
`lead_time_sensitivity.csv` (product-store-assumed lead time).
Product/store/monthly summaries, ABC results and top/bottom-ten files support Excel
and documentation. Never join aggregated summary revenue back into daily sales.

All generated row-level CSVs and the populated Excel/PBIX files stay local by default
because they contain source-derived data. Rebuild them after cloning. Aggregate
findings, report definitions and captured dashboard screenshots support review.
