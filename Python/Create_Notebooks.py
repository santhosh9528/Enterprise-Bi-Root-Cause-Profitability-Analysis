# ============================================================
# CREATE ALL FOUR REQUIRED JUPYTER NOTEBOOKS
# ============================================================

from pathlib import Path
import nbformat as nbf

PYTHON_FOLDER = Path(__file__).resolve().parent


def markdown(text):
    return nbf.v4.new_markdown_cell(text)


def code(text):
    return nbf.v4.new_code_cell(text)


def save_notebook(filename, cells):
    notebook = nbf.v4.new_notebook()
    notebook["cells"] = cells

    notebook["metadata"] = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3"
        }
    }

    output_path = PYTHON_FOLDER / filename

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:
        nbf.write(notebook, file)

    print(f"Created: {output_path}")


# ============================================================
# 1. CLEANING NOTEBOOK
# ============================================================

cleaning_cells = [
    markdown(
        """
# Enterprise BI — Data Cleaning and Quality Audit

## TL;DR

This notebook audits all raw and cleaned datasets for missing values,
duplicate rows, missing primary keys and row-count changes.

## Context & Methods

- Raw files are read from `Raw_Data`.
- Cleaned files are read from `Cleaned_Data`.
- Individual records are not manually edited.
- Cleaning and validation are reproducible.
"""
    ),

    code(
        """
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

warnings.filterwarnings("ignore")
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)

CURRENT_FOLDER = Path.cwd()

if CURRENT_FOLDER.name.lower() == "python":
    PROJECT_FOLDER = CURRENT_FOLDER.parent
else:
    PROJECT_FOLDER = CURRENT_FOLDER

RAW_FOLDER = PROJECT_FOLDER / "Raw_Data"
CLEANED_FOLDER = PROJECT_FOLDER / "Cleaned_Data"
QUALITY_FOLDER = PROJECT_FOLDER / "Data_Quality"

QUALITY_FOLDER.mkdir(parents=True, exist_ok=True)

print("Project folder:", PROJECT_FOLDER)
print("Raw folder exists:", RAW_FOLDER.exists())
print("Cleaned folder exists:", CLEANED_FOLDER.exists())
"""
    ),

    markdown("## Data Audit"),

    code(
        """
def audit_csv_folder(folder, source_name):
    audit_rows = []

    if not folder.exists():
        return pd.DataFrame()

    for file_path in sorted(folder.glob("*.csv")):
        dataframe = pd.read_csv(
            file_path,
            low_memory=False
        )

        primary_key_column = (
            dataframe.columns[0]
            if len(dataframe.columns) > 0
            else None
        )

        missing_primary_keys = (
            dataframe[primary_key_column].isna().sum()
            if primary_key_column
            else 0
        )

        duplicate_rows = dataframe.duplicated().sum()
        missing_cells = dataframe.isna().sum().sum()
        total_cells = dataframe.shape[0] * dataframe.shape[1]

        completeness_percentage = (
            (1 - missing_cells / total_cells) * 100
            if total_cells > 0
            else 0
        )

        valid_records = max(
            len(dataframe)
            - duplicate_rows
            - missing_primary_keys,
            0
        )

        quality_percentage = (
            valid_records / len(dataframe) * 100
            if len(dataframe) > 0
            else 0
        )

        audit_rows.append(
            {
                "Source": source_name,
                "Dataset": file_path.stem,
                "Total_Records": len(dataframe),
                "Total_Columns": len(dataframe.columns),
                "Duplicate_Rows": int(duplicate_rows),
                "Missing_Cells": int(missing_cells),
                "Missing_Primary_Keys": int(missing_primary_keys),
                "Valid_Records": int(valid_records),
                "Completeness_Percentage": round(
                    completeness_percentage,
                    2
                ),
                "Quality_Percentage": round(
                    quality_percentage,
                    2
                )
            }
        )

    return pd.DataFrame(audit_rows)


raw_audit = audit_csv_folder(
    RAW_FOLDER,
    "Raw"
)

cleaned_audit = audit_csv_folder(
    CLEANED_FOLDER,
    "Cleaned"
)

quality_audit = pd.concat(
    [
        raw_audit,
        cleaned_audit
    ],
    ignore_index=True
)

quality_audit
"""
    ),

    markdown("## Raw vs Cleaned Comparison"),

    code(
        """
if not raw_audit.empty and not cleaned_audit.empty:
    comparison = raw_audit.merge(
        cleaned_audit,
        on="Dataset",
        how="outer",
        suffixes=("_Raw", "_Cleaned")
    )

    comparison["Rows_Removed"] = (
        comparison["Total_Records_Raw"]
        - comparison["Total_Records_Cleaned"]
    )

    comparison["Duplicate_Reduction"] = (
        comparison["Duplicate_Rows_Raw"]
        - comparison["Duplicate_Rows_Cleaned"]
    )

    comparison["Missing_Cell_Reduction"] = (
        comparison["Missing_Cells_Raw"]
        - comparison["Missing_Cells_Cleaned"]
    )

    comparison.to_csv(
        QUALITY_FOLDER
        / "Notebook_Raw_Cleaned_Comparison.csv",
        index=False
    )

    display(comparison)
else:
    comparison = pd.DataFrame()
    print("Raw or Cleaned files unavailable.")
"""
    ),

    markdown("## Data Quality Visual"),

    code(
        """
if not quality_audit.empty:
    chart_data = quality_audit[
        quality_audit["Source"] == "Cleaned"
    ].sort_values(
        "Quality_Percentage"
    )

    plt.figure(figsize=(12, 8))

    sns.barplot(
        data=chart_data,
        y="Dataset",
        x="Quality_Percentage",
        color="#2774AE"
    )

    plt.axvline(
        95,
        color="red",
        linestyle="--",
        label="95% quality target"
    )

    plt.title("Cleaned Dataset Quality Score")
    plt.xlabel("Quality Percentage")
    plt.ylabel("Dataset")
    plt.xlim(0, 100)
    plt.legend()
    plt.tight_layout()
    plt.show()
"""
    ),

    markdown(
        """
## Takeaways

- Cleaning is performed through repeatable code rather than manual row edits.
- Duplicate and missing-key checks are retained as an audit trail.
- Foreign-key and reconciliation issues must be reviewed separately because a
  structurally valid record may still be commercially incorrect.
"""
    )
]


