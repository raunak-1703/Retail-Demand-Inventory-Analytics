param([int]$Port=0)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
[void][Reflection.Assembly]::LoadFrom('C:\Program Files\Microsoft Power BI Desktop\bin\Microsoft.PowerBI.AdomdClient.dll')
if ($Port -eq 0) {
    $ports=Get-ChildItem "$env:LOCALAPPDATA\Microsoft\Power BI Desktop\AnalysisServicesWorkspaces" -Filter msmdsrv.port.txt -Recurse
} else { $ports=@($Port) }
$connection=$null
foreach ($candidate in $ports) {
    $value=if ($Port -eq 0) { (Get-Content -LiteralPath $candidate.FullName -Encoding Unicode -Raw).Trim() } else { "$Port" }
    $probe=New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection("Data Source=localhost:$value")
    try {
        $probe.Open()
        $cmd=$probe.CreateCommand(); $cmd.CommandText='EVALUATE ROW("SalesRows", COUNTROWS(Sales))'
        $reader=$cmd.ExecuteReader(); $ok=$reader.Read() -and $reader.GetValue(0) -eq 36500; $reader.Close()
        if ($ok) {$connection=$probe; break}
    } catch {} 
    $probe.Close()
}
if ($null -eq $connection) {throw 'No loaded retail model with 36500 sales rows was found.'}
function Query([string]$Text) {
    $cmd=$connection.CreateCommand(); $cmd.CommandText=$Text
    $reader=$cmd.ExecuteReader(); $rows=@()
    while ($reader.Read()) {
        $row=[ordered]@{}
        for ($c=0;$c -lt $reader.FieldCount;$c++) {$row[$reader.GetName($c)]=$reader.GetValue($c)}
        $rows+= [pscustomobject]$row
    }
    $reader.Close()
    return $rows
}
try {
    $summary=Query 'EVALUATE ROW("Revenue",[Total Sales Revenue],"Units",[Total Units Sold],"Products",[Total Products],"Stores",[Total Stores],"DailyUnits",[Average Daily Units Sold],"ARevenue",[A-Class Revenue],"ACount",[A-Class Product Count],"BCount",[B-Class Product Count],"CCount",[C-Class Product Count],"Safety",[Average Safety Stock],"ROP",[Average Reorder Point],"Demand",[Average Daily Demand],"Fast",[Fast-Moving Product Count])'
    $stores=Query 'EVALUATE SUMMARIZECOLUMNS(DimStore[Store_ID],"Revenue",[Total Sales Revenue],"Units",[Total Units Sold])'
    $classes=Query 'EVALUATE SUMMARIZECOLUMNS(DimProduct[ABC_Class],"Revenue",[Total Sales Revenue],"Products",[Total Products])'
    $scenario=Query 'EVALUATE SUMMARIZECOLUMNS(Sensitivity[Assumed_Lead_Time_Days],"ROP",[Scenario Reorder Point],"Safety",[Scenario Safety Stock])'
    $products=Query 'EVALUATE SUMMARIZECOLUMNS(DimProduct[Product_ID],"Revenue",[Total Sales Revenue],"Share",[Revenue Contribution %],"TopRevenue",[Top 10 Revenue],"Fast",[Top 10 Daily Units],"Slow",[Bottom 10 Daily Units])'
    $dates=Query 'EVALUATE SUMMARIZECOLUMNS(DimDate[Month],"Revenue",[Total Sales Revenue],"Units",[Total Units Sold])'
    $counts=Query 'EVALUATE ROW("Sales",COUNTROWS(Sales),"Date",COUNTROWS(DimDate),"Product",COUNTROWS(DimProduct),"Store",COUNTROWS(DimStore),"Inventory",COUNTROWS(Inventory),"Sensitivity",COUNTROWS(Sensitivity))'
    $relations=Query 'SELECT [Name],[FromTableID],[FromColumnID],[ToTableID],[ToColumnID],[IsActive],[CrossFilteringBehavior] FROM $SYSTEM.TMSCHEMA_RELATIONSHIPS'
    @{summary=$summary; stores=$stores; classes=$classes; scenario=$scenario; products=$products; months=$dates; counts=$counts; relationships=$relations} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $root 'reports\powerbi_live_results.json') -Encoding UTF8
    Write-Output 'Live DAX queries executed: KPIs, stores, classes, scenarios, products, dates, row counts and relationships.'
} finally {$connection.Close()}
