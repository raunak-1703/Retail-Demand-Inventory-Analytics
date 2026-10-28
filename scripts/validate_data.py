"""Independent checks on saved CSVs and original source values. Fails nonzero."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P = ROOT/'data/processed'
SCHEMAS = {
 'retail_sales':'Date Store_ID Product_ID Category Department Units_Sold Unit_Price Sales_Revenue Month Week Day_of_Week',
 'product_summary':'Product_ID Category Department Total_Units_Sold Total_Revenue Observed_Days Average_Daily_Units_Sold Movement_Class ABC_Class',
 'store_summary':'Store_ID Total_Units_Sold Total_Revenue Observed_Days Average_Daily_Units_Sold',
 'monthly_sales':'Month Store_ID Total_Units_Sold Total_Revenue Observed_Days Average_Daily_Units_Sold',
 'abc_analysis':'Product_ID Category Total_Units_Sold Total_Revenue Revenue_Contribution_Percent Cumulative_Revenue_Percent ABC_Class',
 'inventory_planning':'Store_ID Product_ID Average_Daily_Demand Demand_Standard_Deviation Assumed_Lead_Time_Days Target_Service_Level Safety_Stock Reorder_Point Movement_Class ABC_Class',
 'dim_date':'Date Month Week Day_of_Week', 'dim_store':'Store_ID State',
}
SCHEMAS['lead_time_sensitivity'] = SCHEMAS['inventory_planning']
SCHEMAS['top_10_fast_moving'] = SCHEMAS['top_10_slow_moving'] = SCHEMAS['product_summary']
SCHEMAS['dim_product'] = SCHEMAS['product_summary']+' Revenue_Contribution_Percent Cumulative_Revenue_Percent'

def main():
    results=[]
    def check(name, condition):
        results.append((name,bool(condition)))
    frames = {name:pd.read_csv(P/f'{name}.csv') for name in SCHEMAS}
    for name, columns in SCHEMAS.items():
        frame = frames[name]
        check(f'{name}: expected columns',list(frame.columns)==columns.split())
        check(f'{name}: no missing values',not frame.isna().any().any())
    d,p,s,a,i = (frames[n] for n in ['retail_sales','product_summary','store_summary','abc_analysis','inventory_planning'])
    check('No duplicate product-store-date keys',not d.duplicated(['Product_ID','Store_ID','Date']).any())
    check('Exactly 50 products, 2 stores, 365 complete days',len(d)==36500 and d.Product_ID.nunique()==50 and set(d.Store_ID)=={'CA_1','CA_2'} and d.groupby(['Store_ID','Product_ID']).Date.nunique().eq(365).all())
    check('Nonnegative integer sales',((d.Units_Sold>=0)&(d.Units_Sold==np.floor(d.Units_Sold))).all())
    check('Nonnegative finite prices',((d.Unit_Price>=0)&np.isfinite(d.Unit_Price)).all())
    check('Revenue equals quantity times price',np.allclose(d.Sales_Revenue,d.Units_Sold*d.Unit_Price,atol=1e-8))
    for key,frame in [('Product_ID',p),('Store_ID',s)]:
        actual=d.groupby(key)[['Units_Sold','Sales_Revenue']].sum().sort_index()
        expected=frame.set_index(key)[['Total_Units_Sold','Total_Revenue']].sort_index()
        check(f'{key}: detail reconciles to summary',actual.index.equals(expected.index) and np.allclose(actual,expected))
    m=frames['monthly_sales'].set_index(['Month','Store_ID']).sort_index()
    check('Monthly totals reconcile',np.allclose(m[['Total_Units_Sold','Total_Revenue']],d.groupby(['Month','Store_ID'])[['Units_Sold','Sales_Revenue']].sum().sort_index()))
    check('ABC contribution sums to 100%',np.isclose(a.Revenue_Contribution_Percent.sum(),100))
    check('ABC classes valid and complete',len(a)==50 and a.Product_ID.is_unique and a.ABC_Class.isin(['A','B','C']).all())
    ordered=a.sort_values(['Total_Revenue','Product_ID'],ascending=[False,True])
    contribution=ordered.Total_Revenue/ordered.Total_Revenue.sum()*100
    prior=contribution.cumsum()-contribution
    check('ABC threshold crossing rule',np.array_equal(ordered.ABC_Class,np.select([prior<80,prior<95],['A','B'],default='C')))
    check('ABC contributions recomputed',np.allclose(contribution,ordered.Revenue_Contribution_Percent) and np.allclose(contribution.cumsum(),ordered.Cumulative_Revenue_Percent))
    mean=p.Total_Units_Sold/365
    q25,q75=mean.quantile([.25,.75])
    check('Movement quartiles and daily means',np.allclose(mean,p.Average_Daily_Units_Sold) and np.array_equal(p.Movement_Class,np.select([mean<=q25,mean>=q75],['Slow Moving','Fast Moving'],default='Medium Moving')))
    for name,ascending in [('top_10_fast_moving',False),('top_10_slow_moving',True)]:
        check(name+' ranking',frames[name].Product_ID.tolist()==p.sort_values(['Average_Daily_Units_Sold','Product_ID'],ascending=[ascending,True]).head(10).Product_ID.tolist())
    stats=d.groupby(['Store_ID','Product_ID']).Units_Sold.agg(['mean','std'])
    for name in ['inventory_planning','lead_time_sensitivity']:
        inv=frames[name].merge(stats,left_on=['Store_ID','Product_ID'],right_index=True,validate='many_to_one')
        raw=1.645*inv['std']*np.sqrt(inv.Assumed_Lead_Time_Days)
        check(name+': demand statistics',np.allclose(inv.Average_Daily_Demand,inv['mean']) and np.allclose(inv.Demand_Standard_Deviation,inv['std']))
        check(name+': safety stock formula',np.array_equal(inv.Safety_Stock,np.ceil(raw)))
        check(name+': reorder point formula',np.array_equal(inv.Reorder_Point,np.ceil(inv['mean']*inv.Assumed_Lead_Time_Days+raw)))
        check(name+': nonnegative recommendations',(inv[['Safety_Stock','Reorder_Point']]>=0).all().all())
        check(name+': assumptions',(inv.Target_Service_Level==.95).all())
    check('Base lead time seven days',len(i)==100 and (i.Assumed_Lead_Time_Days==7).all())
    sens=frames['lead_time_sensitivity']
    pivot=sens.pivot(index=['Store_ID','Product_ID'],columns='Assumed_Lead_Time_Days',values='Reorder_Point')
    check('5/7/10 day sensitivity monotonic',len(sens)==300 and set(pivot.columns)=={5,7,10} and (pivot[5]<=pivot[7]).all() and (pivot[7]<=pivot[10]).all())
    for name in ['product_summary','abc_analysis','inventory_planning','dim_product']:
        check(name+': product identifiers',set(frames[name].Product_ID)==set(d.Product_ID))
    check('Dimension keys unique',frames['dim_date'].Date.is_unique and frames['dim_product'].Product_ID.is_unique and frames['dim_store'].Store_ID.is_unique)
    # Compare every exported quantity and price back to the original files.
    cal=pd.read_csv(ROOT/'data/raw/calendar.csv')[['d','date','wm_yr_wk']]
    window=cal[cal.date.isin(d.Date)]
    src=pd.read_csv(ROOT/'data/raw/sales_train_validation.csv',usecols=['item_id','store_id']+window.d.tolist())
    src=src[src.item_id.isin(d.Product_ID)&src.store_id.isin(d.Store_ID)]
    src=src.melt(id_vars=['item_id','store_id'],var_name='d',value_name='source_units').merge(window,on='d',validate='many_to_one')
    joined=d.merge(src,left_on=['Product_ID','Store_ID','Date'],right_on=['item_id','store_id','date'],validate='one_to_one')
    check('All quantities and Walmart weeks match original',len(joined)==len(d) and (joined.Units_Sold==joined.source_units).all() and (joined.Week==joined.wm_yr_wk).all())
    prices=pd.concat([x[x.item_id.isin(d.Product_ID)&x.store_id.isin(d.Store_ID)] for x in pd.read_csv(ROOT/'data/raw/sell_prices.csv',chunksize=500000)])
    j=d.merge(prices,left_on=['Product_ID','Store_ID','Week'],right_on=['item_id','store_id','wm_yr_wk'],validate='many_to_one')
    check('All prices match original',len(j)==len(d) and np.allclose(j.Unit_Price,j.sell_price))
    check('Dates continuous',pd.to_datetime(d.Date).nunique()==365 and (pd.to_datetime(d.Date).max()-pd.to_datetime(d.Date).min()).days==364)
    report=ROOT/'reports/data_validation_report.md'
    report.parent.mkdir(exist_ok=True)
    passed=sum(ok for _,ok in results)
    report.write_text('# Data validation report\n\n'+f'{passed}/{len(results)} checks passed on saved CSV outputs. Source quantities and prices independently reconciled.\n\n'+ '\n'.join(f'- {"PASS" if ok else "FAIL"}: {name}' for name,ok in results)+'\n\nPower BI and Excel checks are reported separately in quality_check.md.\n',encoding='utf-8')
    print(f'{passed}/{len(results)} checks passed')
    if passed!=len(results):
        raise AssertionError([name for name,ok in results if not ok])

if __name__=='__main__':
    main()
