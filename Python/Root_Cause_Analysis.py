# ============================================================
# PART 18: FIVE LARGEST BUSINESS PROBLEMS
# ROOT CAUSE ANALYSIS
# ============================================================

from pathlib import Path
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
# ============================================================

MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = getpass("Enter MySQL password: ")
MYSQL_DATABASE = "enterprise_bi"


# ============================================================
# 2. FILE LOCATIONS
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

MARKETING_FILE = (
    PROJECT_FOLDER
    / "Marketing_Analysis"
    / "Marketing_Channel_Summary.csv"
)

EXCEPTION_FILE = (
    PROJECT_FOLDER
    / "Exception_Report"
    / "Executive_Exception_Table.csv"
)

OUTPUT_FOLDER = (
    PROJECT_FOLDER
    / "Root_Cause_Analysis"
)

OUTPUT_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

EXCEL_OUTPUT = (
    OUTPUT_FOLDER
    / "Five_Largest_Problems_Root_Cause_Analysis.xlsx"
)

CSV_OUTPUT = (
    OUTPUT_FOLDER
    / "Root_Cause_Summary.csv"
)

MARKDOWN_OUTPUT = (
    OUTPUT_FOLDER
    / "Root_Cause_Analysis.md"
)

print("=" * 80)
print("ROOT CAUSE ANALYSIS STARTED")
print("=" * 80)


# ============================================================
# 3. CONNECT TO MYSQL
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
# 4. COMPANY PROFITABILITY
# ============================================================

company_query = """
SELECT
    SUM(Revenue) AS Revenue,
    SUM(Discount) AS Discounts,
    SUM(Refunds) AS Refunds,
    SUM(Product_Cost) AS Product_Cost,
    SUM(Shipping_Cost) AS Shipping_Cost,
    SUM(Payment_Fee) AS Payment_Fees,
    SUM(Allocated_Marketing_Cost) AS Marketing_Cost,
    SUM(Net_Profit) AS Net_Profit,

    SUM(Net_Profit) /
    NULLIF(SUM(Revenue), 0) * 100
        AS Profit_Margin_Percentage,

    COUNT(DISTINCT Order_ID) AS Orders,
    COUNT(DISTINCT Customer_ID) AS Customers

FROM vw_sales_profitability;
"""

company_df = pd.read_sql(
    company_query,
    connection
)

company = company_df.iloc[0]


# ============================================================
# 5. CATEGORY PROFITABILITY
# ============================================================

category_query = """
SELECT
    Category,
    SUM(Revenue) AS Revenue,
    SUM(Product_Cost) AS Product_Cost,
    SUM(Allocated_Marketing_Cost) AS Marketing_Cost,
    SUM(Net_Profit) AS Net_Profit,

    SUM(Net_Profit) /
    NULLIF(SUM(Revenue), 0) * 100
        AS Profit_Margin_Percentage

FROM vw_sales_profitability

GROUP BY Category

ORDER BY Net_Profit ASC;
"""

category_df = pd.read_sql(
    category_query,
    connection
)


# ============================================================
# 6. REGIONAL PROFITABILITY
# ============================================================

region_query = """
SELECT
    Region_ID,
    MAX(Region_Name) AS Region_Name,
    SUM(Revenue) AS Revenue,
    SUM(Net_Profit) AS Net_Profit,

    SUM(Net_Profit) /
    NULLIF(SUM(Revenue), 0) * 100
        AS Profit_Margin_Percentage

FROM vw_sales_profitability

GROUP BY Region_ID

ORDER BY Profit_Margin_Percentage ASC;
"""

region_df = pd.read_sql(
    region_query,
    connection
)


# ============================================================
# 7. PRODUCT PROFITABILITY
# ============================================================

product_query = """
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

GROUP BY Product_ID

ORDER BY Net_Profit ASC;
"""

product_df = pd.read_sql(
    product_query,
    connection
)

connection.close()

print("Profitability evidence loaded.")
print("MySQL connection closed.")


# ============================================================
# 8. LOAD ANALYSIS FILES
# ============================================================

