// Create DataFolder text parameter pointing to data/processed/ (trailing slash).

// Sales
let
    Source = Csv.Document(File.Contents(DataFolder & "retail_sales.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"Date", type date}, {"Store_ID", type text}, {"Product_ID", type text}, {"Category", type text}, {"Department", type text}, {"Units_Sold", Int64.Type}, {"Unit_Price", type number}, {"Sales_Revenue", type number}, {"Month", type text}, {"Week", Int64.Type}, {"Day_of_Week", type text}}, "en-US")
in
    Typed

// DimDate
let
    Source = Csv.Document(File.Contents(DataFolder & "dim_date.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"Date", type date}, {"Month", type text}, {"Week", Int64.Type}, {"Day_of_Week", type text}}, "en-US")
in
    Typed

// DimProduct
let
    Source = Csv.Document(File.Contents(DataFolder & "dim_product.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"Product_ID", type text}, {"Category", type text}, {"Department", type text}, {"Total_Units_Sold", Int64.Type}, {"Total_Revenue", type number}, {"Observed_Days", Int64.Type}, {"Average_Daily_Units_Sold", type number}, {"Movement_Class", type text}, {"ABC_Class", type text}, {"Revenue_Contribution_Percent", type number}, {"Cumulative_Revenue_Percent", type number}}, "en-US")
in
    Typed

// DimStore
let
    Source = Csv.Document(File.Contents(DataFolder & "dim_store.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"Store_ID", type text}, {"State", type text}}, "en-US")
in
    Typed

// Inventory
let
    Source = Csv.Document(File.Contents(DataFolder & "inventory_planning.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"Store_ID", type text}, {"Product_ID", type text}, {"Average_Daily_Demand", type number}, {"Demand_Standard_Deviation", type number}, {"Assumed_Lead_Time_Days", Int64.Type}, {"Target_Service_Level", type number}, {"Safety_Stock", Int64.Type}, {"Reorder_Point", Int64.Type}, {"Movement_Class", type text}, {"ABC_Class", type text}}, "en-US")
in
    Typed

// Sensitivity
let
    Source = Csv.Document(File.Contents(DataFolder & "lead_time_sensitivity.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"Store_ID", type text}, {"Product_ID", type text}, {"Average_Daily_Demand", type number}, {"Demand_Standard_Deviation", type number}, {"Assumed_Lead_Time_Days", Int64.Type}, {"Target_Service_Level", type number}, {"Safety_Stock", Int64.Type}, {"Reorder_Point", Int64.Type}, {"Movement_Class", type text}, {"ABC_Class", type text}}, "en-US")
in
    Typed