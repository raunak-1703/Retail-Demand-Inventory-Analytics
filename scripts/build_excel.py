"""Build the requested Excel review workbook using openpyxl."""
from pathlib import Path
import json
import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.chart import LineChart, Reference
from openpyxl.utils import get_column_letter

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'data/processed'

def main():
    meta=json.loads((P/'run_metadata.json').read_text())
    wb=Workbook()
    ws=wb.active
    ws.title='Project Overview'
    rows=[['Retail Demand & Inventory Analytics','Project Overview'],['Purpose','Historical retail demand and assumed replenishment planning'],
        ['Source','https://www.kaggle.com/competitions/m5-forecasting-accuracy/data'],
        ['Public archive','https://doi.org/10.5281/zenodo.10203108'],['Period',meta['start']+' to '+meta['end']],
        ['Scope','50 products; CA_1 and CA_2; 365 days'],['Base lead time (days)',7],['Service level',.95],['Z score',1.645],
        ['Demand proxy','Observed sales; unmet demand and stockouts are unknown'],['ABC boundary','Class uses cumulative share before each product: <80% A, <95% B, else C'],
        ['Movement','P25 and below slow; P75 and above fast; other products medium. Ties stay together.'],
        ['Safety stock','CEILING(Z * sample daily standard deviation * SQRT(lead time))'],
        ['Reorder point','CEILING(mean daily demand * lead time + unrounded safety stock)'],
        ['Limits','No actual stock, inventory turnover, supplier lead times or reorder alerts'],
        ['Selection','First 50 SHA-256 sorted eligible product IDs; complete prices in both stores'],
        ['Currency','USD; revenue estimated as daily units multiplied by supplied weekly price'],
        ['Planning edits','CSV values are the validated base case; formula columns respond to lead time and Z inputs. Keep 95% paired with Z=1.645.'],
        ['Date filters','Inventory estimates use the entire fixed observation period.'],
        ['Redistribution','Source and generated row-level data are excluded from Git; review source terms.']]
    for row in rows: ws.append(row)
    ws.column_dimensions['A'].width=29; ws.column_dimensions['B'].width=105
    for row in ws:
        for c in row: c.alignment=Alignment(wrap_text=True,vertical='center')
        ws.row_dimensions[row[0].row].height=32
    ws['B8'].number_format='0%'
    mapping=[('Cleaned Sales Data','retail_sales'),('Product Analysis','product_summary'),('Store Analysis','store_summary'),('ABC Classification','abc_analysis'),('Inventory Planning','inventory_planning'),('Monthly Trends','monthly_sales')]
    counts={}
    for index,(sheet,name) in enumerate(mapping,1):
        frame=pd.read_csv(P/f'{name}.csv')
        ws=wb.create_sheet(sheet)
        ws.append(frame.columns.tolist())
        for row in frame.itertuples(index=False,name=None): ws.append(row)
        counts[sheet]=len(frame)
        if sheet=='Inventory Planning':
            ws.cell(1,11,'Safety Stock Formula'); ws.cell(1,12,'Reorder Point Formula')
            for r in range(2,ws.max_row+1):
                ws.cell(r,11,f"=ROUNDUP('Project Overview'!$B$9*D{r}*SQRT('Project Overview'!$B$7),0)")
                ws.cell(r,12,f"=ROUNDUP(C{r}*'Project Overview'!$B$7+'Project Overview'!$B$9*D{r}*SQRT('Project Overview'!$B$7),0)")
        ref=f'A1:{get_column_letter(ws.max_column)}{ws.max_row}'
        table=Table(displayName=f'Data{index}',ref=ref)
        table.tableStyleInfo=TableStyleInfo(name='TableStyleMedium2',showRowStripes=True)
        ws.add_table(table)
        for col in ws.iter_cols(min_row=2):
            header=ws.cell(1,col[0].column).value
            for c in col:
                if 'Percent' in header: c.number_format='0.00"%"'
                elif any(x in header for x in ['Revenue','Price']): c.number_format='"$"#,##0.00'
                elif header=='Target_Service_Level': c.number_format='0%'
                elif isinstance(c.value,(int,float)): c.number_format='#,##0.00' if any(x in header for x in ['Average','Deviation']) else '#,##0'
            ws.column_dimensions[col[0].column_letter].width=min(32,max(18,len(header)*.85))
        for c in ws[1]: c.alignment=Alignment(wrap_text=True,vertical='center')
        ws.row_dimensions[1].height=42
        numeric=[c.column_letter for c in ws[2] if isinstance(c.value,(int,float))]
        if numeric:
            col=numeric[-1]
            ws.conditional_formatting.add(f'{col}2:{col}{ws.max_row}',ColorScaleRule(start_type='min',start_color='EFF6FF',end_type='max',end_color='60A5FA'))
    ws=wb.create_sheet('KPI Summary')
    ws.append(['KPI','Python validated value','Excel cross-check'])
    daily=pd.read_csv(P/'retail_sales.csv'); abc=pd.read_csv(P/'abc_analysis.csv'); inv=pd.read_csv(P/'inventory_planning.csv')
    kpis=[('Total Sales Revenue',float(daily.Sales_Revenue.sum()),"=SUM('Cleaned Sales Data'!H2:H36501)"),
        ('Total Units Sold',int(daily.Units_Sold.sum()),"=SUM('Cleaned Sales Data'!F2:F36501)"),
        ('Total Products',50,"=COUNTA('Product Analysis'!A2:A51)"),('Total Stores',2,"=COUNTA('Store Analysis'!A2:A3)"),
        ('Average Daily Units Sold',float(daily.Units_Sold.sum()/365),'=B3/365'),
        ('A-Class Revenue',float(abc.loc[abc.ABC_Class=='A','Total_Revenue'].sum()),'=SUMIF(\'ABC Classification\'!G2:G51,"A",\'ABC Classification\'!D2:D51)'),
        ('Average Safety Stock',float(inv.Safety_Stock.mean()),"=AVERAGE('Inventory Planning'!G2:G101)"),
        ('Average Reorder Point',float(inv.Reorder_Point.mean()),"=AVERAGE('Inventory Planning'!H2:H101)")]
    for row in kpis: ws.append(row)
    ws.column_dimensions['A'].width=32; ws.column_dimensions['B'].width=25; ws.column_dimensions['C'].width=25
    for row in ws.iter_rows(min_row=2):
        for c in row[1:]: c.number_format='"$"#,##0.00' if 'Revenue' in row[0].value else '#,##0.00'
    ws['A12']='Blue column B contains Python-calculated results; column C recalculates in Excel.'
    ws.merge_cells('A12:E13'); ws['A12'].alignment=Alignment(wrap_text=True)
    for ws in wb:
        ws.freeze_panes='A2'; ws.sheet_view.showGridLines=False
        for c in ws[1]: c.fill=PatternFill('solid',fgColor='14213D'); c.font=Font(name='Calibri',bold=True,color='FFFFFF')
        ws.sheet_properties.pageSetUpPr.fitToPage=True
        ws.print_options.horizontalCentered=True
    output=ROOT/'excel/Retail_Inventory_Analysis.xlsx'; output.parent.mkdir(exist_ok=True)
    wb.save(output)
    reopened=load_workbook(output,read_only=False,data_only=False)
    assert len(reopened.sheetnames)==8
    for sheet,count in counts.items():
        assert reopened[sheet].max_row==count+1
        assert reopened[sheet].freeze_panes=='A2'
        assert len(reopened[sheet].tables)==1
    assert reopened['KPI Summary']['B2'].value==kpis[0][1]
    assert '#REF!' not in str([c.value for row in reopened['KPI Summary'] for c in row])
    print(f'Workbook verified: 8 sheets; {len(daily):,} sales rows; all six data tables and formulas preserved')

if __name__=='__main__': main()