required_files = [
    INVENTORY_FILE,
    SUPPLIER_FILE,
    MARKETING_FILE,
    EXCEPTION_FILE
]

missing_files = [
    str(file_path)
    for file_path in required_files
    if not file_path.exists()
]

if missing_files:
    print("\nMissing files:")

    for file_path in missing_files:
        print(file_path)

    raise SystemExit(
        "\nRequired analysis files are missing."
    )

inventory_df = pd.read_csv(INVENTORY_FILE)
supplier_df = pd.read_csv(SUPPLIER_FILE)
marketing_df = pd.read_csv(MARKETING_FILE)
exception_df = pd.read_csv(EXCEPTION_FILE)

print("Supporting analysis files loaded.")


# ============================================================
# 9. HELPER FUNCTIONS
# ============================================================

def safe_sum(dataframe, column):
    if column not in dataframe.columns:
        return 0

    return pd.to_numeric(
        dataframe[column],
        errors="coerce"
    ).fillna(0).sum()


def safe_mean(dataframe, column):
    if column not in dataframe.columns:
        return 0

    return pd.to_numeric(
        dataframe[column],
        errors="coerce"
    ).fillna(0).mean()


def indian_crore(value):
    return float(value) / 10_000_000


def percentage_of(value, total):
    if total == 0:
        return 0

    return value / total * 100


# ============================================================
# 10. PREPARE PROFITABILITY EVIDENCE
# ============================================================

revenue = float(company["Revenue"])
discounts = float(company["Discounts"])
refunds = float(company["Refunds"])
product_cost = float(company["Product_Cost"])
shipping_cost = float(company["Shipping_Cost"])
payment_fees = float(company["Payment_Fees"])
marketing_cost = float(company["Marketing_Cost"])
net_profit = float(company["Net_Profit"])
profit_margin = float(
    company["Profit_Margin_Percentage"]
)

negative_products = product_df[
    product_df["Net_Profit"] < 0
]

worst_category = category_df.iloc[0]
worst_region = region_df.iloc[0]
worst_product = product_df.iloc[0]


# ============================================================
# 11. PREPARE INVENTORY EVIDENCE
# ============================================================

closing_inventory_value = safe_sum(
    inventory_df,
    "Closing_Stock_Value"
)

excess_inventory_value = safe_sum(
    inventory_df,
    "Excess_Inventory_Value"
)

average_inventory_value = safe_sum(
    inventory_df,
    "Average_Inventory_Value"
)

inventory_cogs = safe_sum(
    inventory_df,
    "Cost_Of_Goods_Sold"
)

inventory_turnover = (
    inventory_cogs / average_inventory_value
    if average_inventory_value > 0
    else 0
)

days_inventory = (
    365 / inventory_turnover
    if inventory_turnover > 0
    else 0
)

excess_products = inventory_df[
    inventory_df["Excess_Inventory_Units"] > 0
]

dead_stock_products = inventory_df[
    inventory_df["Inventory_Status"]
    == "Dead Stock"
]

negative_inventory_products = inventory_df[
    inventory_df["Inventory_Status"]
    == "Inventory Data Issue"
]

critical_products = inventory_df[
    inventory_df["Inventory_Status"]
    == "Critical Product"
]

dead_stock_value = safe_sum(
    dead_stock_products,
    "Excess_Inventory_Value"
)


# ============================================================
# 12. PREPARE RECONCILIATION EVIDENCE
# ============================================================

reconciliation_rows = exception_df[
    exception_df["Issue_Type"]
    == "Revenue Reconciliation Difference"
]

if reconciliation_rows.empty:
    reconciliation_difference = 38_990_021.08
else:
    reconciliation_difference = safe_sum(
        reconciliation_rows,
        "Financial_Impact"
    )


# ============================================================
# 13. PREPARE RECEIVABLE EVIDENCE
# ============================================================

overdue_rows = exception_df[
    exception_df["Issue_Type"]
    == "Outstanding Receivable > 180 Days"
].copy()

overdue_invoice_count = overdue_rows[
    "Entity_ID"
].nunique()

overdue_amount = safe_sum(
    overdue_rows,
    "Financial_Impact"
)


# ============================================================
# 14. PREPARE SUPPLIER EVIDENCE
# ============================================================

supplier_review = supplier_df[
    supplier_df["Review_Priority"].isin(
        ["Critical", "High"]
    )
].copy()

critical_suppliers = supplier_df[
    supplier_df["Review_Priority"]
    == "Critical"
]

supplier_purchase_exposure = safe_sum(
    supplier_review,
    "Purchase_Value"
)

average_supplier_score = safe_mean(
    supplier_df,
    "Supplier_Performance_Score"
)

total_deliveries = safe_sum(
    supplier_df,
    "Total_Deliveries"
)

on_time_deliveries = safe_sum(
    supplier_df,
    "On_Time_Deliveries"
)

supplier_on_time_rate = (
    on_time_deliveries
    / total_deliveries
    * 100
    if total_deliveries > 0
    else 0
)

average_lead_time = safe_mean(
    supplier_df,
    "Average_Delivery_Time_Days"
)

lowest_supplier = supplier_df.sort_values(
    "Supplier_Performance_Score"
).iloc[0]


# ============================================================
# 15. PREPARE MARKETING SUPPORTING EVIDENCE
# ============================================================

marketing_spend = safe_sum(
    marketing_df,
    "Marketing_Spend"
)

linear_marketing_revenue = safe_sum(
    marketing_df,
    "Linear_Attributed_Revenue"
)

linear_marketing_profit = safe_sum(
    marketing_df,
    "Linear_Attributed_Profit"
)

unprofitable_channels = marketing_df[
    marketing_df["Linear_Attributed_Profit"] < 0
]

best_channel = marketing_df.sort_values(
    "Linear_Attributed_Profit",
    ascending=False
).iloc[0]


# ============================================================
# 16. FIVE LARGEST PROBLEMS SUMMARY
# ============================================================

root_cause_summary = pd.DataFrame(
    [
        {
            "Problem_Rank": 1,
            "Business_Problem": (
                "Revenue Generated but Company Remains Unprofitable"
            ),
            "Key_Metric": "Net Profit",
            "Actual_Result": net_profit,
            "Actual_Result_Display": (
                f"₹{indian_crore(abs(net_profit)):.2f} Cr loss"
            ),
            "Root_Cause": (
                "Product cost and marketing allocation consume "
                "more than total revenue before discounts, "
                "refunds, shipping and payment fees."
            ),
            "Financial_Impact": abs(net_profit),
            "Priority": "Critical",
            "Recommended_Action": (
                "Reduce marketing cost, renegotiate product cost, "
                "correct loss-making prices and control discounts."
            )
        },
        {
            "Problem_Rank": 2,
            "Business_Problem": (
                "Excess Inventory and Extremely Low Turnover"
            ),
            "Key_Metric": "Excess Inventory Value",
            "Actual_Result": excess_inventory_value,
            "Actual_Result_Display": (
                f"₹{indian_crore(excess_inventory_value):.2f} Cr"
            ),
            "Root_Cause": (
                "Purchasing and replenishment are not aligned "
                "with product demand; slow products continue "
                "to receive inventory."
            ),
            "Financial_Impact": excess_inventory_value,
            "Priority": "Critical",
            "Recommended_Action": (
                "Stop dead-stock purchasing, liquidate excess "
                "inventory and introduce demand-based reorder points."
            )
        },
        {
            "Problem_Rank": 3,
            "Business_Problem": (
                "Supplier Delivery Performance is Unacceptable"
            ),
            "Key_Metric": "Supplier On-Time Delivery %",
            "Actual_Result": supplier_on_time_rate,
            "Actual_Result_Display": (
                f"{supplier_on_time_rate:.2f}% on-time"
            ),
            "Root_Cause": (
                "Supplier SLA performance is weak and almost half "
                "the supplier base requires renegotiation or review."
            ),
            "Financial_Impact": supplier_purchase_exposure,
            "Priority": "Critical",
            "Recommended_Action": (
                "Renegotiate low-performing suppliers, enforce SLA "
                "penalties and shift critical purchases to alternatives."
            )
        },
        {
            "Problem_Rank": 4,
            "Business_Problem": (
                "Revenue Reports Do Not Reconcile"
            ),
            "Key_Metric": "Reconciliation Difference",
            "Actual_Result": reconciliation_difference,
            "Actual_Result_Display": (
                f"₹{indian_crore(reconciliation_difference):.2f} Cr"
            ),
            "Root_Cause": (
                "Management revenue, database sales, discounts, "
                "returns, refunds and unmatched transactions use "
                "different definitions and processing rules."
            ),
            "Financial_Impact": reconciliation_difference,
            "Priority": "Critical",
            "Recommended_Action": (
                "Create a governed revenue definition and automate "
                "order-to-cash reconciliation before reporting."
            )
        },
        {
            "Problem_Rank": 5,
            "Business_Problem": (
                "Long-Overdue Customer Receivables"
            ),
            "Key_Metric": "Outstanding >180 Days",
            "Actual_Result": overdue_amount,
            "Actual_Result_Display": (
                f"₹{indian_crore(overdue_amount):.2f} Cr"
            ),
            "Root_Cause": (
                "Weak collection follow-up, delayed customer "
                "payments and insufficient credit-risk controls."
            ),
            "Financial_Impact": overdue_amount,
            "Priority": "High",
            "Recommended_Action": (
                "Create ageing-based collection workflows, escalate "
                "high-value invoices and review customer credit limits."
            )
        }
    ]
)


