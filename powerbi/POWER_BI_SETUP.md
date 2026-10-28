# Power BI setup and report guide

## Open the generated project

1. Run the pipeline from the repository root. Use current Power BI Desktop.
2. Open `Retail_Demand_Inventory_Analytics.pbip`. It points to the adjacent `.Report`
   and `.SemanticModel` folders; keep them together.
3. Select Home > Refresh. Project definitions are text; Git does not contain the
   local data cache. If prompted about a missing source, edit Transform data > Manage
   parameters > DataFolder to the absolute `data/processed/` folder with trailing slash.
4. Import `theme.json` from Design > Import theme if rebuilding from the generator.
5. Check all three pages and compare the overview with $108,821.09, 36,956 units,
   50 products, 2 stores and 101.249315 daily units.
6. File > Save saves the project. File > Save As > Power BI report (.pbix), if offered
   by your installed Desktop, produces a native packaged report with loaded data.

## Semantic model

| Table | Source | Grain / key |
| --- | --- | --- |
| Sales | retail_sales.csv | Product_ID + Store_ID + Date |
| DimDate | dim_date.csv | Date (unique) |
| DimProduct | dim_product.csv | Product_ID (unique) |
| DimStore | dim_store.csv | Store_ID (unique) |
| Inventory | inventory_planning.csv | Product_ID + Store_ID |
| Sensitivity | lead_time_sensitivity.csv | Product_ID + Store_ID + Assumed_Lead_Time_Days |

Connect DimProduct and DimStore one-to-many to Sales, Inventory and Sensitivity.
Connect DimDate one-to-many only to Sales. Use single-direction filtering from
dimensions to facts. Do not connect facts to one another. No relationships from
product/store/monthly summary CSVs are needed. Desktop can generate an auxiliary
auto-date table; explicit visuals use DimDate[Date], never its auto hierarchy.

All fields use explicit types in `model.bim` and `Power_Query.m`. Date is a date,
IDs remain text, units are whole numbers, prices/revenue/demand statistics are
decimal numbers. Week is the original Walmart `wm_yr_wk`, not ISO week number.

## DAX and filter behavior

`DAX_measures.dax` contains all measures, including the required 12 KPIs. Measures
reside on Sales but can aggregate Inventory or Sensitivity. Revenue and units always
aggregate Sales only. Average Daily Units Sold divides selected sales by the number
of selected calendar dates, including zero-sales days.

ABC and movement labels are fixed attributes on DimProduct calculated across both
stores over the full 365 days. A/B/C counts intersect the active filters using
KEEPFILTERS. The Pareto uses full-period baseline product revenue and cumulative
share; filtering does not re-rank or rebase that historical classification.

Revenue Contribution % removes the current product row using ALLSELECTED while
preserving selected category, store and date filters. In a product table the shares
sum to 100% over the selected product set. Top/bottom ten measures use TOPN with
product ID as the secondary sort, keeping exactly ten products when at least ten
are visible. Inventory statistics are fixed full-period estimates; no date slicer
appears on the planning page. Mean product charts average over selected stores.

## Build manually if your Desktop cannot open PBIP

1. Home > Transform data > New source > Blank query. Create DataFolder as a text parameter.
2. Create six queries with the names in the table above. Paste each matching `let ... in`
   block from `Power_Query.m` into Advanced Editor. Close & Apply.
3. Model view: add the seven relationships described above. Set one-to-many,
   single-direction, active. Disable automatic relationships if they create extras.
4. Add each measure from `DAX_measures.dax` using Modeling > New measure. Set USD
   currency formats for revenue, percentage for shares, and whole-number counts.
5. Create the three pages below. Import `theme.json`. Use Segoe UI, navy titles,
   white panels on #F8FAFC, blue main series, green/orange/red category accents.
6. Add dimension fields to slicers. Use Edit interactions to keep filters active.
   Date filtering applies to sales visuals; planning uses the fixed baseline.

## Layout and field mapping

The generated canvas is 1440 x 1000. Header at top, three slicers below, KPI cards,
then chart panels with 20-pixel outer margins. `report_layout.json` lists exact
visual types and role-to-field mappings; the PBIR files hold exact coordinates.

### Executive Overview

Cards: Total Sales Revenue, Total Units Sold, Total Products, Total Stores, Average
Daily Units Sold. Line: DimDate[Month] / Total Sales Revenue. Store bar:
DimStore[Store_ID] / Total Sales Revenue. Donut: DimProduct[Category] / Total Sales
Revenue. Product bar: DimProduct[Product_ID] / Top 10 Revenue, descending. Daily
line: DimDate[Date] / Total Units Sold, ascending. Date/store/category slicers.

### ABC & Product Analysis

Cards: A-Class Product Count, B-Class Product Count, C-Class Product Count, A-Class
Revenue. Donut: ABC_Class / Total Products. Pareto combo: Product_ID, Baseline Product
Revenue as columns and Baseline Cumulative Revenue % as the secondary line; sort
by baseline revenue descending. Fast/slow bars: Product_ID / Top 10 Daily Units or
Bottom 10 Daily Units. Table: Product_ID, Total Sales Revenue, Total Units Sold,
ABC_Class and Movement_Class. Store/category/ABC slicers.

### Inventory Planning

Cards: Average Daily Demand, Average Safety Stock, Average Reorder Point,
Fast-Moving Product Count. Three product bars: average reorder point, average safety
stock and Demand Variability. Sensitivity line: Assumed_Lead_Time_Days / Scenario
Reorder Point. Table: product, store, Average Daily Demand, Assumed Lead Time,
Average Safety Stock, Average Reorder Point, ABC_Class and Movement_Class.
Store/category/product slicers. All stock recommendations are estimates.

## Verification

`reports/powerbi_validation.md` records live DAX reconciliation. `quality_check.md`
records visual verification and native save status. Use the supplied scripts to
repeat checks after changes. A schema check alone is not proof of correct visuals.

Microsoft format references:
- https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview
- https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report
- https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset
