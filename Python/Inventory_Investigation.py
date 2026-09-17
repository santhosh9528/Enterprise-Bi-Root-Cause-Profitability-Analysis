from getpass import getpass
# ============================================================
# PART 12: INVENTORY INVESTIGATION
# ============================================================

from pathlib import Path
import warnings

import mysql.connector
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore")

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 220)
pd.set_option("display.float_format", lambda x: f"{x:,.2f}")


# ============================================================
# 1. DATABASE CONFIGURATION
# ============================================================

MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = getpass("Enter MySQL password: ")
MYSQL_DATABASE = "enterprise_bi"


# ============================================================
# 2. INVENTORY RULES
# ============================================================

CRITICAL_STOCK_DAYS = 30
TARGET_STOCK_DAYS = 90
DEAD_STOCK_DAYS = 180


# ============================================================
# 3. OUTPUT LOCATION
# ============================================================

CURRENT_FOLDER = Path(__file__).resolve().parent
PROJECT_FOLDER = CURRENT_FOLDER.parent

OUTPUT_FOLDER = PROJECT_FOLDER / "Inventory_Analysis"
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

EXCEL_OUTPUT = OUTPUT_FOLDER / "Inventory_Investigation_Report.xlsx"
CSV_OUTPUT = OUTPUT_FOLDER / "Inventory_Product_Summary.csv"

print("=" * 75)
print("INVENTORY INVESTIGATION STARTED")
print("=" * 75)


# ============================================================
# 4. DATABASE CONNECTION
# ============================================================

try:
    connection = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )

    print("\nMySQL connection successful!")

except mysql.connector.Error as error:
    print("\nMySQL connection failed!")
    print(error)
    raise SystemExit


# ============================================================
# 5. LOAD TABLES
# ============================================================

inventory_df = pd.read_sql(
    "SELECT * FROM inventory",
    connection
)

purchases_df = pd.read_sql(
    "SELECT * FROM purchases",
    connection
)

returns_df = pd.read_sql(
    "SELECT * FROM returns",
    connection
)

products_df = pd.read_sql(
    "SELECT * FROM product_master",
    connection
)

sales_profit_df = pd.read_sql(
    """
    SELECT
        Product_ID,
        SUM(Quantity) AS Units_Sold,
        SUM(Product_Cost) AS Cost_Of_Goods_Sold,
        SUM(Revenue) AS Revenue,
        SUM(Net_Profit) AS Net_Profit,
        MIN(Sale_Date) AS First_Sale_Date,
        MAX(Sale_Date) AS Last_Sale_Date

    FROM vw_sales_profitability

    WHERE Product_ID IS NOT NULL

    GROUP BY Product_ID
    """,
    connection
)

connection.close()

print("All inventory-related datasets loaded.")
print("MySQL connection closed.")


# ============================================================
# 6. HELPER FUNCTION TO FIND COLUMNS
# ============================================================