# ============================================================
# 2. EDA NOTEBOOK
# ============================================================

eda_cells = [
    markdown(
        """
# Enterprise BI — Exploratory Data Analysis

## TL;DR

This notebook explores revenue, profit, monthly trends, categories and regions.
The main analytical question is why revenue does not translate into profit.
"""
    ),

    code(
        """
from getpass import getpass
import mysql.connector
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

warnings.filterwarnings("ignore")

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)
pd.set_option("display.float_format", lambda x: f"{x:,.2f}")

sns.set_theme(style="whitegrid")

MYSQL_PASSWORD = getpass("Enter MySQL password: ")

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password=MYSQL_PASSWORD,
    database="enterprise_bi"
)

print("MySQL connection successful!")
"""
    ),

    markdown("## Company KPI Summary"),

    code(
        """
company_query = '''
SELECT
    SUM(Revenue) AS Revenue,
    SUM(Discount) AS Discounts,
    SUM(Refunds) AS Refunds,
    SUM(Product_Cost) AS Product_Cost,
    SUM(Shipping_Cost) AS Shipping_Cost,
    SUM(Payment_Fee) AS Payment_Fees,
    SUM(Allocated_Marketing_Cost) AS Marketing_Cost,
    SUM(Net_Profit) AS Net_Profit,
    SUM(Net_Profit) / NULLIF(SUM(Revenue), 0) * 100
        AS Profit_Margin_Percentage,
    COUNT(DISTINCT Order_ID) AS Orders,
    COUNT(DISTINCT Customer_ID) AS Customers
FROM vw_sales_profitability
'''

company_kpis = pd.read_sql(
    company_query,
    connection
)

company_kpis
"""
    ),

    markdown("## Monthly Revenue and Profit Trend"),

    code(
        """
monthly_query = '''
SELECT
    DATE_FORMAT(Sale_Date, '%Y-%m-01') AS Month,
    SUM(Revenue) AS Revenue,
    SUM(Net_Profit) AS Net_Profit,
    SUM(Net_Profit) / NULLIF(SUM(Revenue), 0) * 100
        AS Profit_Margin_Percentage,
    COUNT(DISTINCT Order_ID) AS Orders
FROM vw_sales_profitability
GROUP BY DATE_FORMAT(Sale_Date, '%Y-%m-01')
ORDER BY Month
'''

monthly = pd.read_sql(
    monthly_query,
    connection
)

monthly["Month"] = pd.to_datetime(
    monthly["Month"]
)

monthly
"""
    ),

    code(
        """
fig, first_axis = plt.subplots(
    figsize=(13, 6)
)

first_axis.plot(
    monthly["Month"],
    monthly["Revenue"],
    marker="o",
    color="#2774AE",
    label="Revenue"
)

first_axis.set_xlabel("Month")
first_axis.set_ylabel("Revenue", color="#2774AE")

second_axis = first_axis.twinx()

second_axis.plot(
    monthly["Month"],
    monthly["Net_Profit"],
    marker="o",
    color="#D64545",
    label="Net Profit"
)

second_axis.axhline(
    0,
    color="black",
    linewidth=1
)

second_axis.set_ylabel(
    "Net Profit",
    color="#D64545"
)

plt.title(
    "Monthly Revenue vs Net Profit"
)

fig.tight_layout()
plt.show()
"""
    ),

    markdown("## Category Performance"),

    code(
        """
category_query = '''
SELECT
    Category,
    SUM(Quantity) AS Units_Sold,
    SUM(Revenue) AS Revenue,
    SUM(Net_Profit) AS Net_Profit,
    SUM(Net_Profit) / NULLIF(SUM(Revenue), 0) * 100
        AS Profit_Margin_Percentage
FROM vw_sales_profitability
GROUP BY Category
ORDER BY Revenue DESC
'''

category = pd.read_sql(
    category_query,
    connection
)

category
"""
    ),

    code(
        """
plt.figure(figsize=(11, 6))

sns.barplot(
    data=category,
    x="Category",
    y="Net_Profit",
    color="#D64545"
)

plt.axhline(
    0,
    color="black",
    linewidth=1
)

plt.title("Net Profit by Category")
plt.xlabel("Category")
plt.ylabel("Net Profit")
plt.xticks(rotation=25)
plt.tight_layout()
plt.show()
"""
    ),

    markdown("## Regional Performance"),

    code(
        """
region_query = '''
SELECT
    Region_ID,
    MAX(Region_Name) AS Region_Name,
    SUM(Revenue) AS Revenue,
    SUM(Net_Profit) AS Net_Profit,
    SUM(Net_Profit) / NULLIF(SUM(Revenue), 0) * 100
        AS Profit_Margin_Percentage
FROM vw_sales_profitability
GROUP BY Region_ID
ORDER BY Profit_Margin_Percentage
'''

region = pd.read_sql(
    region_query,
    connection
)

connection.close()

region
"""
    ),

    code(
        """
plt.figure(figsize=(11, 7))

sns.barplot(
    data=region,
    y="Region_Name",
    x="Profit_Margin_Percentage",
    color="#D64545"
)

plt.axvline(
    0,
    color="black",
    linewidth=1
)

plt.title("Regional Profit Margin")
plt.xlabel("Profit Margin (%)")
plt.ylabel("Region")
plt.tight_layout()
plt.show()
"""
    ),

    markdown(
        """
## Takeaways

- Revenue remains near ₹4 crore per month, but profit is negative throughout.
- Every category and region is loss-making.
- The loss is structural rather than isolated to one product or month.
- Product cost and marketing allocation are the largest cost drivers.
"""
    )
]


# ============================================================
# 3. STATISTICS NOTEBOOK
# ============================================================

statistics_cells = [
    markdown(
        """
# Checkout A/B Test — Statistical Investigation

## TL;DR

The treatment checkout recorded a small conversion increase, but the result was
not statistically significant. Management should not permanently implement the
new design based on the available evidence.
"""
    ),

    code(
        """
from pathlib import Path
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

CURRENT_FOLDER = Path.cwd()

if CURRENT_FOLDER.name.lower() == "python":
    PROJECT_FOLDER = CURRENT_FOLDER.parent
else:
    PROJECT_FOLDER = CURRENT_FOLDER

SUMMARY_FILE = (
    PROJECT_FOLDER
    / "AB_Test_Analysis"
    / "AB_Test_Summary.csv"
)

ab_summary = pd.read_csv(
    SUMMARY_FILE
)

ab_summary
"""
    ),

    markdown("## Hypotheses and Method"),

    code(
        """
SIGNIFICANCE_LEVEL = 0.05

control = ab_summary[
    ab_summary["Experiment_Group"]
    == "Control"
].iloc[0]

treatment = ab_summary[
    ab_summary["Experiment_Group"]
    == "Treatment"
].iloc[0]

control_sessions = int(
    control["Total_Sessions"]
)

control_conversions = int(
    control["Conversions"]
)

treatment_sessions = int(
    treatment["Total_Sessions"]
)

treatment_conversions = int(
    treatment["Conversions"]
)

control_rate = (
    control_conversions
    / control_sessions
)

treatment_rate = (
    treatment_conversions
    / treatment_sessions
)

print(
    "H0: Control and Treatment conversion rates are equal."
)

print(
    "H1: Control and Treatment conversion rates are different."
)
"""
    ),

    markdown("## Two-Proportion Z-Test"),

    code(
        """
pooled_rate = (
    control_conversions
    + treatment_conversions
) / (
    control_sessions
    + treatment_sessions
)

pooled_standard_error = math.sqrt(
    pooled_rate
    * (1 - pooled_rate)
    * (
        1 / control_sessions
        + 1 / treatment_sessions
    )
)

z_statistic = (
    treatment_rate - control_rate
) / pooled_standard_error

p_value = 2 * (
    1 - norm.cdf(abs(z_statistic))
)

difference = (
    treatment_rate - control_rate
)

unpooled_standard_error = math.sqrt(
    treatment_rate
    * (1 - treatment_rate)
    / treatment_sessions
    +
    control_rate
    * (1 - control_rate)
    / control_sessions
)

ci_lower = (
    difference
    - 1.96 * unpooled_standard_error
)

ci_upper = (
    difference
    + 1.96 * unpooled_standard_error
)

cohens_h = (
    2 * math.asin(math.sqrt(treatment_rate))
    - 2 * math.asin(math.sqrt(control_rate))
)

result = pd.DataFrame(
    {
        "Metric": [
            "Control Conversion Rate %",
            "Treatment Conversion Rate %",
            "Absolute Lift Percentage Points",
            "Relative Lift %",
            "Z Statistic",
            "P Value",
            "95% CI Lower %",
            "95% CI Upper %",
            "Cohen's H"
        ],
        "Value": [
            control_rate * 100,
            treatment_rate * 100,
            difference * 100,
            difference / control_rate * 100,
            z_statistic,
            p_value,
            ci_lower * 100,
            ci_upper * 100,
            cohens_h
        ]
    }
)

result
"""
    ),

    markdown("## Conversion Comparison"),

    code(
        """
plot_data = pd.DataFrame(
    {
        "Group": [
            "Control",
            "Treatment"
        ],
        "Conversion Rate": [
            control_rate * 100,
            treatment_rate * 100
        ]
    }
)

plt.figure(figsize=(8, 5))

bars = plt.bar(
    plot_data["Group"],
    plot_data["Conversion Rate"],
    color=[
        "#2774AE",
        "#F79009"
    ]
)

for bar, value in zip(
    bars,
    plot_data["Conversion Rate"]
):
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.03,
        f"{value:.3f}%",
        ha="center"
    )

plt.title("Checkout A/B Test Conversion Rate")
plt.ylabel("Conversion Rate (%)")
plt.tight_layout()
plt.show()
"""
    ),

    markdown(
        """
## Takeaways

- Control conversion: approximately 8.604%.
- Treatment conversion: approximately 8.657%.
- P-value is approximately 0.764, above the 0.05 significance level.
- The 95% confidence interval includes zero.
- Cohen's h indicates a negligible effect.
- Recommendation: do not permanently implement the treatment yet.
"""
    )
]


