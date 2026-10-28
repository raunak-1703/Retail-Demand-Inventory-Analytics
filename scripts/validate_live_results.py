"""Compare exported live DAX query results with independent Python controls."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'data/processed'
def main():
    r=json.loads((ROOT/'reports/powerbi_live_results.json').read_text(encoding='utf-8-sig'))
    d=pd.read_csv(P/'retail_sales.csv'); p=pd.read_csv(P/'product_summary.csv'); i=pd.read_csv(P/'inventory_planning.csv'); a=pd.read_csv(P/'abc_analysis.csv')
    expected={'Revenue':d.Sales_Revenue.sum(),'Units':d.Units_Sold.sum(),'Products':50,'Stores':2,'DailyUnits':d.Units_Sold.sum()/365,'ARevenue':a.loc[a.ABC_Class=='A','Total_Revenue'].sum(),'ACount':26,'BCount':14,'CCount':10,'Safety':i.Safety_Stock.mean(),'ROP':i.Reorder_Point.mean(),'Demand':i.Average_Daily_Demand.mean(),'Fast':(p.Movement_Class=='Fast Moving').sum()}
    checks=[]
    for k,v in expected.items():
        assert np.isclose(r['summary']['['+k+']'],v),k
        checks.append('KPI '+k)
    for section,dim,key in [('stores','DimStore[Store_ID]','Store_ID'),('months','DimDate[Month]','Month'),('products','DimProduct[Product_ID]','Product_ID')]:
        actual=pd.DataFrame(r[section]).set_index(dim).sort_index()
        control=d.groupby(key).Sales_Revenue.sum().sort_index()
        assert actual.index.tolist()==control.index.tolist() and np.allclose(actual['[Revenue]'],control)
        checks.append(section+' filter context')
    products=pd.DataFrame(r['products'])
    assert np.isclose(products['[Share]'].sum(),1)
    for key in ['TopRevenue','Fast','Slow']: assert products['['+key+']'].notna().sum()==10
    checks.append('Revenue share and all three top/bottom-ten measures')
    scen=pd.DataFrame(r['scenario']).set_index('Sensitivity[Assumed_Lead_Time_Days]').sort_index()
    ref=pd.read_csv(P/'lead_time_sensitivity.csv').groupby('Assumed_Lead_Time_Days')[['Reorder_Point','Safety_Stock']].mean().sort_index()
    assert np.allclose(scen[['[ROP]','[Safety]']],ref)
    checks.append('All three lead-time scenarios')
    assert r['counts']=={'[Sales]':36500,'[Date]':365,'[Product]':50,'[Store]':2,'[Inventory]':100,'[Sensitivity]':300}
    checks.append('All six table row counts')
    model=json.loads((ROOT/'powerbi/Retail_Demand_Inventory_Analytics.SemanticModel/model.bim').read_text(encoding='utf-8-sig'))
    intended={x['name'] for x in model['model']['relationships']}
    live={x['Name']:x for x in r['relationships']}
    assert intended.issubset(live) and all(live[n]['IsActive'] and live[n]['CrossFilteringBehavior']==1 for n in intended)
    checks.append('All seven declared single-direction relationships active (Desktop may add an auxiliary auto-date relationship)')
    text='# Power BI live DAX validation\n\n'+f'{len(checks)}/{len(checks)} checks passed against the running Desktop model.\n\n'+'\n'.join('- PASS: '+x for x in checks)+'\n\nUI rendering and slicer interaction checks are recorded in quality_check.md.\n'
    (ROOT/'reports/powerbi_validation.md').write_text(text,encoding='utf-8')
    print(f'{len(checks)}/{len(checks)} live model checks passed')
if __name__=='__main__': main()