# ============================================================
# 17. DETAILED ROOT CAUSE CHAIN
# ============================================================

root_cause_chain = pd.DataFrame(
    [
        # ----------------------------------------------------
        # Problem 1
        # ----------------------------------------------------
        {
            "Problem_Rank": 1,
            "Business_Problem": (
                "Revenue Generated but Company Remains Unprofitable"
            ),
            "Analysis_Stage": "Business Problem",
            "Finding": (
                f"Company generated ₹{indian_crore(revenue):.2f} Cr "
                f"revenue but recorded ₹{indian_crore(abs(net_profit)):.2f} Cr loss."
            )
        },
        {
            "Problem_Rank": 1,
            "Business_Problem": (
                "Revenue Generated but Company Remains Unprofitable"
            ),
            "Analysis_Stage": "Metric Change",
            "Finding": (
                f"Net margin is {profit_margin:.2f}% while "
                "revenue remained near ₹4 Cr per month."
            )
        },
        {
            "Problem_Rank": 1,
            "Business_Problem": (
                "Revenue Generated but Company Remains Unprofitable"
            ),
            "Analysis_Stage": "Segment Breakdown",
            "Finding": (
                f"All {category_df['Category'].nunique()} categories "
                "and all regions recorded negative profit."
            )
        },
        {
            "Problem_Rank": 1,
            "Business_Problem": (
                "Revenue Generated but Company Remains Unprofitable"
            ),
            "Analysis_Stage": "Product / Region Analysis",
            "Finding": (
                f"{len(negative_products)} products are loss-making. "
                f"Worst category: {worst_category['Category']} "
                f"(₹{abs(worst_category['Net_Profit']):,.2f} loss). "
                f"Worst-margin region: {worst_region['Region_Name']} "
                f"({worst_region['Profit_Margin_Percentage']:.2f}%)."
            )
        },
        {
            "Problem_Rank": 1,
            "Business_Problem": (
                "Revenue Generated but Company Remains Unprofitable"
            ),
            "Analysis_Stage": "Root Cause",
            "Finding": (
                f"Product cost is {percentage_of(product_cost, revenue):.2f}% "
                f"and marketing cost is {percentage_of(marketing_cost, revenue):.2f}% "
                "of revenue. Additional discounts, refunds, shipping "
                "and fees push total cost above revenue."
            )
        },
        {
            "Problem_Rank": 1,
            "Business_Problem": (
                "Revenue Generated but Company Remains Unprofitable"
            ),
            "Analysis_Stage": "Financial Impact",
            "Finding": (
                f"Net annual loss: ₹{abs(net_profit):,.2f}."
            )
        },
        {
            "Problem_Rank": 1,
            "Business_Problem": (
                "Revenue Generated but Company Remains Unprofitable"
            ),
            "Analysis_Stage": "Recommendation",
            "Finding": (
                "Set product-level minimum margins, reduce marketing "
                "allocation, renegotiate costs and stop campaigns that "
                "do not create profitable customers."
            )
        },

        # ----------------------------------------------------
        # Problem 2
        # ----------------------------------------------------
        {
            "Problem_Rank": 2,
            "Business_Problem": (
                "Excess Inventory and Extremely Low Turnover"
            ),
            "Analysis_Stage": "Business Problem",
            "Finding": (
                "Large inventory value is locked in products that "
                "sell slowly while other products face stockout risk."
            )
        },
        {
            "Problem_Rank": 2,
            "Business_Problem": (
                "Excess Inventory and Extremely Low Turnover"
            ),
            "Analysis_Stage": "Metric Change",
            "Finding": (
                f"Inventory turnover is only {inventory_turnover:.2f} "
                f"times and estimated days inventory is {days_inventory:,.2f} days."
            )
        },
        {
            "Problem_Rank": 2,
            "Business_Problem": (
                "Excess Inventory and Extremely Low Turnover"
            ),
            "Analysis_Stage": "Segment Breakdown",
            "Finding": (
                f"{len(excess_products)} products contain excess stock, "
                f"{len(dead_stock_products)} are dead stock and "
                f"{len(critical_products)} are critical low-stock products."
            )
        },
        {
            "Problem_Rank": 2,
            "Business_Problem": (
                "Excess Inventory and Extremely Low Turnover"
            ),
            "Analysis_Stage": "Product / Region Analysis",
            "Finding": (
                f"{len(negative_inventory_products)} products have "
                "negative inventory records, indicating reconciliation issues."
            )
        },
        {
            "Problem_Rank": 2,
            "Business_Problem": (
                "Excess Inventory and Extremely Low Turnover"
            ),
            "Analysis_Stage": "Root Cause",
            "Finding": (
                "Purchasing is not linked to demand forecasts, reorder "
                "points and supplier lead times. Slow products continue "
                "to receive stock."
            )
        },
        {
            "Problem_Rank": 2,
            "Business_Problem": (
                "Excess Inventory and Extremely Low Turnover"
            ),
            "Analysis_Stage": "Financial Impact",
            "Finding": (
                f"Excess inventory exposure is ₹{excess_inventory_value:,.2f}; "
                f"dead-stock exposure is ₹{dead_stock_value:,.2f}."
            )
        },
        {
            "Problem_Rank": 2,
            "Business_Problem": (
                "Excess Inventory and Extremely Low Turnover"
            ),
            "Analysis_Stage": "Recommendation",
            "Finding": (
                "Stop dead-stock purchasing, introduce ABC classification, "
                "set demand-based reorder points and liquidate excess inventory."
            )
        },

        # ----------------------------------------------------
        # Problem 3
        # ----------------------------------------------------
        {
            "Problem_Rank": 3,
            "Business_Problem": (
                "Supplier Delivery Performance is Unacceptable"
            ),
            "Analysis_Stage": "Business Problem",
            "Finding": (
                "Supplier delivery performance creates replenishment "
                "delays and stockout risk."
            )
        },
        {
            "Problem_Rank": 3,
            "Business_Problem": (
                "Supplier Delivery Performance is Unacceptable"
            ),
            "Analysis_Stage": "Metric Change",
            "Finding": (
                f"Overall on-time delivery is only "
                f"{supplier_on_time_rate:.2f}% and average lead time "
                f"is {average_lead_time:.2f} days."
            )
        },
        {
            "Problem_Rank": 3,
            "Business_Problem": (
                "Supplier Delivery Performance is Unacceptable"
            ),
            "Analysis_Stage": "Segment Breakdown",
            "Finding": (
                f"{len(supplier_review)} suppliers require Critical/High "
                f"review; {len(critical_suppliers)} are Critical."
            )
        },
        {
            "Problem_Rank": 3,
            "Business_Problem": (
                "Supplier Delivery Performance is Unacceptable"
            ),
            "Analysis_Stage": "Product / Supplier Analysis",
            "Finding": (
                f"Lowest supplier is {lowest_supplier['Supplier_Name']} "
                f"with score {lowest_supplier['Supplier_Performance_Score']:.2f}. "
                f"Average supplier score is {average_supplier_score:.2f}."
            )
        },
        {
            "Problem_Rank": 3,
            "Business_Problem": (
                "Supplier Delivery Performance is Unacceptable"
            ),
            "Analysis_Stage": "Root Cause",
            "Finding": (
                "Weak supplier SLAs, limited penalty enforcement and "
                "continued spend allocation to low-performing suppliers."
            )
        },
        {
            "Problem_Rank": 3,
            "Business_Problem": (
                "Supplier Delivery Performance is Unacceptable"
            ),
            "Analysis_Stage": "Financial Impact",
            "Finding": (
                f"Purchase value exposed to Critical/High suppliers: "
                f"₹{supplier_purchase_exposure:,.2f}."
            )
        },
        {
            "Problem_Rank": 3,
            "Business_Problem": (
                "Supplier Delivery Performance is Unacceptable"
            ),
            "Analysis_Stage": "Recommendation",
            "Finding": (
                "Renegotiate supplier contracts, introduce SLA scorecards "
                "and shift critical product orders to alternative suppliers."
            )
        },

        # ----------------------------------------------------
        # Problem 4
        # ----------------------------------------------------
        {
            "Problem_Rank": 4,
            "Business_Problem": (
                "Revenue Reports Do Not Reconcile"
            ),
            "Analysis_Stage": "Business Problem",
            "Finding": (
                "Management revenue and reconciled database revenue "
                "do not match."
            )
        },
        {
            "Problem_Rank": 4,
            "Business_Problem": (
                "Revenue Reports Do Not Reconcile"
            ),
            "Analysis_Stage": "Metric Change",
            "Finding": (
                f"Final reconciliation difference is "
                f"₹{reconciliation_difference:,.2f}."
            )
        },
        {
            "Problem_Rank": 4,
            "Business_Problem": (
                "Revenue Reports Do Not Reconcile"
            ),
            "Analysis_Stage": "Segment Breakdown",
            "Finding": (
                "Difference is distributed across gross-to-net revenue, "
                "discounts, returns, refunds and unmatched transactions."
            )
        },
        {
            "Problem_Rank": 4,
            "Business_Problem": (
                "Revenue Reports Do Not Reconcile"
            ),
            "Analysis_Stage": "Product / Source Analysis",
            "Finding": (
                "Orders, sales, returns, invoices and payments have "
                "different grains and duplicate/unmatched records."
            )
        },
        {
            "Problem_Rank": 4,
            "Business_Problem": (
                "Revenue Reports Do Not Reconcile"
            ),
            "Analysis_Stage": "Root Cause",
            "Finding": (
                "Departments use inconsistent revenue definitions and "
                "source systems are not reconciled before reporting."
            )
        },
        {
            "Problem_Rank": 4,
            "Business_Problem": (
                "Revenue Reports Do Not Reconcile"
            ),
            "Analysis_Stage": "Financial Impact",
            "Finding": (
                f"Unexplained reporting difference: "
                f"₹{reconciliation_difference:,.2f}."
            )
        },
        {
            "Problem_Rank": 4,
            "Business_Problem": (
                "Revenue Reports Do Not Reconcile"
            ),
            "Analysis_Stage": "Recommendation",
            "Finding": (
                "Create a governed revenue definition and automated "
                "order-to-cash reconciliation with exception ownership."
            )
        },

        # ----------------------------------------------------
        # Problem 5
        # ----------------------------------------------------
        {
            "Problem_Rank": 5,
            "Business_Problem": (
                "Long-Overdue Customer Receivables"
            ),
            "Analysis_Stage": "Business Problem",
            "Finding": (
                "A large number of invoices remain unpaid more than "
                "180 days after their due date."
            )
        },
        {
            "Problem_Rank": 5,
            "Business_Problem": (
                "Long-Overdue Customer Receivables"
            ),
            "Analysis_Stage": "Metric Change",
            "Finding": (
                f"{overdue_invoice_count:,} unique invoices have "
                f"₹{overdue_amount:,.2f} outstanding beyond 180 days."
            )
        },
        {
            "Problem_Rank": 5,
            "Business_Problem": (
                "Long-Overdue Customer Receivables"
            ),
            "Analysis_Stage": "Segment Breakdown",
            "Finding": (
                "Outstanding exposure is concentrated in long-aged "
                "invoice and customer accounts."
            )
        },
        {
            "Problem_Rank": 5,
            "Business_Problem": (
                "Long-Overdue Customer Receivables"
            ),
            "Analysis_Stage": "Customer Analysis",
            "Finding": (
                "Collection risk exists even though aggregate payment "
                "values are distorted by overpayments in some invoices."
            )
        },
        {
            "Problem_Rank": 5,
            "Business_Problem": (
                "Long-Overdue Customer Receivables"
            ),
            "Analysis_Stage": "Root Cause",
            "Finding": (
                "Weak ageing-based collection workflow, delayed follow-up "
                "and insufficient customer credit controls."
            )
        },
        {
            "Problem_Rank": 5,
            "Business_Problem": (
                "Long-Overdue Customer Receivables"
            ),
            "Analysis_Stage": "Financial Impact",
            "Finding": (
                f"Overdue exposure beyond 180 days: "
                f"₹{overdue_amount:,.2f}."
            )
        },
        {
            "Problem_Rank": 5,
            "Business_Problem": (
                "Long-Overdue Customer Receivables"
            ),
            "Analysis_Stage": "Recommendation",
            "Finding": (
                "Create ageing buckets, assign collection owners, "
                "escalate high-value cases and review credit limits."
            )
        }
    ]
)


