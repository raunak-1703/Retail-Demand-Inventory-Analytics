"""Write business findings exclusively from the validated outputs."""
from pathlib import Path
import pandas as pd
import json
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'data/processed'
def main():
    d=pd.read_csv(P/'retail_sales.csv'); p=pd.read_csv(P/'product_summary.csv'); a=pd.read_csv(P/'abc_analysis.csv'); s=pd.read_csv(P/'store_summary.csv'); i=pd.read_csv(P/'inventory_planning.csv'); sens=pd.read_csv(P/'lead_time_sensitivity.csv')
    m=d.groupby('Month').agg(Units=('Units_Sold','sum'),Revenue=('Sales_Revenue','sum'),Days=('Date','nunique'))
    m['Units_per_day']=m.Units/m.Days
    aclass=a[a.ABC_Class=='A']; top=s.sort_values('Total_Revenue',ascending=False).iloc[0]
    fast=p.sort_values(['Average_Daily_Units_Sold','Product_ID'],ascending=[False,True]).head(10)
    slow=p.sort_values(['Average_Daily_Units_Sold','Product_ID']).head(10)
    def table(frame):
        return '| '+' | '.join(frame.columns)+' |\n| '+' | '.join(['---']*len(frame.columns))+' |\n'+'\n'.join('| '+' | '.join(f'{v:,.2f}' if isinstance(v,float) else str(v) for v in row)+' |' for row in frame.itertuples(index=False,name=None))
    peak=m.Units_per_day.idxmax(); low=m.Units_per_day.idxmin()
    text=f'''# Business insights

These findings describe only 50 selected products in CA_1 and CA_2, from {d.Date.min()} to {d.Date.max()}. They are not estimates for Walmart as a whole.

## Revenue and store performance

- Calculated sales revenue: **${d.Sales_Revenue.sum():,.2f}** from **{d.Units_Sold.sum():,} units**.
- Average observed sales across both stores: **{d.Units_Sold.sum()/365:,.2f} units/day**.
- Highest-revenue store: **{top.Store_ID}**, with **${top.Total_Revenue:,.2f}** ({top.Total_Revenue/d.Sales_Revenue.sum()*100:.2f}% of selected revenue).
- Highest-revenue product: **{a.iloc[0].Product_ID}**, with **${a.iloc[0].Total_Revenue:,.2f}**.

{table(s)}

## ABC priorities

**{len(aclass)} A-class products contribute ${aclass.Total_Revenue.sum():,.2f}, or {aclass.Revenue_Contribution_Percent.sum():.2f}% of revenue.** Class counts are {a.ABC_Class.value_counts().sort_index().to_dict()}.
Use A-class products for tighter review of replenishment parameters and more frequent cycle-count planning once real stock records are available. Revenue priority is not the same as unit velocity or profit margin.

## Fastest-moving products

Average daily sales here are product totals across BOTH stores divided by 365 days. The model's product-store daily averages are separate.

{table(fast[['Product_ID','Average_Daily_Units_Sold','Movement_Class','ABC_Class']])}

## Slowest-moving products

{table(slow[['Product_ID','Average_Daily_Units_Sold','Movement_Class','ABC_Class']])}

Slow observed sales suggest reviewing order sizes and assortment before allocating more space. They do not establish excess inventory or obsolete stock.

## Monthly demand

{table(m.reset_index())}

The highest observed daily rate is **{peak}: {m.loc[peak,'Units_per_day']:.2f} units/day**; the lowest is **{low}: {m.loc[low,'Units_per_day']:.2f}**.
April 2015 and April 2016 are partial months. Compare units per observed day, not their unadjusted totals. One year and a small selected basket do not prove recurring seasonality or its causes.

## Demand variability and safety stock

Highest sample standard deviations (units/day):

{table(i.sort_values('Demand_Standard_Deviation',ascending=False).head(5)[['Store_ID','Product_ID','Average_Daily_Demand','Demand_Standard_Deviation','Safety_Stock','Reorder_Point']])}

Products in this table have the highest estimated safety stock because the base model uses a common lead time and service factor. Review unusual demand spikes and promotional history before accepting these thresholds.

## Lead-time sensitivity

{table(sens.groupby('Assumed_Lead_Time_Days',as_index=False)[['Safety_Stock','Reorder_Point']].mean())}

Figures above are averages over 100 product-store combinations. Mean lead-time demand grows linearly with lead time; the safety allowance grows with its square root. Reducing replenishment delays can lower the estimated reorder threshold, but actual lead times must be measured first.

## Practical recommendations and limits

1. Prioritize high-revenue A items for service monitoring; combine ABC and movement classes rather than treating all high-unit items as high-value items.
2. Use product-store thresholds because the stores have different demand distributions. Compare the 5/7/10-day assumptions with measured supplier delivery times before implementation.
3. Review slow items' order quantities and pack sizes. No warehouse capacity, stock on hand, order quantity, carrying cost or margin is supplied here.
4. Collect current inventory position (on hand + on order - backorders) before deciding whether to reorder. This project deliberately generates no actual reorder alerts.
5. Daily sales are observed demand proxies: zero sales could reflect zero demand, availability, or other causes. The data cannot identify actual stockouts or lost sales.
6. The normal approximation, independent daily demand and constant lead time are simplifying assumptions. A 95% target is not a measured fill rate or proven achieved service level. For intermittent demand, validate this model before use.
'''
    (ROOT/'reports').mkdir(exist_ok=True)
    (ROOT/'reports/business_insights.md').write_text(text,encoding='utf-8')
    print(f'Insights written: A contribution {aclass.Revenue_Contribution_Percent.sum():.2f}%; {len(aclass)} A products; peak {peak}')
if __name__=='__main__': main()