# ============================================================
# 4. FORECASTING NOTEBOOK
# ============================================================

forecasting_cells = [
    markdown(
        """
# Revenue, Orders and Product Demand Forecasting

## TL;DR

This notebook reviews the three-month Holt trend forecast and compares forecast
revenue, orders and product demand against management targets.
"""
    ),

    code(
        """
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")

CURRENT_FOLDER = Path.cwd()

if CURRENT_FOLDER.name.lower() == "python":
    PROJECT_FOLDER = CURRENT_FOLDER.parent
else:
    PROJECT_FOLDER = CURRENT_FOLDER

FORECAST_REPORT = (
    PROJECT_FOLDER
    / "Forecasting_Analysis"
    / "Forecasting_Report.xlsx"
)

next_three_months = pd.read_excel(
    FORECAST_REPORT,
    sheet_name="Next_3_Months"
)

actual_forecast_target = pd.read_excel(
    FORECAST_REPORT,
    sheet_name="Actual_Forecast_Target"
)

product_demand = pd.read_excel(
    FORECAST_REPORT,
    sheet_name="Product_Demand_Summary"
)

next_three_months["Month"] = pd.to_datetime(
    next_three_months["Month"]
)

actual_forecast_target["Month"] = pd.to_datetime(
    actual_forecast_target["Month"]
)

next_three_months
"""
    ),

    markdown("## Next Three-Month Forecast"),

    code(
        """
forecast_columns = [
    "Month",
    "Revenue_Forecast",
    "Revenue_CI_Lower",
    "Revenue_CI_Upper",
    "Revenue_Target",
    "Revenue_Target_Achievement_Percentage",
    "Revenue_Target_Status",
    "Orders_Forecast",
    "Order_Target",
    "Demand_Forecast_Units"
]

next_three_months[
    forecast_columns
]
"""
    ),

    markdown("## Actual vs Forecast vs Target"),

    code(
        """
historical = actual_forecast_target[
    actual_forecast_target["Record_Type"]
    == "Actual"
].copy()

future = actual_forecast_target[
    actual_forecast_target["Record_Type"]
    == "Forecast"
].copy()

plt.figure(figsize=(13, 6))

plt.plot(
    historical["Month"],
    historical["Actual_Revenue"],
    marker="o",
    label="Actual Revenue",
    color="#2774AE"
)

plt.plot(
    future["Month"],
    future["Revenue_Forecast"],
    marker="o",
    label="Forecast Revenue",
    color="#F79009"
)

plt.plot(
    future["Month"],
    future["Revenue_Target"],
    marker="s",
    linestyle="--",
    label="Revenue Target",
    color="#D64545"
)

plt.fill_between(
    future["Month"],
    future["Revenue_CI_Lower"],
    future["Revenue_CI_Upper"],
    color="#F79009",
    alpha=0.20,
    label="95% Confidence Interval"
)

plt.title("Revenue: Actual vs Forecast vs Target")
plt.xlabel("Month")
plt.ylabel("Revenue")
plt.legend()
plt.xticks(rotation=30)
plt.tight_layout()
plt.show()
"""
    ),

    markdown("## Next-Quarter Target Assessment"),

    code(
        """
quarter_revenue_forecast = next_three_months[
    "Revenue_Forecast"
].sum()

quarter_revenue_target = next_three_months[
    "Revenue_Target"
].sum()

quarter_orders_forecast = next_three_months[
    "Orders_Forecast"
].sum()

quarter_demand_forecast = next_three_months[
    "Demand_Forecast_Units"
].sum()

revenue_achievement = (
    quarter_revenue_forecast
    / quarter_revenue_target
    * 100
)

quarter_summary = pd.DataFrame(
    {
        "Metric": [
            "Revenue Forecast",
            "Revenue Target",
            "Revenue Target Achievement %",
            "Orders Forecast",
            "Product Demand Forecast"
        ],
        "Value": [
            quarter_revenue_forecast,
            quarter_revenue_target,
            revenue_achievement,
            quarter_orders_forecast,
            quarter_demand_forecast
        ]
    }
)

quarter_summary
"""
    ),

    markdown("## Top Forecasted Products"),

    code(
        """
top_products = product_demand.sort_values(
    "Next_Quarter_Demand",
    ascending=False
).head(15)

plt.figure(figsize=(12, 8))

sns.barplot(
    data=top_products,
    y="Product_Name",
    x="Next_Quarter_Demand",
    color="#2774AE"
)

plt.title(
    "Top 15 Products by Forecasted Next-Quarter Demand"
)

plt.xlabel("Forecasted Units")
plt.ylabel("Product")
plt.tight_layout()
plt.show()

top_products
"""
    ),

    markdown(
        """
## Key Assumptions and Limitations

- Only 12 months of historical data is available.
- The model uses a damped Holt trend and cannot fully validate annual seasonality.
- No major pricing, supply-chain or economic disruption is assumed.
- Future targets are extrapolated when explicit future targets are unavailable.
- Forecast confidence intervals reflect historical residual error.

## Takeaways

- Next-quarter revenue forecast is approximately ₹12.31 crore.
- Revenue target is approximately ₹12.55 crore.
- Expected achievement is approximately 98.15%, so the target is at risk.
- Forecasted next-quarter demand is approximately 188,298 units.
"""
    )
]


# ============================================================
# SAVE ALL NOTEBOOKS
# ============================================================

save_notebook(
    "Cleaning.ipynb",
    cleaning_cells
)

save_notebook(
    "EDA.ipynb",
    eda_cells
)

save_notebook(
    "Statistics.ipynb",
    statistics_cells
)

save_notebook(
    "Forecasting.ipynb",
    forecasting_cells
)

print("\n" + "=" * 70)
print("ALL FOUR NOTEBOOKS CREATED SUCCESSFULLY")
print("=" * 70)