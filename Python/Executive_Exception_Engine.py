# ============================================================
# PART 17: EXECUTIVE EXCEPTION ENGINE - CORRECTED FULL CODE
# ============================================================

from pathlib import Path
from datetime import datetime
from getpass import getpass
import warnings

import mysql.connector
import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 250)
pd.set_option("display.float_format", lambda value: f"{value:,.2f}")


# ============================================================
# 1. DATABASE CONFIGURATION
# Password will be requested safely during execution
# ============================================================

MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = getpass("Enter MySQL password: ")
MYSQL_DATABASE = "enterprise_bi"


# ============================================================
# 2. BUSINESS THRESHOLDS
# ============================================================

REVENUE_RECONCILIATION_DIFFERENCE = 38_990_021.08
RETURN_RATE_THRESHOLD = 5.00
SALES_ACHIEVEMENT_THRESHOLD = 70.00
OUTSTANDING_DAYS_THRESHOLD = 180
CRITICAL_ANOMALY_SCORE = 90.00


# ============================================================
# 3. PROJECT PATHS
# ============================================================

CURRENT_FOLDER = Path(__file__).resolve().parent
PROJECT_FOLDER = CURRENT_FOLDER.parent

INVENTORY_FILE = (
    PROJECT_FOLDER
    / "Inventory_Analysis"
    / "Inventory_Product_Summary.csv"
)

SUPPLIER_FILE = (
    PROJECT_FOLDER
    / "Supplier_Analysis"
    / "Supplier_Performance_Summary.csv"
)

FORECAST_FILE = (
    PROJECT_FOLDER
    / "Forecasting_Analysis"
    / "Next_3_Month_Forecast.csv"
)

ANOMALY_FILE = (
    PROJECT_FOLDER
    / "Anomaly_Analysis"
    / "Top_Suspicious_Records.csv"
)

OUTPUT_FOLDER = PROJECT_FOLDER / "Exception_Report"
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

CSV_OUTPUT = (
    OUTPUT_FOLDER
    / "Executive_Exception_Table.csv"
)

EXCEL_OUTPUT = (
    OUTPUT_FOLDER
    / "Executive_Exception_Report.xlsx"
)

print("=" * 78)
print("EXECUTIVE EXCEPTION ENGINE STARTED")
print("=" * 78)


# ============================================================
# 4. CONNECT TO MYSQL
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
# 5. PRODUCT PROFITABILITY
# ============================================================

product_profit_query = """
SELECT
    Product_ID,
    MAX(Product_Name) AS Product_Name,
    MAX(Category) AS Category,
    SUM(Revenue) AS Revenue,
    SUM(Net_Profit) AS Net_Profit,

    SUM(Net_Profit) /
    NULLIF(SUM(Revenue), 0) * 100
        AS Profit_Margin_Percentage

FROM vw_sales_profitability

WHERE Product_ID IS NOT NULL

GROUP BY Product_ID;
"""

product_profit_df = pd.read_sql(
    product_profit_query,
    connection
)


# ============================================================
# 6. CORRECTED INVOICE-LEVEL OUTSTANDING QUERY
# Duplicate invoice rows are grouped before calculation
# ============================================================

outstanding_query = """
WITH Invoice_Base AS
(
    SELECT
        Invoice_ID,
        MAX(Customer_ID) AS Customer_ID,
        MAX(Invoice_Date) AS Invoice_Date,
        MAX(Due_Date) AS Due_Date,
        MAX(Invoice_Amount) AS Invoice_Amount

    FROM invoices

    WHERE Invoice_ID IS NOT NULL

    GROUP BY Invoice_ID
),

Payment_Summary AS
(
    SELECT
        Invoice_ID,
        SUM(Payment_Amount) AS Total_Paid

    FROM payments

    WHERE Invoice_ID IS NOT NULL

    GROUP BY Invoice_ID
)

SELECT
    ib.Invoice_ID,
    ib.Customer_ID,
    cm.Customer_Name,
    ib.Invoice_Date,
    ib.Due_Date,
    ib.Invoice_Amount,

    LEAST(
        COALESCE(ps.Total_Paid, 0),
        ib.Invoice_Amount
    ) AS Recognized_Payment,

    GREATEST(
        ib.Invoice_Amount
        - LEAST(
            COALESCE(ps.Total_Paid, 0),
            ib.Invoice_Amount
        ),
        0
    ) AS Outstanding_Amount,

    GREATEST(
        DATEDIFF(
            '2026-08-31',
            ib.Due_Date
        ),
        0
    ) AS Days_Overdue

FROM Invoice_Base ib

LEFT JOIN Payment_Summary ps
    ON ib.Invoice_ID = ps.Invoice_ID

LEFT JOIN customer_master cm
    ON ib.Customer_ID = cm.Customer_ID

WHERE ib.Due_Date IS NOT NULL;
"""