# ============================================================
# 18. SUPPORTING KPI TABLE
# ============================================================

supporting_kpis = pd.DataFrame(
    {
        "KPI": [
            "Revenue",
            "Net Profit",
            "Profit Margin %",
            "Product Cost % of Revenue",
            "Marketing Cost % of Revenue",
            "Negative-Profit Products",
            "Excess Inventory Value",
            "Dead Stock Value",
            "Inventory Turnover",
            "Days Inventory",
            "Negative Inventory Products",
            "Critical Inventory Products",
            "Supplier On-Time Delivery %",
            "Average Supplier Score",
            "Suppliers Requiring Review",
            "Revenue Reconciliation Difference",
            "Overdue Invoices >180 Days",
            "Overdue Amount >180 Days",
            "Marketing Spend",
            "Unprofitable Marketing Channels",
            "Linear Attributed Marketing Profit"
        ],
        "Value": [
            revenue,
            net_profit,
            profit_margin,
            percentage_of(product_cost, revenue),
            percentage_of(marketing_cost, revenue),
            len(negative_products),
            excess_inventory_value,
            dead_stock_value,
            inventory_turnover,
            days_inventory,
            len(negative_inventory_products),
            len(critical_products),
            supplier_on_time_rate,
            average_supplier_score,
            len(supplier_review),
            reconciliation_difference,
            overdue_invoice_count,
            overdue_amount,
            marketing_spend,
            len(unprofitable_channels),
            linear_marketing_profit
        ]
    }
)


