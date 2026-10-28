"""Generate documented PBIP/PBIR and a TMSL semantic model from CSV outputs."""
from pathlib import Path
import json
import uuid
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'data/processed'
B=ROOT/'powerbi'
NAME='Retail_Demand_Inventory_Analytics'
SCHEMA='https://developer.microsoft.com/json-schemas/fabric/item/report/definition/'
MEASURES={
 'Total Sales Revenue':'SUM(Sales[Sales_Revenue])',
 'Total Units Sold':'SUM(Sales[Units_Sold])',
 'Average Daily Units Sold':'DIVIDE([Total Units Sold], COUNTROWS(VALUES(DimDate[Date])))',
 'Total Products':'DISTINCTCOUNT(Sales[Product_ID])',
 'Total Stores':'DISTINCTCOUNT(Sales[Store_ID])',
 'Revenue Contribution %':'DIVIDE([Total Sales Revenue], CALCULATE([Total Sales Revenue], ALLSELECTED(DimProduct[Product_ID])))',
 'A-Class Revenue':'CALCULATE([Total Sales Revenue], KEEPFILTERS(DimProduct[ABC_Class] = "A"))',
 'A-Class Product Count':'CALCULATE([Total Products], KEEPFILTERS(DimProduct[ABC_Class] = "A"))',
 'B-Class Product Count':'CALCULATE([Total Products], KEEPFILTERS(DimProduct[ABC_Class] = "B"))',
 'C-Class Product Count':'CALCULATE([Total Products], KEEPFILTERS(DimProduct[ABC_Class] = "C"))',
 'Average Safety Stock':'AVERAGE(Inventory[Safety_Stock])',
 'Average Reorder Point':'AVERAGE(Inventory[Reorder_Point])',
 'Average Daily Demand':'AVERAGE(Inventory[Average_Daily_Demand])',
 'Demand Variability':'AVERAGE(Inventory[Demand_Standard_Deviation])',
 'Fast-Moving Product Count':'CALCULATE(DISTINCTCOUNT(Inventory[Product_ID]), KEEPFILTERS(DimProduct[Movement_Class] = "Fast Moving"))',
 'Scenario Reorder Point':'AVERAGE(Sensitivity[Reorder_Point])',
 'Scenario Safety Stock':'AVERAGE(Sensitivity[Safety_Stock])',
 'Assumed Lead Time':'MAX(Inventory[Assumed_Lead_Time_Days])',
 'Baseline Product Revenue':'SUM(DimProduct[Total_Revenue])',
 'Baseline Cumulative Revenue %':'DIVIDE(MAX(DimProduct[Cumulative_Revenue_Percent]),100)',
 'Top 10 Revenue':'VAR p = SELECTEDVALUE(DimProduct[Product_ID]) RETURN IF(CONTAINS(TOPN(10, ALLSELECTED(DimProduct[Product_ID]), [Total Sales Revenue], DESC, DimProduct[Product_ID], ASC), DimProduct[Product_ID], p), [Total Sales Revenue])',
 'Top 10 Daily Units':'VAR p = SELECTEDVALUE(DimProduct[Product_ID]) RETURN IF(CONTAINS(TOPN(10, ALLSELECTED(DimProduct[Product_ID]), [Average Daily Units Sold], DESC, DimProduct[Product_ID], ASC), DimProduct[Product_ID], p), [Average Daily Units Sold])',
 'Bottom 10 Daily Units':'VAR p = SELECTEDVALUE(DimProduct[Product_ID]) RETURN IF(CONTAINS(TOPN(10, ALLSELECTED(DimProduct[Product_ID]), [Average Daily Units Sold], ASC, DimProduct[Product_ID], ASC), DimProduct[Product_ID], p), [Average Daily Units Sold])',
 'Overview Title':'"RETAIL DEMAND & INVENTORY ANALYTICS"',
 'Products Title':'"ABC & PRODUCT ANALYSIS | fixed full-period classes"',
 'Inventory Title':'"INVENTORY PLANNING | estimates: 7-day lead time, 95% service"',
}

def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2),encoding='utf-8')

def lit(v):
    if isinstance(v,bool): v=str(v).lower()
    elif isinstance(v,str): v="'"+v.replace("'","''")+"'"
    else: v=str(v)+'D'
    return {'expr':{'Literal':{'Value':v}}}