outstanding_df = pd.read_sql(
    outstanding_query,
    connection
)

connection.close()

print("Product profitability loaded.")
print("Unique invoice-level receivables loaded.")
print("MySQL connection closed.")


# ============================================================
# 7. VALIDATE AND LOAD ANALYSIS FILES
# ============================================================

required_files = [
    INVENTORY_FILE,
    SUPPLIER_FILE,
    FORECAST_FILE,
    ANOMALY_FILE
]

missing_files = [
    str(file_path)
    for file_path in required_files
    if not file_path.exists()
]

if missing_files:
    print("\nRequired files missing:")

    for file_path in missing_files:
        print(file_path)

    raise SystemExit(
        "\nRequired analysis files are missing."
    )

inventory_df = pd.read_csv(INVENTORY_FILE)
supplier_df = pd.read_csv(SUPPLIER_FILE)
forecast_df = pd.read_csv(FORECAST_FILE)
anomaly_df = pd.read_csv(ANOMALY_FILE)

print(f"Inventory rows loaded: {len(inventory_df):,}")
print(f"Supplier rows loaded: {len(supplier_df):,}")
print(f"Forecast rows loaded: {len(forecast_df):,}")
print(f"Anomaly rows loaded: {len(anomaly_df):,}")


# ============================================================
# 8. STANDARD EXCEPTION STRUCTURE
# ============================================================

exception_columns = [
    "Department",
    "Issue_Type",
    "Entity_ID",
    "Entity_Name",
    "Metric",
    "Actual_Value",
    "Expected_Value",
    "Variance",
    "Priority",
    "Root_Cause",
    "Financial_Impact",
    "Recommended_Action",
    "Source"
]

exception_frames = []


def add_exception_frame(dataframe):
    if dataframe is not None and not dataframe.empty:
        exception_frames.append(
            dataframe[exception_columns].copy()
        )


# ============================================================
# 9. NEGATIVE PRODUCT PROFIT
# ============================================================

negative_products = product_profit_df[
    product_profit_df["Net_Profit"] < 0
].copy()

negative_product_exceptions = pd.DataFrame(
    {
        "Department": "Sales / Product",
        "Issue_Type": "Negative Product Profit",
        "Entity_ID": negative_products["Product_ID"],
        "Entity_Name": negative_products["Product_Name"],
        "Metric": "Net Profit",
        "Actual_Value": negative_products["Net_Profit"],
        "Expected_Value": 0,
        "Variance": negative_products["Net_Profit"],
        "Priority": "Critical",
        "Root_Cause": (
            "Product cost, marketing allocation, discounts, "
            "returns and operating costs exceed revenue."
        ),
        "Financial_Impact": (
            negative_products["Net_Profit"].abs()
        ),
        "Recommended_Action": (
            "Review pricing, product cost, marketing allocation, "
            "discounts and return losses immediately."
        ),
        "Source": "Product Profitability Analysis"
    }
)

add_exception_frame(
    negative_product_exceptions
)


# ============================================================
# 10. REVENUE RECONCILIATION DIFFERENCE
# ============================================================