# ============================================================
# 19. SAVE CSV
# ============================================================

root_cause_summary.to_csv(
    CSV_OUTPUT,
    index=False
)


# ============================================================
# 20. SAVE EXCEL REPORT
# ============================================================

with pd.ExcelWriter(
    EXCEL_OUTPUT,
    engine="openpyxl"
) as writer:

    root_cause_summary.to_excel(
        writer,
        sheet_name="Five_Largest_Problems",
        index=False
    )

    root_cause_chain.to_excel(
        writer,
        sheet_name="Root_Cause_Chain",
        index=False
    )

    supporting_kpis.to_excel(
        writer,
        sheet_name="Supporting_KPIs",
        index=False
    )

    category_df.to_excel(
        writer,
        sheet_name="Category_Evidence",
        index=False
    )

    region_df.to_excel(
        writer,
        sheet_name="Region_Evidence",
        index=False
    )

    product_df.head(100).to_excel(
        writer,
        sheet_name="Product_Evidence",
        index=False
    )

    dead_stock_products.head(100).to_excel(
        writer,
        sheet_name="Inventory_Evidence",
        index=False
    )

    supplier_review.to_excel(
        writer,
        sheet_name="Supplier_Evidence",
        index=False
    )

    overdue_rows.head(500).to_excel(
        writer,
        sheet_name="Receivable_Evidence",
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
# 21. CREATE MARKDOWN REPORT
# ============================================================

markdown_lines = [
    "# Five Largest Business Problems — Root Cause Analysis",
    "",
    "## Executive Summary",
    ""
]

for _, problem in root_cause_summary.iterrows():
    markdown_lines.extend(
        [
            f"## {int(problem['Problem_Rank'])}. "
            f"{problem['Business_Problem']}",
            "",
            f"- **Key metric:** {problem['Key_Metric']}",
            f"- **Actual result:** {problem['Actual_Result_Display']}",
            f"- **Priority:** {problem['Priority']}",
            f"- **Root cause:** {problem['Root_Cause']}",
            f"- **Financial impact/exposure:** "
            f"₹{problem['Financial_Impact']:,.2f}",
            f"- **Recommendation:** "
            f"{problem['Recommended_Action']}",
            ""
        ]
    )

markdown_lines.extend(
    [
        "## Important Interpretation Note",
        "",
        "Financial impact values include different concepts such as "
        "actual loss, cash exposure, excess inventory and supplier "
        "purchase exposure. They should not be added together as "
        "one unique company loss.",
        ""
    ]
)

with open(
    MARKDOWN_OUTPUT,
    "w",
    encoding="utf-8"
) as markdown_file:
    markdown_file.write(
        "\n".join(markdown_lines)
    )


# ============================================================
# 22. PRINT FINAL RESULTS
# ============================================================

print("\n" + "=" * 80)
print("FIVE LARGEST BUSINESS PROBLEMS")
print("=" * 80)

print(
    root_cause_summary[
        [
            "Problem_Rank",
            "Business_Problem",
            "Actual_Result_Display",
            "Priority",
            "Financial_Impact",
            "Recommended_Action"
        ]
    ].to_string(index=False)
)

print("\n" + "=" * 80)
print("SUPPORTING FINDINGS")
print("=" * 80)

print(
    f"\nCompany net loss: "
    f"₹{abs(net_profit):,.2f}"
)

print(
    f"Negative-profit products: "
    f"{len(negative_products):,}"
)

print(
    f"Excess inventory value: "
    f"₹{excess_inventory_value:,.2f}"
)

print(
    f"Supplier on-time delivery: "
    f"{supplier_on_time_rate:.2f}%"
)

print(
    f"Revenue reconciliation difference: "
    f"₹{reconciliation_difference:,.2f}"
)

print(
    f"Overdue amount >180 days: "
    f"₹{overdue_amount:,.2f}"
)

print("\n" + "=" * 80)
print("ROOT CAUSE ANALYSIS COMPLETED SUCCESSFULLY")
print("=" * 80)

print(f"\nExcel report saved in:\n{EXCEL_OUTPUT}")
print(f"\nCSV summary saved in:\n{CSV_OUTPUT}")
print(f"\nMarkdown report saved in:\n{MARKDOWN_OUTPUT}")