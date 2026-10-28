"""Reproducible historical demand analysis; no inventory balances are inferred."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/processed'
STORES = ['CA_1', 'CA_2']

def export(frame, name):
    frame.to_csv(OUT / f'{name}.csv', index=False, float_format='%.10f')

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    raw = ROOT / 'data/raw'
    header = pd.read_csv(raw / 'sales_train_validation.csv', nrows=0).columns
    days = sorted([c for c in header if c.startswith('d_')], key=lambda x: int(x[2:]))[-365:]
    ids = ['item_id', 'dept_id', 'cat_id', 'store_id']
    sales = pd.read_csv(raw / 'sales_train_validation.csv', usecols=ids + days)
    source_rows = len(sales)
    sales = sales[sales.store_id.isin(STORES)].copy()
    assert not sales.duplicated(['store_id', 'item_id']).any()
    calendar = pd.read_csv(raw / 'calendar.csv')
    cal = calendar[calendar.d.isin(days)][['d', 'date', 'wm_yr_wk', 'weekday']].copy()
    assert len(cal) == 365 and cal.d.is_unique and cal.date.is_unique
    weeks = cal.wm_yr_wk.unique()
    prices = pd.concat([part[part.store_id.isin(STORES) & part.wm_yr_wk.isin(weeks)]
        for part in pd.read_csv(raw / 'sell_prices.csv', chunksize=500000)], ignore_index=True)
    assert not prices.duplicated(['store_id', 'item_id', 'wm_yr_wk']).any()
    valid_prices = prices[prices.sell_price.notna() & np.isfinite(prices.sell_price) & (prices.sell_price >= 0)]
    coverage = valid_prices.groupby(['store_id', 'item_id']).wm_yr_wk.nunique()
    complete = set(coverage[coverage == len(weeks)].index)
    eligible = []
    for product, group in sales.groupby('item_id'):
        if set(group.store_id) == set(STORES) and all((s, product) in complete for s in STORES):
            values = group[days].to_numpy()
            if np.isfinite(values).all() and (values >= 0).all() and (values == np.floor(values)).all() and (values.sum(axis=1) > 0).all():
                eligible.append(product)
    # Hash ordering spreads selection over IDs/categories without choosing by revenue.
    selected = sorted(eligible, key=lambda x: (hashlib.sha256(x.encode()).hexdigest(), x))[:50]
    assert len(selected) == 50, 'Fewer than 50 fully priced eligible products'
    selected_sales = sales[sales.item_id.isin(selected)]
    daily = selected_sales.melt(id_vars=ids, value_vars=days, var_name='d', value_name='Units_Sold')
    daily = daily.merge(cal, on='d', how='left', validate='many_to_one')
    daily = daily.merge(prices, on=['store_id', 'item_id', 'wm_yr_wk'], how='left', validate='many_to_one')
    assert daily.sell_price.notna().all(), 'Missing prices: do not impute'
    daily = daily.rename(columns={'date':'Date', 'store_id':'Store_ID', 'item_id':'Product_ID',
        'cat_id':'Category', 'dept_id':'Department', 'sell_price':'Unit_Price', 'wm_yr_wk':'Week', 'weekday':'Day_of_Week'})
    daily['Date'] = pd.to_datetime(daily.Date)
    daily['Units_Sold'] = daily.Units_Sold.astype('int64')
    daily['Sales_Revenue'] = daily.Units_Sold * daily.Unit_Price
    daily['Month'] = daily.Date.dt.strftime('%Y-%m')
    daily = daily[['Date','Store_ID','Product_ID','Category','Department','Units_Sold','Unit_Price','Sales_Revenue','Month','Week','Day_of_Week']].sort_values(['Date','Store_ID','Product_ID'])
    product = daily.groupby(['Product_ID','Category','Department'], as_index=False).agg(Total_Units_Sold=('Units_Sold','sum'),Total_Revenue=('Sales_Revenue','sum'),Observed_Days=('Date','nunique'))
    product['Average_Daily_Units_Sold'] = product.Total_Units_Sold / product.Observed_Days
    # Empirical quartiles; ties at a threshold stay together.
    q25, q75 = product.Average_Daily_Units_Sold.quantile([.25,.75])
    product['Movement_Class'] = np.select([product.Average_Daily_Units_Sold <= q25, product.Average_Daily_Units_Sold >= q75], ['Slow Moving','Fast Moving'], default='Medium Moving')
    abc = product[['Product_ID','Category','Total_Units_Sold','Total_Revenue']].sort_values(['Total_Revenue','Product_ID'], ascending=[False,True]).copy()
    abc['Revenue_Contribution_Percent'] = abc.Total_Revenue / abc.Total_Revenue.sum() * 100
    abc['Cumulative_Revenue_Percent'] = abc.Revenue_Contribution_Percent.cumsum()
    prior = abc.Cumulative_Revenue_Percent - abc.Revenue_Contribution_Percent
    abc['ABC_Class'] = np.select([prior < 80, prior < 95], ['A','B'], default='C')
    product = product.merge(abc[['Product_ID','ABC_Class']], on='Product_ID', validate='one_to_one')
    store = daily.groupby('Store_ID', as_index=False).agg(Total_Units_Sold=('Units_Sold','sum'),Total_Revenue=('Sales_Revenue','sum'),Observed_Days=('Date','nunique'))
    store['Average_Daily_Units_Sold'] = store.Total_Units_Sold/store.Observed_Days
    monthly = daily.groupby(['Month','Store_ID'], as_index=False).agg(Total_Units_Sold=('Units_Sold','sum'),Total_Revenue=('Sales_Revenue','sum'),Observed_Days=('Date','nunique'))
    monthly['Average_Daily_Units_Sold'] = monthly.Total_Units_Sold/monthly.Observed_Days
    base = daily.groupby(['Store_ID','Product_ID'], as_index=False).agg(Average_Daily_Demand=('Units_Sold','mean'),Demand_Standard_Deviation=('Units_Sold','std'))
    base = base.merge(product[['Product_ID','Movement_Class','ABC_Class']], on='Product_ID', validate='many_to_one')
    scenarios = []
    for lead in [5,7,10]:
        inv = base.copy()
        inv['Assumed_Lead_Time_Days'] = lead
        inv['Target_Service_Level'] = .95
        ss = 1.645 * inv.Demand_Standard_Deviation * np.sqrt(lead)
        inv['Safety_Stock'] = np.ceil(ss).astype(int)
        inv['Reorder_Point'] = np.ceil(inv.Average_Daily_Demand * lead + ss).astype(int)
        inv = inv[['Store_ID','Product_ID','Average_Daily_Demand','Demand_Standard_Deviation','Assumed_Lead_Time_Days','Target_Service_Level','Safety_Stock','Reorder_Point','Movement_Class','ABC_Class']]
        scenarios.append(inv)
    sensitivity = pd.concat(scenarios, ignore_index=True)
    inventory = sensitivity[sensitivity.Assumed_Lead_Time_Days == 7]
    for name, frame in [('retail_sales',daily),('product_summary',product),('store_summary',store),('monthly_sales',monthly),('abc_analysis',abc),('inventory_planning',inventory),('lead_time_sensitivity',sensitivity),('top_10_fast_moving',product.sort_values(['Average_Daily_Units_Sold','Product_ID'], ascending=[False,True]).head(10)),('top_10_slow_moving',product.sort_values(['Average_Daily_Units_Sold','Product_ID']).head(10))]:
        export(frame,name)
    export(daily[['Date','Month','Week','Day_of_Week']].drop_duplicates().sort_values('Date'), 'dim_date')
    export(product.merge(abc[['Product_ID','Revenue_Contribution_Percent','Cumulative_Revenue_Percent']],on='Product_ID'), 'dim_product')
    export(pd.DataFrame({'Store_ID':STORES,'State':['CA','CA']}), 'dim_store')
    metadata = dict(source_sales_rows=source_rows, start=str(daily.Date.min().date()), end=str(daily.Date.max().date()), days=365,
        records=len(daily), products=50, stores=STORES, eligible_products=len(eligible), selected_products=selected,
        missing_prices_selected=int(daily.Unit_Price.isna().sum()), movement_q25=float(q25),movement_q75=float(q75),
        revenue=float(daily.Sales_Revenue.sum()), units=int(daily.Units_Sold.sum()))
    (OUT/'run_metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in metadata.items() if k!='selected_products'},indent=2))

if __name__ == '__main__':
    main()