reconciliation_exception = pd.DataFrame(
    [
        {
            "Department": "Finance",
            "Issue_Type": (
                "Revenue Reconciliation Difference"
            ),
            "Entity_ID": "COMPANY",
            "Entity_Name": "Enterprise BI Company",
            "Metric": (
                "Management Revenue vs Reconciled Revenue"
            ),
            "Actual_Value": (
                REVENUE_RECONCILIATION_DIFFERENCE
            ),
            "Expected_Value": 0,
            "Variance": (
                REVENUE_RECONCILIATION_DIFFERENCE
            ),
            "Priority": "Critical",
            "Root_Cause": (
                "Management revenue differs because of discounts, "
                "returns, refunds, unmatched transactions and "
                "source-system differences."
            ),
            "Financial_Impact": (
                REVENUE_RECONCILIATION_DIFFERENCE
            ),
            "Recommended_Action": (
                "Reconcile orders, sales, returns, invoices and "
                "payments before publishing management revenue."
            ),
            "Source": "Revenue Reconciliation Analysis"
        }
    ]
)

add_exception_frame(
    reconciliation_exception
)


# ============================================================
# 11. CRITICAL INVENTORY PRODUCTS
# ============================================================

critical_inventory = inventory_df[
    inventory_df["Inventory_Status"]
    == "Critical Product"
].copy()

critical_inventory_exceptions = pd.DataFrame(
    {
        "Department": "Inventory / Operations",
        "Issue_Type": (
            "High Demand + Low Stock + Long Lead Time"
        ),
        "Entity_ID": critical_inventory["Product_ID"],
        "Entity_Name": critical_inventory["Product_Name"],
        "Metric": "Days Inventory",
        "Actual_Value": critical_inventory["Days_Inventory"],
        "Expected_Value": 30,
        "Variance": (
            critical_inventory["Days_Inventory"] - 30
        ),
        "Priority": "Critical",
        "Root_Cause": (
            "High demand, insufficient stock and long "
            "supplier lead time."
        ),
        "Financial_Impact": critical_inventory["Revenue"],
        "Recommended_Action": (
            "Create urgent purchase order, increase safety stock "
            "and reduce supplier lead time."
        ),
        "Source": "Inventory Analysis"
    }
)

add_exception_frame(
    critical_inventory_exceptions
)


# ============================================================
# 12. NEGATIVE INVENTORY
# ============================================================

negative_inventory = inventory_df[
    (
        inventory_df["Closing_Stock"] < 0
    )
    |
    (
        inventory_df["Closing_Stock_Value"] < 0
    )
].copy()

negative_inventory_exceptions = pd.DataFrame(
    {
        "Department": "Inventory / Data Quality",
        "Issue_Type": "Negative Inventory",
        "Entity_ID": negative_inventory["Product_ID"],
        "Entity_Name": negative_inventory["Product_Name"],
        "Metric": "Closing Stock",
        "Actual_Value": negative_inventory["Closing_Stock"],
        "Expected_Value": 0,
        "Variance": negative_inventory["Closing_Stock"],
        "Priority": "Critical",
        "Root_Cause": (
            "Inventory movements are missing, duplicated, "
            "incorrectly sequenced or not reconciled."
        ),
        "Financial_Impact": (
            negative_inventory[
                "Closing_Stock_Value"
            ].abs()
        ),
        "Recommended_Action": (
            "Reconcile physical stock with purchases, sales, "
            "returns and warehouse movements."
        ),
        "Source": "Inventory Analysis"
    }
)

add_exception_frame(
    negative_inventory_exceptions
)


# ============================================================
# 13. DEAD STOCK
# ============================================================

dead_stock = inventory_df[
    inventory_df["Inventory_Status"]
    == "Dead Stock"
].copy()

dead_stock_exceptions = pd.DataFrame(
    {
        "Department": "Inventory / Operations",
        "Issue_Type": "Dead Stock",
        "Entity_ID": dead_stock["Product_ID"],
        "Entity_Name": dead_stock["Product_Name"],
        "Metric": "Days Inventory",
        "Actual_Value": dead_stock["Days_Inventory"],
        "Expected_Value": 180,
        "Variance": (
            dead_stock["Days_Inventory"] - 180
        ),
        "Priority": "High",
        "Root_Cause": (
            "Low demand combined with high inventory and "
            "continued purchasing."
        ),
        "Financial_Impact": dead_stock[
            "Excess_Inventory_Value"
        ],
        "Recommended_Action": (
            "Stop replenishment and use clearance, bundle, "
            "transfer or supplier-return strategy."
        ),
        "Source": "Inventory Analysis"
    }
)

