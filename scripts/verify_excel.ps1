$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$path = Join-Path $root 'excel\Retail_Inventory_Analysis.xlsx'
$temp = Join-Path $root '.tmp\excel_preview'
New-Item -ItemType Directory -Path $temp -Force | Out-Null
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
try {
    $book = $excel.Workbooks.Open($path)
    $excel.CalculateFullRebuild()
    $kpi = $book.Worksheets.Item('KPI Summary')
    for ($r=2; $r -le 9; $r++) {
        $expected = [double]$kpi.Cells.Item($r,2).Value2
        $actual = [double]$kpi.Cells.Item($r,3).Value2
        if ([Math]::Abs($expected-$actual) -gt 0.00001) { throw "KPI mismatch at row $r" }
    }
    $inv = $book.Worksheets.Item('Inventory Planning')
    for ($r=2; $r -le 101; $r++) {
        if ($inv.Cells.Item($r,7).Value2 -ne $inv.Cells.Item($r,11).Value2) {throw "Safety stock mismatch $r"}
        if ($inv.Cells.Item($r,8).Value2 -ne $inv.Cells.Item($r,12).Value2) {throw "Reorder point mismatch $r"}
    }
    $overview = $book.Worksheets.Item('Project Overview')
    $old = $inv.Cells.Item(2,12).Value2
    $overview.Cells.Item(7,2).Value2 = 10
    $excel.CalculateFullRebuild()
    if ($inv.Cells.Item(2,12).Value2 -lt $old) {throw 'Lead time sensitivity failed'}
    $overview.Cells.Item(7,2).Value2 = 7
    $excel.CalculateFullRebuild()
    $book.Save()
    foreach ($sheet in $book.Worksheets) {
        $lastCol = [Math]::Min(12,$sheet.UsedRange.Columns.Count)
        $lastRow = [Math]::Min(16,$sheet.UsedRange.Rows.Count)
        $sheet.PageSetup.PrintArea = $sheet.Range($sheet.Cells.Item(1,1),$sheet.Cells.Item($lastRow,$lastCol)).Address()
        $sheet.PageSetup.Orientation = 2
        $sheet.PageSetup.Zoom = $false
        $sheet.PageSetup.FitToPagesWide = 1
        $sheet.PageSetup.FitToPagesTall = 1
        $sheet.ExportAsFixedFormat(0,(Join-Path $temp ($sheet.Name+'.pdf')))
    }
    $book.Close($false)
    Write-Output 'Excel native verification passed: 8 KPI formulas, 200 stock formulas, lead-time input change, 8 sheet previews.'
} finally {
    $excel.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)
}