def normalize_column_name(column_name):
    return (
        str(column_name)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def find_column(dataframe, possible_names, required=True):
    normalized_columns = {
        normalize_column_name(column): column
        for column in dataframe.columns
    }

    for possible_name in possible_names:
        normalized_name = normalize_column_name(possible_name)

        if normalized_name in normalized_columns:
            return normalized_columns[normalized_name]

    if required:
        raise KeyError(
            f"Column not found. Expected one of: {possible_names}. "
            f"Available columns: {list(dataframe.columns)}"
        )

    return None


def numeric_series(dataframe, column_name):
    if column_name is None:
        return pd.Series(
            0,
            index=dataframe.index,
            dtype=float
        )

    return pd.to_numeric(
        dataframe[column_name],
        errors="coerce"
    ).fillna(0)


# ============================================================
# 7. IDENTIFY REQUIRED COLUMNS
# ============================================================

inventory_product_col = find_column(
    inventory_df,
    ["Product_ID", "ProductID"]
)

inventory_warehouse_col = find_column(
    inventory_df,
    ["Warehouse_ID", "WarehouseID"]
)

inventory_date_col = find_column(
    inventory_df,
    ["Snapshot_Date", "Inventory_Date", "Date"]
)

opening_stock_col = find_column(
    inventory_df,
    ["Opening_Stock", "OpeningStock"],
    required=False
)

closing_stock_col = find_column(
    inventory_df,
    ["Closing_Stock", "ClosingStock"]
)

stock_value_col = find_column(
    inventory_df,
    ["Stock_Value", "Inventory_Value"]
)

inventory_purchase_col = find_column(
    inventory_df,
    [
        "Purchases",
        "Purchase_Quantity",
        "Purchased_Quantity"
    ],
    required=False
)

inventory_sales_col = find_column(
    inventory_df,
    [
        "Sales",
        "Sales_Quantity",
        "Sold_Quantity"
    ],
    required=False
)

inventory_returns_col = find_column(
    inventory_df,
    [
        "Returns",
        "Return_Quantity",
        "Returned_Quantity"
    ],
    required=False
)

purchase_product_col = find_column(
    purchases_df,
    ["Product_ID", "ProductID"]
)

purchase_quantity_col = find_column(
    purchases_df,
    [
        "Quantity",
        "Purchase_Quantity",
        "Ordered_Quantity"
    ]
)

purchase_date_col = find_column(
    purchases_df,
    ["Purchase_Date", "Order_Date", "Date"]
)

expected_delivery_col = find_column(
    purchases_df,
    [
        "Expected_Delivery_Date",
        "ExpectedDeliveryDate",
        "Scheduled_Delivery_Date"
    ],
    required=False
)

actual_delivery_col = find_column(
    purchases_df,
    [
        "Actual_Delivery_Date",
        "Delivery_Date",
        "ActualDeliveryDate"
    ],
    required=False
)

return_product_col = find_column(
    returns_df,
    ["Product_ID", "ProductID"]
)

return_quantity_col = find_column(
    returns_df,
    [
        "Return_Quantity",
        "Returned_Quantity",
        "Quantity"
    ]
)

product_id_col = find_column(
    products_df,
    ["Product_ID", "ProductID"]
)

product_name_col = find_column(
    products_df,
    ["Product_Name", "ProductName"]
)

category_col = find_column(
    products_df,
    ["Category"]
)

subcategory_col = find_column(
    products_df,
    ["Subcategory", "Sub_Category"],
    required=False
)


# ============================================================
# 8. CLEAN DATA TYPES
# ============================================================

inventory_df[inventory_date_col] = pd.to_datetime(
    inventory_df[inventory_date_col],
    errors="coerce"
)

purchases_df[purchase_date_col] = pd.to_datetime(
    purchases_df[purchase_date_col],
    errors="coerce"
)

if expected_delivery_col:
    purchases_df[expected_delivery_col] = pd.to_datetime(
        purchases_df[expected_delivery_col],
        errors="coerce"
    )

if actual_delivery_col:
    purchases_df[actual_delivery_col] = pd.to_datetime(
        purchases_df[actual_delivery_col],
        errors="coerce"
    )

sales_profit_df["First_Sale_Date"] = pd.to_datetime(
    sales_profit_df["First_Sale_Date"],
    errors="coerce"
)

sales_profit_df["Last_Sale_Date"] = pd.to_datetime(
    sales_profit_df["Last_Sale_Date"],
    errors="coerce"
)

inventory_df["Opening_Stock_Clean"] = numeric_series(
    inventory_df,
    opening_stock_col
)

inventory_df["Closing_Stock_Clean"] = numeric_series(
    inventory_df,
    closing_stock_col
)

inventory_df["Stock_Value_Clean"] = numeric_series(
    inventory_df,
    stock_value_col
)

inventory_df["Inventory_Purchases_Clean"] = numeric_series(
    inventory_df,
    inventory_purchase_col
)

inventory_df["Inventory_Sales_Clean"] = numeric_series(
    inventory_df,
    inventory_sales_col
)

inventory_df["Inventory_Returns_Clean"] = numeric_series(
    inventory_df,
    inventory_returns_col
)

purchases_df["Purchase_Quantity_Clean"] = numeric_series(
    purchases_df,
    purchase_quantity_col
)

returns_df["Return_Quantity_Clean"] = numeric_series(
    returns_df,
    return_quantity_col
)


# ============================================================
# 9. ANALYSIS PERIOD
# ============================================================

analysis_start_date = min(
    inventory_df[inventory_date_col].min(),
    sales_profit_df["First_Sale_Date"].min()
)

analysis_end_date = max(
    inventory_df[inventory_date_col].max(),
    sales_profit_df["Last_Sale_Date"].max()
)

analysis_days = max(
    (analysis_end_date - analysis_start_date).days + 1,
    1
)

print(f"\nAnalysis start date: {analysis_start_date.date()}")
print(f"Analysis end date: {analysis_end_date.date()}")
print(f"Analysis period: {analysis_days:,} days")


# ============================================================
# 10. OPENING INVENTORY
# First record for each Product + Warehouse
# ============================================================

first_inventory_rows = (
    inventory_df
    .sort_values(inventory_date_col)
    .drop_duplicates(
        subset=[
            inventory_product_col,
            inventory_warehouse_col
        ],
        keep="first"
    )
)

opening_inventory = (
    first_inventory_rows
    .groupby(inventory_product_col)
    .agg(
        Opening_Stock=("Opening_Stock_Clean", "sum")
    )
    .reset_index()
    .rename(
        columns={
            inventory_product_col: "Product_ID"
        }
    )
)


# ============================================================
# 11. CURRENT/CLOSING INVENTORY
# Latest record for each Product + Warehouse
# ============================================================

latest_inventory_rows = (
    inventory_df
    .sort_values(inventory_date_col)
    .drop_duplicates(
        subset=[
            inventory_product_col,
            inventory_warehouse_col
        ],
        keep="last"
    )
)

current_inventory = (
    latest_inventory_rows
    .groupby(inventory_product_col)
    .agg(
        Closing_Stock=("Closing_Stock_Clean", "sum"),
        Closing_Stock_Value=("Stock_Value_Clean", "sum"),
        Warehouse_Count=(
            inventory_warehouse_col,
            "nunique"
        )
    )
    .reset_index()
    .rename(
        columns={
            inventory_product_col: "Product_ID"
        }
    )
)


# ============================================================
# 12. AVERAGE DAILY INVENTORY
# ============================================================

daily_inventory = (
    inventory_df
    .groupby(
        [
            inventory_product_col,
            inventory_date_col
        ]
    )
    .agg(
        Daily_Stock_Units=("Closing_Stock_Clean", "sum"),
        Daily_Stock_Value=("Stock_Value_Clean", "sum")
    )
    .reset_index()
)

average_inventory = (
    daily_inventory
    .groupby(inventory_product_col)
    .agg(
        Average_Inventory_Units=(
            "Daily_Stock_Units",
            "mean"
        ),
        Average_Inventory_Value=(
            "Daily_Stock_Value",
            "mean"
        )
    )
    .reset_index()
    .rename(
        columns={
            inventory_product_col: "Product_ID"
        }
    )
)


# ============================================================
# 13. STOCKOUT RATE
# ============================================================

stockout_summary = (
    inventory_df
    .assign(
        Stockout_Flag=np.where(
            inventory_df["Closing_Stock_Clean"] <= 0,
            1,
            0
        )
    )
    .groupby(inventory_product_col)
    .agg(
        Inventory_Observations=(
            "Stockout_Flag",
            "count"
        ),
        Stockout_Observations=(
            "Stockout_Flag",
            "sum"
        )
    )
    .reset_index()
    .rename(
        columns={
            inventory_product_col: "Product_ID"
        }
    )
)

stockout_summary["Stockout_Rate_Percentage"] = (
    stockout_summary["Stockout_Observations"]
    / stockout_summary["Inventory_Observations"]
    * 100
)


# ============================================================
# 14. PURCHASE SUMMARY AND LEAD TIME
# ============================================================

if actual_delivery_col:
    purchases_df["Lead_Time_Days"] = (
        purchases_df[actual_delivery_col]
        - purchases_df[purchase_date_col]
    ).dt.days
else:
    purchases_df["Lead_Time_Days"] = np.nan

if expected_delivery_col and actual_delivery_col:
    purchases_df["Delivery_Delay_Days"] = (
        purchases_df[actual_delivery_col]
        - purchases_df[expected_delivery_col]
    ).dt.days

    purchases_df["On_Time_Flag"] = np.where(
        purchases_df["Delivery_Delay_Days"] <= 0,
        1,
        0
    )
else:
    purchases_df["Delivery_Delay_Days"] = np.nan
    purchases_df["On_Time_Flag"] = np.nan

purchase_summary = (
    purchases_df
    .groupby(purchase_product_col)
    .agg(
        Purchased_Units=(
            "Purchase_Quantity_Clean",
            "sum"
        ),
        Purchase_Orders=(
            purchase_product_col,
            "size"
        ),
        Average_Lead_Time_Days=(
            "Lead_Time_Days",
            "mean"
        ),
        Average_Delivery_Delay_Days=(
            "Delivery_Delay_Days",
            "mean"
        ),
        On_Time_Delivery_Rate=(
            "On_Time_Flag",
            "mean"
        )
    )
    .reset_index()
    .rename(
        columns={
            purchase_product_col: "Product_ID"
        }
    )
)

purchase_summary["On_Time_Delivery_Rate_Percentage"] = (
    purchase_summary["On_Time_Delivery_Rate"] * 100
)


# ============================================================
# 15. RETURN SUMMARY
# ============================================================

return_summary = (
    returns_df
    .groupby(return_product_col)
    .agg(
        Returned_Units=(
            "Return_Quantity_Clean",
            "sum"
        )
    )
    .reset_index()
    .rename(
        columns={
            return_product_col: "Product_ID"
        }
    )
)


# ============================================================
# 16. PRODUCT MASTER
# ============================================================

product_columns = [
    product_id_col,
    product_name_col,
    category_col
]

if subcategory_col:
    product_columns.append(subcategory_col)

product_master = products_df[
    product_columns
].copy()

rename_columns = {
    product_id_col: "Product_ID",
    product_name_col: "Product_Name",
    category_col: "Category"
}

if subcategory_col:
    rename_columns[subcategory_col] = "Subcategory"

product_master = product_master.rename(
    columns=rename_columns
)


# ============================================================
# 17. MERGE INVENTORY ANALYSIS
# ============================================================

product_summary = product_master.merge(
    opening_inventory,
    on="Product_ID",
    how="left"
)

product_summary = product_summary.merge(
    current_inventory,
    on="Product_ID",
    how="left"
)

product_summary = product_summary.merge(
    average_inventory,
    on="Product_ID",
    how="left"
)

product_summary = product_summary.merge(
    stockout_summary,
    on="Product_ID",
    how="left"
)

product_summary = product_summary.merge(
    purchase_summary,
    on="Product_ID",
    how="left"
)

product_summary = product_summary.merge(
    return_summary,
    on="Product_ID",
    how="left"
)

product_summary = product_summary.merge(
    sales_profit_df,
    on="Product_ID",
    how="left"
)

numeric_columns = product_summary.select_dtypes(
    include=[np.number]
).columns

product_summary[numeric_columns] = (
    product_summary[numeric_columns]
    .fillna(0)
)


# ============================================================
# 18. INVENTORY KPIs
# ============================================================

product_summary["Average_Daily_Demand"] = (
    product_summary["Units_Sold"]
    / analysis_days
)

product_summary["Inventory_Turnover"] = np.where(
    product_summary["Average_Inventory_Value"] > 0,
    product_summary["Cost_Of_Goods_Sold"]
    / product_summary["Average_Inventory_Value"],
    0
)

product_summary["Days_Inventory"] = np.where(
    product_summary["Average_Daily_Demand"] > 0,
    product_summary["Closing_Stock"]
    / product_summary["Average_Daily_Demand"],
    0
)

product_summary["Return_Rate_Percentage"] = np.where(
    product_summary["Units_Sold"] > 0,
    product_summary["Returned_Units"]
    / product_summary["Units_Sold"]
    * 100,
    0
)

product_summary["Average_Unit_Stock_Value"] = np.where(
    product_summary["Closing_Stock"] > 0,
    product_summary["Closing_Stock_Value"]
    / product_summary["Closing_Stock"],
    0
)


# ============================================================
# 19. EXCESS INVENTORY
# Target = 90 days of demand
# ============================================================

product_summary["Target_Stock_Units"] = (
    product_summary["Average_Daily_Demand"]
    * TARGET_STOCK_DAYS
)

product_summary["Excess_Inventory_Units"] = np.maximum(
    product_summary["Closing_Stock"]
    - product_summary["Target_Stock_Units"],
    0
)

product_summary["Excess_Inventory_Value"] = (
    product_summary["Excess_Inventory_Units"]
    * product_summary["Average_Unit_Stock_Value"]
)


# ============================================================
# 20. INVENTORY RECONCILIATION
# ============================================================

product_summary["Expected_Closing_Stock"] = (
    product_summary["Opening_Stock"]
    + product_summary["Purchased_Units"]
    + product_summary["Returned_Units"]
    - product_summary["Units_Sold"]
)

product_summary["Inventory_Reconciliation_Difference"] = (
    product_summary["Closing_Stock"]
    - product_summary["Expected_Closing_Stock"]
)


# ============================================================
# 21. BUSINESS THRESHOLDS
# ============================================================

high_demand_threshold = product_summary[
    "Average_Daily_Demand"
].quantile(0.75)

low_demand_threshold = product_summary[
    "Average_Daily_Demand"
].quantile(0.25)

high_inventory_threshold = product_summary[
    "Closing_Stock"
].quantile(0.75)

valid_lead_times = product_summary.loc[
    product_summary["Average_Lead_Time_Days"] > 0,
    "Average_Lead_Time_Days"
]

if valid_lead_times.empty:
    long_lead_time_threshold = 0
else:
    long_lead_time_threshold = valid_lead_times.quantile(0.75)


# ============================================================
# 22. PRODUCT CLASSIFICATION
# ============================================================

def classify_inventory(row):
    if (
        row["Closing_Stock"] < 0
        or row["Closing_Stock_Value"] < 0
    ):
        return "Inventory Data Issue"

    if (
        row["Average_Daily_Demand"] >= high_demand_threshold
        and row["Days_Inventory"] <= CRITICAL_STOCK_DAYS
        and row["Average_Lead_Time_Days"]
        >= long_lead_time_threshold
    ):
        return "Critical Product"

    if (
        row["Average_Daily_Demand"] <= low_demand_threshold
        and row["Closing_Stock"] >= high_inventory_threshold
        and row["Days_Inventory"] >= DEAD_STOCK_DAYS
    ):
        return "Dead Stock"

    if row["Excess_Inventory_Units"] > 0:
        return "Excess Inventory"

    if row["Stockout_Rate_Percentage"] > 10:
        return "Stockout Risk"

    return "Normal"


product_summary["Inventory_Status"] = (
    product_summary.apply(
        classify_inventory,
        axis=1
    )
)


# ============================================================
# 23. PRIORITY
# ============================================================

def assign_priority(row):
    if row["Inventory_Status"] in [
        "Critical Product",
        "Inventory Data Issue"
    ]:
        return "Critical"

    if row["Inventory_Status"] in [
        "Dead Stock",
        "Stockout Risk"
    ]:
        return "High"

    if row["Inventory_Status"] == "Excess Inventory":
        return "Medium"

    return "Low"


product_summary["Priority"] = product_summary.apply(
    assign_priority,
    axis=1
)


# ============================================================
# 24. RECOMMENDED ACTION
# ============================================================

def recommended_action(row):
    status = row["Inventory_Status"]

    if status == "Inventory Data Issue":
        return (
            "Investigate negative stock and correct inventory "
            "movement or reconciliation records."
        )

    if status == "Critical Product":
        return (
            "Create urgent purchase order, increase safety stock "
            "and reduce supplier lead time."
        )

    if status == "Dead Stock":
        return (
            "Stop further purchasing and use clearance, bundle "
            "or supplier-return strategy."
        )

    if status == "Excess Inventory":
        return (
            "Reduce reorder quantity and transfer or promote "
            "excess stock."
        )

    if status == "Stockout Risk":
        return (
            "Review reorder point and maintain safety stock."
        )

    return "Continue normal inventory monitoring."


product_summary["Recommended_Action"] = (
    product_summary.apply(
        recommended_action,
        axis=1
    )
)


# ============================================================
# 25. CRITICAL AND DEAD-STOCK TABLES
# ============================================================

critical_products = product_summary[
    product_summary["Inventory_Status"]
    == "Critical Product"
].copy()

critical_products = critical_products.sort_values(
    by=[
        "Average_Daily_Demand",
        "Average_Lead_Time_Days"
    ],
    ascending=[False, False]
)

dead_stock = product_summary[
    product_summary["Inventory_Status"]
    == "Dead Stock"
].copy()

dead_stock = dead_stock.sort_values(
    "Excess_Inventory_Value",
    ascending=False
)

inventory_issues = product_summary[
    product_summary["Inventory_Status"]
    == "Inventory Data Issue"
].copy()

inventory_issues = inventory_issues.sort_values(
    "Closing_Stock_Value"
)

excess_inventory = product_summary[
    product_summary["Excess_Inventory_Units"] > 0
].copy()

excess_inventory = excess_inventory.sort_values(
    "Excess_Inventory_Value",
    ascending=False
)


# ============================================================
# 26. INVENTORY STATUS SUMMARY
# ============================================================

status_summary = (
    product_summary
    .groupby(
        [
            "Inventory_Status",
            "Priority"
        ]
    )
    .agg(
        Product_Count=("Product_ID", "nunique"),
        Closing_Stock=("Closing_Stock", "sum"),
        Closing_Stock_Value=(
            "Closing_Stock_Value",
            "sum"
        ),
        Excess_Inventory_Units=(
            "Excess_Inventory_Units",
            "sum"
        ),
        Excess_Inventory_Value=(
            "Excess_Inventory_Value",
            "sum"
        ),
        Revenue=("Revenue", "sum"),
        Net_Profit=("Net_Profit", "sum")
    )
    .reset_index()
)

status_summary["Product_Percentage"] = (
    status_summary["Product_Count"]
    / product_summary["Product_ID"].nunique()
    * 100
)


# ============================================================
# 27. COMPANY INVENTORY KPIs
# ============================================================

total_cogs = product_summary[
    "Cost_Of_Goods_Sold"
].sum()

total_average_inventory_value = product_summary[
    "Average_Inventory_Value"
].sum()

company_inventory_turnover = (
    total_cogs / total_average_inventory_value
    if total_average_inventory_value > 0
    else 0
)

company_days_inventory = (
    365 / company_inventory_turnover
    if company_inventory_turnover > 0
    else 0
)

total_observations = product_summary[
    "Inventory_Observations"
].sum()

total_stockouts = product_summary[
    "Stockout_Observations"
].sum()

company_stockout_rate = (
    total_stockouts / total_observations * 100
    if total_observations > 0
    else 0
)

company_summary = pd.DataFrame(
    {
        "Metric": [
            "Analysis Start Date",
            "Analysis End Date",
            "Analysis Days",
            "Total Products",
            "Opening Stock Units",
            "Purchased Units",
            "Sold Units",
            "Returned Units",
            "Closing Stock Units",
            "Closing Stock Value",
            "Average Inventory Value",
            "Cost of Goods Sold",
            "Inventory Turnover",
            "Days Inventory",
            "Stockout Rate (%)",
            "Critical Products",
            "Dead Stock Products",
            "Negative Inventory Products",
            "Excess Inventory Units",
            "Excess Inventory Value"
        ],

        "Value": [
            analysis_start_date.date(),
            analysis_end_date.date(),
            analysis_days,
            product_summary["Product_ID"].nunique(),
            product_summary["Opening_Stock"].sum(),
            product_summary["Purchased_Units"].sum(),
            product_summary["Units_Sold"].sum(),
            product_summary["Returned_Units"].sum(),
            product_summary["Closing_Stock"].sum(),
            product_summary["Closing_Stock_Value"].sum(),
            total_average_inventory_value,
            total_cogs,
            company_inventory_turnover,
            company_days_inventory,
            company_stockout_rate,
            len(critical_products),
            len(dead_stock),
            len(inventory_issues),
            product_summary[
                "Excess_Inventory_Units"
            ].sum(),
            product_summary[
                "Excess_Inventory_Value"
            ].sum()
        ]
    }
)


# ============================================================
# 28. ROUND RESULTS
# ============================================================

for dataframe in [
    product_summary,
    critical_products,
    dead_stock,
    inventory_issues,
    excess_inventory,
    status_summary
]:
    decimal_columns = dataframe.select_dtypes(
        include=[np.number]
    ).columns

    dataframe[decimal_columns] = dataframe[
        decimal_columns
    ].round(2)


# ============================================================
# 29. SAVE CSV
# ============================================================

product_summary.to_csv(
    CSV_OUTPUT,
    index=False
)


# ============================================================
# 30. SAVE EXCEL REPORT
# ============================================================

with pd.ExcelWriter(
    EXCEL_OUTPUT,
    engine="openpyxl"
) as writer:

    company_summary.to_excel(
        writer,
        sheet_name="Executive_Summary",
        index=False
    )

    status_summary.to_excel(
        writer,
        sheet_name="Status_Summary",
        index=False
    )

    critical_products.to_excel(
        writer,
        sheet_name="Critical_Products",
        index=False
    )

    dead_stock.to_excel(
        writer,
        sheet_name="Dead_Stock",
        index=False
    )

    excess_inventory.to_excel(
        writer,
        sheet_name="Excess_Inventory",
        index=False
    )

    inventory_issues.to_excel(
        writer,
        sheet_name="Inventory_Data_Issues",
        index=False
    )

    product_summary.to_excel(
        writer,
        sheet_name="Product_Inventory",
        index=False
    )

    workbook = writer.book

    for worksheet in workbook.worksheets:
        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions

        for column_cells in worksheet.columns:
            max_length = 0
            column_letter = column_cells[0].column_letter

            for cell in column_cells:
                try:
                    max_length = max(
                        max_length,
                        len(str(cell.value))
                    )
                except Exception:
                    pass

            worksheet.column_dimensions[
                column_letter
            ].width = min(max_length + 2, 45)


# ============================================================
# 31. CREATE CHARTS
# ============================================================

sns.set_theme(style="whitegrid")

# Chart 1: Inventory status

plt.figure(figsize=(11, 6))

status_chart = (
    product_summary["Inventory_Status"]
    .value_counts()
    .reset_index()
)

status_chart.columns = [
    "Inventory_Status",
    "Product_Count"
]

sns.barplot(
    data=status_chart,
    x="Inventory_Status",
    y="Product_Count",
    palette="Set2"
)

plt.title(
    "Products by Inventory Status",
    fontsize=15,
    fontweight="bold"
)

plt.xlabel("Inventory Status")
plt.ylabel("Product Count")
plt.xticks(rotation=25)
plt.tight_layout()

plt.savefig(
    OUTPUT_FOLDER / "01_Inventory_Status.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# Chart 2: Top excess-inventory products

top_excess = excess_inventory.head(15)

if not top_excess.empty:
    plt.figure(figsize=(12, 7))

    sns.barplot(
        data=top_excess,
        y="Product_Name",
        x="Excess_Inventory_Value",
        palette="Reds_r"
    )

    plt.title(
        "Top 15 Products by Excess Inventory Value",
        fontsize=15,
        fontweight="bold"
    )

    plt.xlabel("Excess Inventory Value")
    plt.ylabel("Product")
    plt.tight_layout()

    plt.savefig(
        OUTPUT_FOLDER / "02_Excess_Inventory.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()


# Chart 3: Demand vs stock

valid_scatter = product_summary[
    (product_summary["Closing_Stock"] >= 0)
    & (product_summary["Average_Daily_Demand"] >= 0)
].copy()

plt.figure(figsize=(11, 7))

sns.scatterplot(
    data=valid_scatter,
    x="Average_Daily_Demand",
    y="Closing_Stock",
    hue="Inventory_Status",
    alpha=0.75
)

plt.title(
    "Product Demand vs Current Stock",
    fontsize=15,
    fontweight="bold"
)

plt.xlabel("Average Daily Demand")
plt.ylabel("Closing Stock")
plt.tight_layout()

plt.savefig(
    OUTPUT_FOLDER / "03_Demand_vs_Stock.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 32. PRINT RESULTS
# ============================================================

print("\n" + "=" * 75)
print("COMPANY INVENTORY SUMMARY")
print("=" * 75)

print(company_summary.to_string(index=False))

print("\n" + "=" * 75)
print("INVENTORY STATUS SUMMARY")
print("=" * 75)

print(status_summary.to_string(index=False))

print("\n" + "=" * 75)
print("TOP 10 CRITICAL PRODUCTS")
print("=" * 75)

critical_display_columns = [
    "Product_ID",
    "Product_Name",
    "Category",
    "Average_Daily_Demand",
    "Closing_Stock",
    "Days_Inventory",
    "Average_Lead_Time_Days",
    "Stockout_Rate_Percentage",
    "Priority"
]

if critical_products.empty:
    print("No products matched all critical-product conditions.")
else:
    print(
        critical_products[
            critical_display_columns
        ].head(10).to_string(index=False)
    )

print("\n" + "=" * 75)
print("TOP 10 DEAD-STOCK PRODUCTS")
print("=" * 75)

dead_display_columns = [
    "Product_ID",
    "Product_Name",
    "Category",
    "Average_Daily_Demand",
    "Closing_Stock",
    "Days_Inventory",
    "Excess_Inventory_Value",
    "Priority"
]

if dead_stock.empty:
    print("No products matched all dead-stock conditions.")
else:
    print(
        dead_stock[
            dead_display_columns
        ].head(10).to_string(index=False)
    )

print("\n" + "=" * 75)
print("FINAL INVENTORY FINDINGS")
print("=" * 75)

print(
    f"\nInventory turnover: "
    f"{company_inventory_turnover:,.2f} times"
)

print(
    f"Days inventory: "
    f"{company_days_inventory:,.2f} days"
)

print(
    f"Stockout rate: "
    f"{company_stockout_rate:,.2f}%"
)

print(
    f"Critical products: "
    f"{len(critical_products):,}"
)

print(
    f"Dead-stock products: "
    f"{len(dead_stock):,}"
)

print(
    f"Negative inventory products: "
    f"{len(inventory_issues):,}"
)

print(
    f"Excess inventory financial value: "
    f"{product_summary['Excess_Inventory_Value'].sum():,.2f}"
)

print("\n" + "=" * 75)
print("INVENTORY INVESTIGATION COMPLETED SUCCESSFULLY")
print("=" * 75)

print(f"\nExcel report saved in:\n{EXCEL_OUTPUT}")
print(f"\nCSV report saved in:\n{CSV_OUTPUT}")
print(f"\nCharts saved in:\n{OUTPUT_FOLDER}")