add_exception_frame(
    dead_stock_exceptions
)


# ============================================================
# 14. STOCKOUT RISK
# ============================================================

stockout_risk = inventory_df[
    inventory_df["Inventory_Status"]
    == "Stockout Risk"
].copy()

stockout_exceptions = pd.DataFrame(
    {
        "Department": "Inventory / Operations",
        "Issue_Type": "Stockout Risk",
        "Entity_ID": stockout_risk["Product_ID"],
        "Entity_Name": stockout_risk["Product_Name"],
        "Metric": "Stockout Rate %",
        "Actual_Value": stockout_risk[
            "Stockout_Rate_Percentage"
        ],
        "Expected_Value": 10,
        "Variance": (
            stockout_risk[
                "Stockout_Rate_Percentage"
            ] - 10
        ),
        "Priority": "High",
        "Root_Cause": (
            "Reorder point, safety stock or replenishment "
            "frequency is insufficient."
        ),
        "Financial_Impact": stockout_risk["Revenue"],
        "Recommended_Action": (
            "Increase safety stock and revise reorder point "
            "using demand and supplier lead time."
        ),
        "Source": "Inventory Analysis"
    }
)

add_exception_frame(
    stockout_exceptions
)


# ============================================================
# 15. HIGH PRODUCT RETURN RATE
# ============================================================

high_return_products = inventory_df[
    inventory_df["Return_Rate_Percentage"]
    > RETURN_RATE_THRESHOLD
].copy()

high_return_exceptions = pd.DataFrame(
    {
        "Department": "Sales / Quality",
        "Issue_Type": "High Product Return Rate",
        "Entity_ID": high_return_products["Product_ID"],
        "Entity_Name": high_return_products["Product_Name"],
        "Metric": "Return Rate %",
        "Actual_Value": high_return_products[
            "Return_Rate_Percentage"
        ],
        "Expected_Value": RETURN_RATE_THRESHOLD,
        "Variance": (
            high_return_products[
                "Return_Rate_Percentage"
            ] - RETURN_RATE_THRESHOLD
        ),
        "Priority": "High",
        "Root_Cause": (
            "Product quality, incorrect customer expectation, "
            "damaged delivery or description mismatch."
        ),
        "Financial_Impact": (
            high_return_products["Net_Profit"].abs()
        ),
        "Recommended_Action": (
            "Review return reasons, quality, packaging and "
            "product-description accuracy."
        ),
        "Source": "Product and Return Analysis"
    }
)

add_exception_frame(
    high_return_exceptions
)


# ============================================================
# 16. UNIQUE OUTSTANDING INVOICES > 180 DAYS
# ============================================================

outstanding_df["Days_Overdue"] = pd.to_numeric(
    outstanding_df["Days_Overdue"],
    errors="coerce"
).fillna(0)

outstanding_df["Outstanding_Amount"] = pd.to_numeric(
    outstanding_df["Outstanding_Amount"],
    errors="coerce"
).fillna(0)

overdue_accounts = outstanding_df[
    (
        outstanding_df["Days_Overdue"]
        > OUTSTANDING_DAYS_THRESHOLD
    )
    &
    (
        outstanding_df["Outstanding_Amount"] > 0
    )
].copy()

overdue_exceptions = pd.DataFrame(
    {
        "Department": "Finance / Collections",
        "Issue_Type": (
            "Outstanding Receivable > 180 Days"
        ),
        "Entity_ID": overdue_accounts["Invoice_ID"],
        "Entity_Name": (
            overdue_accounts["Customer_Name"]
            .fillna("Unknown Customer")
        ),
        "Metric": "Outstanding Amount",
        "Actual_Value": overdue_accounts[
            "Outstanding_Amount"
        ],
        "Expected_Value": 0,
        "Variance": overdue_accounts[
            "Outstanding_Amount"
        ],
        "Priority": "High",
        "Root_Cause": (
            "Delayed customer payment, weak collection follow-up "
            "or customer credit exposure."
        ),
        "Financial_Impact": overdue_accounts[
            "Outstanding_Amount"
        ],
        "Recommended_Action": (
            "Escalate collection, contact customer and review "
            "credit terms immediately."
        ),
        "Source": "Invoice and Payment Analysis"
    }
)