def color(v): return {'solid':{'color':lit(v)}}
def field(table,column,measure=False):
    return {('Measure' if measure else 'Column'):{'Expression':{'SourceRef':{'Entity':table}},'Property':column}}
def col(table,name): return (table,name,False)
def ms(name): return ('Sales',name,True)

def main():
    B.mkdir(exist_ok=True)
    mappings={'Sales':'retail_sales','DimDate':'dim_date','DimProduct':'dim_product','DimStore':'dim_store','Inventory':'inventory_planning','Sensitivity':'lead_time_sensitivity'}
    tables=[]; queries=[]
    for name,filename in mappings.items():
        frame=pd.read_csv(P/f'{filename}.csv')
        columns=[]; transforms=[]
        for c in frame.columns:
            dtype='dateTime' if c=='Date' else ('int64' if pd.api.types.is_integer_dtype(frame[c]) else 'double' if pd.api.types.is_float_dtype(frame[c]) else 'string')
            mtype={'dateTime':'type date','int64':'Int64.Type','double':'type number','string':'type text'}[dtype]
            columns.append({'name':c,'dataType':dtype,'sourceColumn':c,'summarizeBy':'none',**({'formatString':'yyyy-MM-dd'} if dtype=='dateTime' else {})})
            transforms.append('{"'+c+'", '+mtype+'}')
        expr=['let',f'    Source = Csv.Document(File.Contents(DataFolder & "{filename}.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
              '    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
              '    Typed = Table.TransformColumnTypes(Headers, {'+', '.join(transforms)+'}, "en-US")','in','    Typed']
        table={'name':name,'columns':columns,'partitions':[{'name':name,'mode':'import','source':{'type':'m','expression':expr}}]}
        if name=='Sales':
            table['measures']=[{'name':n,'expression':e,'formatString':('0.0%' if '%' in n else '$#,##0.00' if 'Revenue' in n and 'Title' not in n else '#,##0.00' if any(x in n for x in ['Average','Demand','Variability','Daily','Scenario']) else '#,##0')} for n,e in MEASURES.items()]
        tables.append(table)
        queries.append('// '+name+'\n'+'\n'.join(expr))
    relationships=[]
    for fact in ['Sales','Inventory','Sensitivity']:
        for dim,key in [('DimProduct','Product_ID'),('DimStore','Store_ID')]+([('DimDate','Date')] if fact=='Sales' else []):
            relationships.append({'name':str(uuid.uuid5(uuid.NAMESPACE_DNS,f'{fact}-{dim}')),'fromTable':fact,'fromColumn':key,'toTable':dim,'toColumn':key,'fromCardinality':'many','toCardinality':'one','crossFilteringBehavior':'oneDirection'})
    model={'name':NAME,'compatibilityLevel':1567,'model':{'culture':'en-US','defaultPowerBIDataSourceVersion':'powerBI_V3','sourceQueryCulture':'en-US',
        'expressions':[{'name':'DataFolder','kind':'m','expression':'"'+str(P.resolve()).replace('\\','/')+'/" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'}],
        'tables':tables,'relationships':relationships}}
    sm=B/(NAME+'.SemanticModel')
    dump(sm/'definition.pbism',{'version':'1.0','settings':{}})
    dump(sm/'model.bim',model)
    rp=B/(NAME+'.Report')
    dump(B/(NAME+'.pbip'),{'version':'1.0','artifacts':[{'report':{'path':NAME+'.Report'}}],'settings':{'enableAutoRecovery':True}})
    dump(rp/'definition.pbir',{'version':'4.0','datasetReference':{'byPath':{'path':'../'+NAME+'.SemanticModel'}}})
    dump(rp/'definition/version.json',{'$schema':SCHEMA+'versionMetadata/1.0.0/schema.json','version':'2.0.0'})
    # Preserve Desktop-registered theme metadata when regenerating a local project.
    report_path=rp/'definition/report.json'
    old_report=json.loads(report_path.read_text(encoding='utf-8-sig')) if report_path.exists() else {}
    report={'$schema':SCHEMA+'report/2.0.0/schema.json','themeCollection':old_report.get('themeCollection',{})}
    if 'resourcePackages' in old_report: report['resourcePackages']=old_report['resourcePackages']
    dump(report_path,report)
    theme={'name':'Retail Navy','dataColors':['#2563EB','#16A34A','#F59E0B','#DC2626','#14213D'],'background':'#F8FAFC','foreground':'#14213D','tableAccent':'#2563EB','textClasses':{'label':{'fontFace':'Segoe UI'},'title':{'fontFace':'Segoe UI'}}}
    dump(B/'theme.json',theme)
    pages=[]; layout=[]
    def page(pid,title):
        pages.append(pid)
        folder=rp/'definition/pages'/pid
        dump(folder/'page.json',{'$schema':SCHEMA+'page/2.0.0/schema.json','name':pid,'displayName':title,'displayOption':'FitToPage','width':1440,'height':1000,
            'objects':{'background':[{'properties':{'color':color('#F8FAFC'),'transparency':lit(0)}}]}})
        return folder
    def visual(folder,typ,title,x,y,width,height,roles,sort=None):
        vid=f'v{len(layout):03d}'
        state={role:{'projections':[{'field':field(*f),'queryRef':f[0]+'.'+f[1]} for f in fields]} for role,fields in roles.items()}
        query={'queryState':state}
        if sort: query['sortDefinition']={'sort':[{'field':field(*sort[0]),'direction':sort[1]}],'isDefaultSort':False}
        v={'visualType':typ,'query':query,'drillFilterOtherVisuals':True,
            'visualContainerObjects':{'title':[{'properties':{'show':lit(True),'text':lit(title),'fontColor':color('#14213D'),'fontSize':lit(12),'fontFamily':lit('Segoe UI')}}],
                'background':[{'properties':{'show':lit(True),'color':color('#FFFFFF'),'transparency':lit(0)}}],
                'border':[{'properties':{'show':lit(True),'color':color('#E2E8F0'),'radius':lit(6)}}]}}
        if typ=='card': v['objects']={'labels':[{'properties':{'fontSize':lit(22),'color':color('#2563EB')}}],'categoryLabels':[{'properties':{'show':lit(False)}}]}
        if typ=='slicer': v['objects']={'data':[{'properties':{'mode':lit('Dropdown')}}]}
        dump(folder/'visuals'/vid/'visual.json',{'$schema':SCHEMA+'visualContainer/2.4.0/schema.json','name':vid,'position':{'x':x,'y':y,'z':len(layout),'width':width,'height':height,'tabOrder':len(layout)},'visual':v})
        layout.append(dict(page=folder.name,type=typ,title=title,roles=roles))
    def header(folder,measure): visual(folder,'card','Walmart M5 | 26 Apr 2015 - 24 Apr 2016 | 50 products / 2 stores',20,12,1400,75,{'Values':[ms(measure)]})
    def slicers(folder,fields):
        for idx,(label,t,c) in enumerate(fields): visual(folder,'slicer',label,20+idx*470,96,460,75,{'Values':[col(t,c)]})
    def cards(folder,names):
        width=1400/len(names)
        for idx,n in enumerate(names): visual(folder,'card',n,20+idx*width,184,width-12,100,{'Values':[ms(n)]})
    f=page('executive','Executive Overview'); header(f,'Overview Title')
    slicers(f,[('Date','DimDate','Date'),('Store','DimStore','Store_ID'),('Category','DimProduct','Category')])
    cards(f,['Total Sales Revenue','Total Units Sold','Total Products','Total Stores','Average Daily Units Sold'])
    visual(f,'lineChart','Monthly sales revenue (partial first/last month)',20,300,690,270,{'Category':[col('DimDate','Month')],'Y':[ms('Total Sales Revenue')]},(col('DimDate','Month'),'Ascending'))
    visual(f,'clusteredBarChart','Sales revenue by store',730,300,330,270,{'Category':[col('DimStore','Store_ID')],'Y':[ms('Total Sales Revenue')]})
    visual(f,'donutChart','Sales revenue by category',1080,300,340,270,{'Category':[col('DimProduct','Category')],'Y':[ms('Total Sales Revenue')]})
    visual(f,'clusteredBarChart','Top 10 products by revenue',20,590,690,380,{'Category':[col('DimProduct','Product_ID')],'Y':[ms('Top 10 Revenue')]},(ms('Top 10 Revenue'),'Descending'))
    visual(f,'lineChart','Daily units sold',730,590,690,380,{'Category':[col('DimDate','Date')],'Y':[ms('Total Units Sold')]},(col('DimDate','Date'),'Ascending'))
    f=page('products','ABC & Product Analysis'); header(f,'Products Title')
    slicers(f,[('Store','DimStore','Store_ID'),('Category','DimProduct','Category'),('ABC Class','DimProduct','ABC_Class')])
    cards(f,['A-Class Product Count','B-Class Product Count','C-Class Product Count','A-Class Revenue'])
    visual(f,'donutChart','ABC product distribution (fixed baseline classes)',20,300,340,270,{'Category':[col('DimProduct','ABC_Class')],'Y':[ms('Total Products')]})
    visual(f,'lineClusteredColumnComboChart','Pareto | full-period, both-store baseline',380,300,1040,270,{'Category':[col('DimProduct','Product_ID')],'Y':[ms('Baseline Product Revenue')],'Y2':[ms('Baseline Cumulative Revenue %')]},(ms('Baseline Product Revenue'),'Descending'))
    visual(f,'clusteredBarChart','Top 10 products by daily units',20,590,450,380,{'Category':[col('DimProduct','Product_ID')],'Y':[ms('Top 10 Daily Units')]},(ms('Top 10 Daily Units'),'Descending'))
    visual(f,'clusteredBarChart','Bottom 10 products by daily units',490,590,450,380,{'Category':[col('DimProduct','Product_ID')],'Y':[ms('Bottom 10 Daily Units')]},(ms('Bottom 10 Daily Units'),'Ascending'))
    visual(f,'tableEx','Product performance',960,590,460,380,{'Values':[col('DimProduct','Product_ID'),ms('Total Sales Revenue'),ms('Total Units Sold'),col('DimProduct','ABC_Class'),col('DimProduct','Movement_Class')]})
    f=page('inventory','Inventory Planning'); header(f,'Inventory Title')
    slicers(f,[('Store','DimStore','Store_ID'),('Category','DimProduct','Category'),('Product','DimProduct','Product_ID')])
    cards(f,['Average Daily Demand','Average Safety Stock','Average Reorder Point','Fast-Moving Product Count'])
    for x,title,measure in [(20,'Mean reorder threshold by product','Average Reorder Point'),(490,'Mean safety stock by product','Average Safety Stock'),(960,'Mean daily demand standard deviation','Demand Variability')]:
        visual(f,'clusteredBarChart',title,x,300,460,280,{'Category':[col('DimProduct','Product_ID')],'Y':[ms(measure)]},(ms(measure),'Descending'))
    visual(f,'lineChart','Mean reorder threshold | assumed lead time 5 / 7 / 10 days',20,600,460,370,{'Category':[col('Sensitivity','Assumed_Lead_Time_Days')],'Y':[ms('Scenario Reorder Point')]},(col('Sensitivity','Assumed_Lead_Time_Days'),'Ascending'))
    visual(f,'tableEx','Planning estimates | no current inventory / no reorder alerts',500,600,920,370,{'Values':[col('DimProduct','Product_ID'),col('DimStore','Store_ID'),ms('Average Daily Demand'),ms('Assumed Lead Time'),ms('Average Safety Stock'),ms('Average Reorder Point'),col('DimProduct','ABC_Class'),col('DimProduct','Movement_Class')]})
    dump(rp/'definition/pages/pages.json',{'$schema':SCHEMA+'pagesMetadata/1.0.0/schema.json','pageOrder':pages,'activePageName':pages[0]})
    dump(B/'report_layout.json',layout)
    (B/'DAX_measures.dax').write_text('\n\n'.join(f'{n} =\n{e}' for n,e in MEASURES.items()),encoding='utf-8')
    (B/'Power_Query.m').write_text('// Create DataFolder text parameter pointing to data/processed/ (trailing slash).\n\n'+'\n\n'.join(queries),encoding='utf-8')
    print(f'Generated PBIP: {len(pages)} pages, {len(layout)} visuals, {len(tables)} tables, {len(relationships)} relationships, {len(MEASURES)} measures')

if __name__=='__main__': main()