add_exception_frame(
    overdue_exceptions
)


# ============================================================
# 17. SUPPLIERS REQUIRING REVIEW
# ============================================================

supplier_issues = supplier_df[
    supplier_df["Review_Priority"].isin(
        ["Critical", "High"]
    )
].copy()

supplier_exceptions = pd.DataFrame(
    {
        "Department": "Procurement",
        "Issue_Type": "Supplier Performance Issue",
        "Entity_ID": supplier_issues["Supplier_ID"],
        "Entity_Name": supplier_issues["Supplier_Name"],
        "Metric": "Supplier Performance Score",
        "Actual_Value": supplier_issues[
            "Supplier_Performance_Score"
        ],
        "Expected_Value": 70,
        "Variance": (
            supplier_issues[
                "Supplier_Performance_Score"
            ] - 70
        ),
        "Priority": supplier_issues["Review_Priority"],
        "Root_Cause": (
            supplier_issues["Trend_Status"]
            .fillna("Low supplier performance")
        ),
        "Financial_Impact": supplier_issues[
            "Purchase_Value"
        ],
        "Recommended_Action": supplier_issues[
            "Recommended_Action"
        ],
        "Source": "Supplier Analytics"
    }
)

add_exception_frame(
    supplier_exceptions
)


# ============================================================
# 18. SALES TARGET ACHIEVEMENT BELOW 70%
# ============================================================

forecast_df["Month"] = pd.to_datetime(
    forecast_df["Month"],
    errors="coerce"
)

low_sales_achievement = forecast_df[
    forecast_df[
        "Revenue_Target_Achievement_Percentage"
    ] < SALES_ACHIEVEMENT_THRESHOLD
].copy()

target_exceptions = pd.DataFrame(
    {
        "Department": "Sales / Planning",
        "Issue_Type": "Sales Achievement Below 70%",
        "Entity_ID": (
            low_sales_achievement["Month"]
            .dt.strftime("%Y-%m")
        ),
        "Entity_Name": (
            low_sales_achievement["Month"]
            .dt.strftime("%B %Y")
        ),
        "Metric": "Revenue Target Achievement %",
        "Actual_Value": low_sales_achievement[
            "Revenue_Target_Achievement_Percentage"
        ],
        "Expected_Value": (
            SALES_ACHIEVEMENT_THRESHOLD
        ),
        "Variance": (
            low_sales_achievement[
                "Revenue_Target_Achievement_Percentage"
            ] - SALES_ACHIEVEMENT_THRESHOLD
        ),
        "Priority": "Medium",
        "Root_Cause": (
            "Forecasted revenue is materially below "
            "the monthly target."
        ),
        "Financial_Impact": (
            low_sales_achievement["Revenue_Target"]
            - low_sales_achievement["Revenue_Forecast"]
        ).clip(lower=0),
        "Recommended_Action": (
            "Review product, region and sales pipeline and "
            "prepare a monthly recovery plan."
        ),
        "Source": "Forecasting Analysis"
    }
)

add_exception_frame(
    target_exceptions
)


# ============================================================
# 19. CRITICAL ANOMALIES
# ============================================================

critical_anomalies = anomaly_df[
    (
        anomaly_df["Priority"] == "Critical"
    )
    |
    (
        anomaly_df["Anomaly_Score"]
        >= CRITICAL_ANOMALY_SCORE
    )
].copy()

anomaly_exceptions = pd.DataFrame(
    {
        "Department": (
            critical_anomalies["Dataset"]
            .fillna("Risk / Audit")
        ),
        "Issue_Type": "Critical Anomaly",
        "Entity_ID": (
            critical_anomalies["Record_ID"]
            .fillna("Unknown Record")
            .astype(str)
        ),
        "Entity_Name": (
            critical_anomalies["Dataset"]
            .fillna("Unknown Dataset")
            .astype(str)
            + " Record"
        ),
        "Metric": "Anomaly Score",
        "Actual_Value": critical_anomalies[
            "Anomaly_Score"
        ],
        "Expected_Value": 60,
        "Variance": (
            critical_anomalies["Anomaly_Score"]
            - 60
        ),
        "Priority": "Critical",
        "Root_Cause": critical_anomalies[
            "Anomaly_Reason"
        ],
        "Financial_Impact": (
            pd.to_numeric(
                critical_anomalies[
                    "Transaction_Amount"
                ],
                errors="coerce"
            )
            .fillna(0)
            .abs()
        ),
        "Recommended_Action": critical_anomalies[
            "Recommended_Action"
        ],
        "Source": "Multi-Factor Anomaly Detection"
    }
)

add_exception_frame(
    anomaly_exceptions
)


# ============================================================
# 20. CONSOLIDATE ALL EXCEPTIONS
# ============================================================

if not exception_frames:
    raise ValueError(
        "No exceptions generated."
    )

exception_table = pd.concat(
    exception_frames,
    ignore_index=True
)

for column in [
    "Actual_Value",
    "Expected_Value",
    "Variance",
    "Financial_Impact"
]:
    exception_table[column] = pd.to_numeric(
        exception_table[column],
        errors="coerce"
    ).fillna(0)

exception_table["Financial_Impact"] = (
    exception_table["Financial_Impact"]
    .abs()
)


# ============================================================
# 21. REMOVE EXACT DUPLICATE EXCEPTIONS
# ============================================================

exception_table = exception_table.drop_duplicates(
    subset=[
        "Issue_Type",
        "Entity_ID",
        "Metric"
    ],
    keep="first"
).reset_index(drop=True)


# ============================================================
# 22. SORT BY PRIORITY AND IMPACT
# ============================================================

priority_order = {
    "Critical": 1,
    "High": 2,
    "Medium": 3,
    "Low": 4
}

exception_table["Priority_Order"] = (
    exception_table["Priority"]
    .map(priority_order)
    .fillna(5)
)

exception_table = exception_table.sort_values(
    [
        "Priority_Order",
        "Financial_Impact"
    ],
    ascending=[True, False]
).reset_index(drop=True)

exception_table.insert(
    0,
    "Issue_ID",
    [
        f"ISSUE-{number:05d}"
        for number in range(
            1,
            len(exception_table) + 1
        )
    ]
)

exception_table["Report_Date"] = (
    datetime.now().date()
)

exception_table = exception_table.drop(
    columns=["Priority_Order"]
)


# ============================================================
# 23. CREATE EXECUTIVE SUMMARIES
# ============================================================

priority_summary = (
    exception_table
    .groupby("Priority")
    .agg(
        Issue_Count=("Issue_ID", "count"),
        Gross_Exception_Exposure=(
            "Financial_Impact",
            "sum"
        )
    )
    .reset_index()
)

priority_summary["Priority_Order"] = (
    priority_summary["Priority"]
    .map(priority_order)
)

priority_summary = (
    priority_summary
    .sort_values("Priority_Order")
    .drop(columns=["Priority_Order"])
)

department_summary = (
    exception_table
    .groupby("Department")
    .agg(
        Issue_Count=("Issue_ID", "count"),
        Critical_Issues=(
            "Priority",
            lambda values: (
                values == "Critical"
            ).sum()
        ),
        High_Issues=(
            "Priority",
            lambda values: (
                values == "High"
            ).sum()
        ),
        Gross_Exception_Exposure=(
            "Financial_Impact",
            "sum"
        )
    )
    .reset_index()
    .sort_values(
        "Gross_Exception_Exposure",
        ascending=False
    )
)

issue_type_summary = (
    exception_table
    .groupby("Issue_Type")
    .agg(
        Issue_Count=("Issue_ID", "count"),
        Critical_Issues=(
            "Priority",
            lambda values: (
                values == "Critical"
            ).sum()
        ),
        Gross_Exception_Exposure=(
            "Financial_Impact",
            "sum"
        )
    )
    .reset_index()
    .sort_values(
        "Gross_Exception_Exposure",
        ascending=False
    )
)

executive_summary = pd.DataFrame(
    {
        "Metric": [
            "Total Exceptions",
            "Critical Exceptions",
            "High-Priority Exceptions",
            "Medium-Priority Exceptions",
            "Gross Exception Exposure",
            "Negative-Profit Products",
            "Critical Inventory Products",
            "Negative Inventory Products",
            "Unique Overdue Invoices >180 Days",
            "Total Overdue Amount >180 Days",
            "Suppliers Requiring Review",
            "Critical Anomalies"
        ],
        "Value": [
            len(exception_table),
            (
                exception_table["Priority"]
                == "Critical"
            ).sum(),
            (
                exception_table["Priority"]
                == "High"
            ).sum(),
            (
                exception_table["Priority"]
                == "Medium"
            ).sum(),
            exception_table[
                "Financial_Impact"
            ].sum(),
            len(negative_products),
            len(critical_inventory),
            len(negative_inventory),
            overdue_accounts[
                "Invoice_ID"
            ].nunique(),
            overdue_accounts[
                "Outstanding_Amount"
            ].sum(),
            len(supplier_issues),
            len(critical_anomalies)
        ]
    }
)


# ============================================================
# 24. ROUND VALUES
# ============================================================

numeric_columns = [
    "Actual_Value",
    "Expected_Value",
    "Variance",
    "Financial_Impact"
]

exception_table[numeric_columns] = (
    exception_table[numeric_columns]
    .round(2)
)


# ============================================================
# 25. SAVE CSV
# ============================================================

exception_table.to_csv(
    CSV_OUTPUT,
    index=False
)


# ============================================================
# 26. SAVE EXCEL
# ============================================================

with pd.ExcelWriter(
    EXCEL_OUTPUT,
    engine="openpyxl"
) as writer:

    executive_summary.to_excel(
        writer,
        sheet_name="Executive_Summary",
        index=False
    )

    priority_summary.to_excel(
        writer,
        sheet_name="Priority_Summary",
        index=False
    )

    department_summary.to_excel(
        writer,
        sheet_name="Department_Summary",
        index=False
    )

    issue_type_summary.to_excel(
        writer,
        sheet_name="Issue_Type_Summary",
        index=False
    )

    exception_table.to_excel(
        writer,
        sheet_name="Exception_Table",
        index=False
    )

    workbook = writer.book

    for worksheet in workbook.worksheets:
        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions

        for column_cells in worksheet.columns:
            maximum_length = 0
            column_letter = column_cells[0].column_letter

            for cell in column_cells:
                try:
                    maximum_length = max(
                        maximum_length,
                        len(str(cell.value))
                    )
                except Exception:
                    pass

            worksheet.column_dimensions[
                column_letter
            ].width = min(
                maximum_length + 2,
                60
            )


# ============================================================
# 27. PRINT FINAL RESULTS
# ============================================================

print("\n" + "=" * 78)
print("EXECUTIVE EXCEPTION SUMMARY")
print("=" * 78)

print(
    executive_summary.to_string(
        index=False
    )
)

print("\n" + "=" * 78)
print("PRIORITY SUMMARY")
print("=" * 78)

print(
    priority_summary.to_string(
        index=False
    )
)

print("\n" + "=" * 78)
print("TOP 20 CRITICAL EXCEPTIONS")
print("=" * 78)

display_columns = [
    "Issue_ID",
    "Issue_Type",
    "Department",
    "Entity_ID",
    "Entity_Name",
    "Actual_Value",
    "Expected_Value",
    "Variance",
    "Priority",
    "Financial_Impact",
    "Recommended_Action"
]

print(
    exception_table[
        exception_table["Priority"]
        == "Critical"
    ][display_columns]
    .head(20)
    .to_string(index=False)
)

print("\n" + "=" * 78)
print("IMPORTANT NOTE")
print("=" * 78)

print(
    "Gross Exception Exposure includes overlapping business "
    "issues. It should not be treated as unique company loss."
)

print("\n" + "=" * 78)
print("EXECUTIVE EXCEPTION ENGINE COMPLETED SUCCESSFULLY")
print("=" * 78)

print(f"\nCSV saved in:\n{CSV_OUTPUT}")
print(f"\nExcel report saved in:\n{EXCEL_OUTPUT}")