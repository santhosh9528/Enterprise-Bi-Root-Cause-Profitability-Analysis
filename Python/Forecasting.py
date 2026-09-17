from getpass import getpass
# ============================================================
# PART 14: REVENUE, ORDERS AND PRODUCT DEMAND FORECASTING
# Forecast Horizon: Next 3 Months
# ============================================================

from pathlib import Path
import warnings
import math

import mysql.connector
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.holtwinters import Holt

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
# 2. FORECAST CONFIGURATION
# ============================================================

FORECAST_MONTHS = 3
CONFIDENCE_LEVEL = 0.95
Z_VALUE = 1.96


# ============================================================
# 3. OUTPUT LOCATION
# ============================================================

CURRENT_FOLDER = Path(__file__).resolve().parent
PROJECT_FOLDER = CURRENT_FOLDER.parent

OUTPUT_FOLDER = PROJECT_FOLDER / "Forecasting_Analysis"
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

EXCEL_OUTPUT = OUTPUT_FOLDER / "Forecasting_Report.xlsx"
CSV_OUTPUT = OUTPUT_FOLDER / "Next_3_Month_Forecast.csv"

print("=" * 78)
print("REVENUE, ORDERS AND PRODUCT DEMAND FORECASTING STARTED")
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
# 5. LOAD MONTHLY REVENUE AND ORDER DATA
# ============================================================

monthly_business_query = """
SELECT
    DATE_FORMAT(Sale_Date, '%Y-%m-01') AS Month,

    SUM(Revenue) AS Actual_Revenue,

    COUNT(
        DISTINCT Order_ID
    ) AS Actual_Orders,

    SUM(Quantity) AS Actual_Units

FROM vw_sales_profitability

WHERE Sale_Date IS NOT NULL

GROUP BY
    DATE_FORMAT(Sale_Date, '%Y-%m-01')

ORDER BY Month;
"""

monthly_business_df = pd.read_sql(
    monthly_business_query,
    connection
)


# ============================================================
# 6. LOAD MONTHLY PRODUCT DEMAND
# ============================================================

product_demand_query = """
SELECT
    DATE_FORMAT(
        vsp.Sale_Date,
        '%Y-%m-01'
    ) AS Month,

    vsp.Product_ID,
    MAX(vsp.Product_Name) AS Product_Name,
    MAX(vsp.Category) AS Category,

    SUM(vsp.Quantity) AS Actual_Demand

FROM vw_sales_profitability vsp

WHERE vsp.Sale_Date IS NOT NULL
  AND vsp.Product_ID IS NOT NULL

GROUP BY
    DATE_FORMAT(
        vsp.Sale_Date,
        '%Y-%m-01'
    ),
    vsp.Product_ID

ORDER BY
    vsp.Product_ID,
    Month;
"""

product_demand_df = pd.read_sql(
    product_demand_query,
    connection
)


# ============================================================
# 7. LOAD MONTHLY TARGETS
# ============================================================

monthly_targets_df = pd.read_sql(
    "SELECT * FROM monthly_targets",
    connection
)

connection.close()

print("Historical business data loaded.")
print("Product demand data loaded.")
print("Monthly target data loaded.")
print("MySQL connection closed.")


# ============================================================
# 8. HELPER FUNCTIONS
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
        normalized_name = normalize_column_name(
            possible_name
        )

        if normalized_name in normalized_columns:
            return normalized_columns[normalized_name]

    if required:
        raise KeyError(
            f"Expected column not found: {possible_names}. "
            f"Available columns: {list(dataframe.columns)}"
        )

    return None


def create_monthly_series(dataframe, date_column, value_column):
    temporary_df = dataframe[
        [
            date_column,
            value_column
        ]
    ].copy()

    temporary_df[date_column] = pd.to_datetime(
        temporary_df[date_column],
        errors="coerce"
    )

    temporary_df[value_column] = pd.to_numeric(
        temporary_df[value_column],
        errors="coerce"
    ).fillna(0)

    temporary_df = temporary_df.dropna(
        subset=[date_column]
    )

    temporary_df[date_column] = (
        temporary_df[date_column]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    monthly_series = (
        temporary_df
        .groupby(date_column)[value_column]
        .sum()
        .sort_index()
    )

    full_month_range = pd.date_range(
        start=monthly_series.index.min(),
        end=monthly_series.index.max(),
        freq="MS"
    )

    monthly_series = monthly_series.reindex(
        full_month_range,
        fill_value=0
    )

    return monthly_series.astype(float)


def forecast_holt(series, forecast_periods=3):
    clean_series = pd.Series(
        series
    ).astype(float)

    clean_series = clean_series.replace(
        [np.inf, -np.inf],
        np.nan
    ).fillna(0)

    if len(clean_series) >= 4:
        try:
            model = Holt(
                clean_series,
                damped_trend=True,
                initialization_method="estimated"
            )

            fitted_model = model.fit(
                optimized=True
            )

            forecast_values = fitted_model.forecast(
                forecast_periods
            )

            fitted_values = fitted_model.fittedvalues

        except Exception:
            x_values = np.arange(
                len(clean_series)
            )

            coefficients = np.polyfit(
                x_values,
                clean_series.values,
                1
            )

            future_x = np.arange(
                len(clean_series),
                len(clean_series) + forecast_periods
            )

            forecast_values = np.polyval(
                coefficients,
                future_x
            )

            fitted_values = np.polyval(
                coefficients,
                x_values
            )

    else:
        forecast_values = np.repeat(
            clean_series.mean(),
            forecast_periods
        )

        fitted_values = np.repeat(
            clean_series.mean(),
            len(clean_series)
        )

    forecast_values = np.maximum(
        np.asarray(forecast_values, dtype=float),
        0
    )

    residuals = (
        clean_series.values
        - np.asarray(fitted_values, dtype=float)
    )

    rmse = math.sqrt(
        np.mean(np.square(residuals))
    ) if len(residuals) > 0 else 0

    lower_values = []
    upper_values = []

    for forecast_step, forecast_value in enumerate(
        forecast_values,
        start=1
    ):
        forecast_error = (
            Z_VALUE
            * rmse
            * math.sqrt(forecast_step)
        )

        lower_values.append(
            max(
                forecast_value - forecast_error,
                0
            )
        )

        upper_values.append(
            forecast_value + forecast_error
        )

    return (
        forecast_values,
        np.array(lower_values),
        np.array(upper_values),
        rmse
    )


def linear_target_forecast(
    historical_series,
    forecast_periods=3
):
    historical_series = pd.Series(
        historical_series
    ).astype(float)

    if len(historical_series) >= 2:
        x_values = np.arange(
            len(historical_series)
        )

        coefficients = np.polyfit(
            x_values,
            historical_series.values,
            1
        )

        future_x = np.arange(
            len(historical_series),
            len(historical_series) + forecast_periods
        )

        target_forecast = np.polyval(
            coefficients,
            future_x
        )

    else:
        target_forecast = np.repeat(
            historical_series.mean(),
            forecast_periods
        )

    return np.maximum(
        target_forecast,
        0
    )


# ============================================================
# 9. PREPARE HISTORICAL BUSINESS DATA
# ============================================================

monthly_business_df["Month"] = pd.to_datetime(
    monthly_business_df["Month"],
    errors="coerce"
)

monthly_business_df = monthly_business_df.dropna(
    subset=["Month"]
)

monthly_business_df = monthly_business_df.sort_values(
    "Month"
).reset_index(drop=True)

for column in [
    "Actual_Revenue",
    "Actual_Orders",
    "Actual_Units"
]:
    monthly_business_df[column] = pd.to_numeric(
        monthly_business_df[column],
        errors="coerce"
    ).fillna(0)

first_month = monthly_business_df[
    "Month"
].min()

last_month = monthly_business_df[
    "Month"
].max()

future_months = pd.date_range(
    start=last_month + pd.offsets.MonthBegin(1),
    periods=FORECAST_MONTHS,
    freq="MS"
)

print(f"\nHistorical period: {first_month.date()} to {last_month.date()}")
print(f"Forecast period: {future_months[0].date()} to {future_months[-1].date()}")


# ============================================================
# 10. FORECAST REVENUE
# ============================================================

revenue_series = create_monthly_series(
    monthly_business_df,
    "Month",
    "Actual_Revenue"
)

(
    revenue_forecast,
    revenue_lower,
    revenue_upper,
    revenue_rmse
) = forecast_holt(
    revenue_series,
    FORECAST_MONTHS
)


# ============================================================
# 11. FORECAST ORDERS
# ============================================================

orders_series = create_monthly_series(
    monthly_business_df,
    "Month",
    "Actual_Orders"
)

(
    orders_forecast,
    orders_lower,
    orders_upper,
    orders_rmse
) = forecast_holt(
    orders_series,
    FORECAST_MONTHS
)


# ============================================================
# 12. FORECAST TOTAL PRODUCT DEMAND
# ============================================================

units_series = create_monthly_series(
    monthly_business_df,
    "Month",
    "Actual_Units"
)

(
    units_forecast,
    units_lower,
    units_upper,
    units_rmse
) = forecast_holt(
    units_series,
    FORECAST_MONTHS
)


# ============================================================
# 13. IDENTIFY MONTHLY TARGET COLUMNS
# ============================================================

target_month_col = find_column(
    monthly_targets_df,
    [
        "Target_Month",
        "Month",
        "Target_Date",
        "Date"
    ]
)

revenue_target_col = find_column(
    monthly_targets_df,
    [
        "Revenue_Target",
        "Target_Revenue",
        "Sales_Target",
        "Target_Sales"
    ],
    required=False
)

order_target_col = find_column(
    monthly_targets_df,
    [
        "Order_Target",
        "Orders_Target",
        "Target_Orders"
    ],
    required=False
)

units_target_col = find_column(
    monthly_targets_df,
    [
        "Units_Target",
        "Quantity_Target",
        "Demand_Target",
        "Target_Quantity"
    ],
    required=False
)

monthly_targets_df[target_month_col] = pd.to_datetime(
    monthly_targets_df[target_month_col],
    errors="coerce"
)

monthly_targets_df[target_month_col] = (
    monthly_targets_df[target_month_col]
    .dt.to_period("M")
    .dt.to_timestamp()
)


# ============================================================
# 14. PREPARE HISTORICAL TARGETS
# ============================================================

historical_targets = pd.DataFrame(
    {
        "Month": sorted(
            monthly_targets_df[
                target_month_col
            ].dropna().unique()
        )
    }
)

if revenue_target_col:
    revenue_targets = (
        monthly_targets_df
        .groupby(target_month_col)[revenue_target_col]
        .sum()
        .reset_index()
        .rename(
            columns={
                target_month_col: "Month",
                revenue_target_col: "Revenue_Target"
            }
        )
    )

    historical_targets = historical_targets.merge(
        revenue_targets,
        on="Month",
        how="left"
    )
else:
    historical_targets["Revenue_Target"] = (
        revenue_series.values
    )

if order_target_col:
    order_targets = (
        monthly_targets_df
        .groupby(target_month_col)[order_target_col]
        .sum()
        .reset_index()
        .rename(
            columns={
                target_month_col: "Month",
                order_target_col: "Order_Target"
            }
        )
    )

    historical_targets = historical_targets.merge(
        order_targets,
        on="Month",
        how="left"
    )
else:
    historical_targets["Order_Target"] = np.nan

if units_target_col:
    unit_targets = (
        monthly_targets_df
        .groupby(target_month_col)[units_target_col]
        .sum()
        .reset_index()
        .rename(
            columns={
                target_month_col: "Month",
                units_target_col: "Units_Target"
            }
        )
    )

    historical_targets = historical_targets.merge(
        unit_targets,
        on="Month",
        how="left"
    )
else:
    historical_targets["Units_Target"] = np.nan


# ============================================================
# 15. FORECAST NEXT-QUARTER TARGETS
# ============================================================

historical_targets = historical_targets.sort_values(
    "Month"
)

historical_targets["Revenue_Target"] = pd.to_numeric(
    historical_targets["Revenue_Target"],
    errors="coerce"
)

available_revenue_targets = (
    historical_targets["Revenue_Target"]
    .dropna()
)

if available_revenue_targets.empty:
    future_revenue_targets = (
        revenue_forecast * 1.05
    )
else:
    future_revenue_targets = linear_target_forecast(
        available_revenue_targets,
        FORECAST_MONTHS
    )

available_order_targets = (
    historical_targets["Order_Target"]
    .dropna()
)

if available_order_targets.empty:
    future_order_targets = (
        orders_forecast * 1.05
    )
else:
    future_order_targets = linear_target_forecast(
        available_order_targets,
        FORECAST_MONTHS
    )

available_unit_targets = (
    historical_targets["Units_Target"]
    .dropna()
)

if available_unit_targets.empty:
    future_units_targets = (
        units_forecast * 1.05
    )
else:
    future_units_targets = linear_target_forecast(
        available_unit_targets,
        FORECAST_MONTHS
    )


# ============================================================
# 16. CREATE NEXT 3-MONTH FORECAST TABLE
# ============================================================

forecast_df = pd.DataFrame(
    {
        "Month": future_months,

        "Revenue_Forecast": revenue_forecast,
        "Revenue_CI_Lower": revenue_lower,
        "Revenue_CI_Upper": revenue_upper,
        "Revenue_Target": future_revenue_targets,

        "Orders_Forecast": orders_forecast,
        "Orders_CI_Lower": orders_lower,
        "Orders_CI_Upper": orders_upper,
        "Order_Target": future_order_targets,

        "Demand_Forecast_Units": units_forecast,
        "Demand_CI_Lower": units_lower,
        "Demand_CI_Upper": units_upper,
        "Units_Target": future_units_targets
    }
)


# ============================================================
# 17. TARGET ACHIEVEMENT
# ============================================================

forecast_df["Revenue_Target_Achievement_Percentage"] = np.where(
    forecast_df["Revenue_Target"] > 0,
    forecast_df["Revenue_Forecast"]
    / forecast_df["Revenue_Target"]
    * 100,
    0
)

forecast_df["Order_Target_Achievement_Percentage"] = np.where(
    forecast_df["Order_Target"] > 0,
    forecast_df["Orders_Forecast"]
    / forecast_df["Order_Target"]
    * 100,
    0
)

forecast_df["Demand_Target_Achievement_Percentage"] = np.where(
    forecast_df["Units_Target"] > 0,
    forecast_df["Demand_Forecast_Units"]
    / forecast_df["Units_Target"]
    * 100,
    0
)


def target_status(forecast, target, lower_limit):
    if target <= 0:
        return "Target Not Available"

    if lower_limit >= target:
        return "Likely to Achieve"

    if forecast >= target:
        return "Possible - Forecast Above Target"

    if forecast >= target * 0.90:
        return "At Risk"

    return "Unlikely to Achieve"


forecast_df["Revenue_Target_Status"] = forecast_df.apply(
    lambda row: target_status(
        row["Revenue_Forecast"],
        row["Revenue_Target"],
        row["Revenue_CI_Lower"]
    ),
    axis=1
)

forecast_df["Order_Target_Status"] = forecast_df.apply(
    lambda row: target_status(
        row["Orders_Forecast"],
        row["Order_Target"],
        row["Orders_CI_Lower"]
    ),
    axis=1
)

forecast_df["Demand_Target_Status"] = forecast_df.apply(
    lambda row: target_status(
        row["Demand_Forecast_Units"],
        row["Units_Target"],
        row["Demand_CI_Lower"]
    ),
    axis=1
)


# ============================================================
# 18. PRODUCT-LEVEL DEMAND FORECAST
# ============================================================

product_demand_df["Month"] = pd.to_datetime(
    product_demand_df["Month"],
    errors="coerce"
)

product_demand_df["Actual_Demand"] = pd.to_numeric(
    product_demand_df["Actual_Demand"],
    errors="coerce"
).fillna(0)

all_historical_months = pd.date_range(
    start=first_month,
    end=last_month,
    freq="MS"
)

product_forecast_rows = []

for product_id, product_group in product_demand_df.groupby(
    "Product_ID"
):
    product_name = product_group[
        "Product_Name"
    ].iloc[0]

    category = product_group[
        "Category"
    ].iloc[0]

    monthly_product_series = (
        product_group
        .groupby("Month")["Actual_Demand"]
        .sum()
        .reindex(
            all_historical_months,
            fill_value=0
        )
        .astype(float)
    )

    (
        demand_forecast,
        demand_lower,
        demand_upper,
        demand_rmse
    ) = forecast_holt(
        monthly_product_series,
        FORECAST_MONTHS
    )

    historical_average = (
        monthly_product_series.mean()
    )

    recent_three_month_average = (
        monthly_product_series.tail(3).mean()
    )

    for month_index in range(
        FORECAST_MONTHS
    ):
        product_forecast_rows.append(
            {
                "Forecast_Month": future_months[
                    month_index
                ],

                "Product_ID": product_id,
                "Product_Name": product_name,
                "Category": category,

                "Historical_Monthly_Average_Demand":
                    historical_average,

                "Recent_3_Month_Average_Demand":
                    recent_three_month_average,

                "Forecast_Demand_Units":
                    demand_forecast[month_index],

                "Demand_CI_Lower":
                    demand_lower[month_index],

                "Demand_CI_Upper":
                    demand_upper[month_index],

                "Forecast_RMSE":
                    demand_rmse
            }
        )

product_forecast_df = pd.DataFrame(
    product_forecast_rows
)

product_forecast_df[
    "Demand_Trend_Percentage"
] = np.where(
    product_forecast_df[
        "Historical_Monthly_Average_Demand"
    ] > 0,

    (
        product_forecast_df[
            "Forecast_Demand_Units"
        ]
        - product_forecast_df[
            "Historical_Monthly_Average_Demand"
        ]
    )
    / product_forecast_df[
        "Historical_Monthly_Average_Demand"
    ]
    * 100,

    0
)

product_forecast_df["Demand_Status"] = np.select(
    [
        product_forecast_df[
            "Demand_Trend_Percentage"
        ] >= 10,

        product_forecast_df[
            "Demand_Trend_Percentage"
        ] <= -10
    ],
    [
        "Demand Increasing",
        "Demand Decreasing"
    ],
    default="Stable Demand"
)


# ============================================================
# 19. TOP FORECASTED PRODUCTS
# ============================================================

next_quarter_product_summary = (
    product_forecast_df
    .groupby(
        [
            "Product_ID",
            "Product_Name",
            "Category"
        ]
    )
    .agg(
        Next_Quarter_Demand=(
            "Forecast_Demand_Units",
            "sum"
        ),
        Average_Monthly_Forecast=(
            "Forecast_Demand_Units",
            "mean"
        ),
        Average_Demand_Trend_Percentage=(
            "Demand_Trend_Percentage",
            "mean"
        )
    )
    .reset_index()
    .sort_values(
        "Next_Quarter_Demand",
        ascending=False
    )
)

next_quarter_product_summary[
    "Demand_Rank"
] = (
    next_quarter_product_summary[
        "Next_Quarter_Demand"
    ]
    .rank(
        method="dense",
        ascending=False
    )
    .astype(int)
)


# ============================================================
# 20. NEXT-QUARTER SUMMARY
# ============================================================

next_quarter_revenue_forecast = forecast_df[
    "Revenue_Forecast"
].sum()

next_quarter_revenue_target = forecast_df[
    "Revenue_Target"
].sum()

next_quarter_orders_forecast = forecast_df[
    "Orders_Forecast"
].sum()

next_quarter_order_target = forecast_df[
    "Order_Target"
].sum()

next_quarter_demand_forecast = forecast_df[
    "Demand_Forecast_Units"
].sum()

next_quarter_units_target = forecast_df[
    "Units_Target"
].sum()

quarter_revenue_achievement = (
    next_quarter_revenue_forecast
    / next_quarter_revenue_target
    * 100
    if next_quarter_revenue_target > 0
    else 0
)

quarter_order_achievement = (
    next_quarter_orders_forecast
    / next_quarter_order_target
    * 100
    if next_quarter_order_target > 0
    else 0
)

quarter_demand_achievement = (
    next_quarter_demand_forecast
    / next_quarter_units_target
    * 100
    if next_quarter_units_target > 0
    else 0
)

if quarter_revenue_achievement >= 100:
    quarter_target_conclusion = (
        "Company is forecasted to achieve the next-quarter "
        "revenue target."
    )
elif quarter_revenue_achievement >= 90:
    quarter_target_conclusion = (
        "Next-quarter revenue target is at risk; management "
        "action is required."
    )
else:
    quarter_target_conclusion = (
        "Company is unlikely to achieve the next-quarter "
        "revenue target."
    )


# ============================================================
# 21. MODEL SUMMARY
# ============================================================

model_summary = pd.DataFrame(
    {
        "Metric": [
            "Forecast Model",
            "Historical Months",
            "Forecast Horizon",
            "Revenue Forecast RMSE",
            "Orders Forecast RMSE",
            "Demand Forecast RMSE",
            "Next Quarter Revenue Forecast",
            "Next Quarter Revenue Target",
            "Revenue Target Achievement (%)",
            "Next Quarter Orders Forecast",
            "Next Quarter Order Target",
            "Order Target Achievement (%)",
            "Next Quarter Demand Forecast",
            "Next Quarter Units Target",
            "Demand Target Achievement (%)",
            "Management Conclusion"
        ],

        "Value": [
            "Holt Damped Trend",
            len(monthly_business_df),
            FORECAST_MONTHS,
            revenue_rmse,
            orders_rmse,
            units_rmse,
            next_quarter_revenue_forecast,
            next_quarter_revenue_target,
            quarter_revenue_achievement,
            next_quarter_orders_forecast,
            next_quarter_order_target,
            quarter_order_achievement,
            next_quarter_demand_forecast,
            next_quarter_units_target,
            quarter_demand_achievement,
            quarter_target_conclusion
        ]
    }
)


# ============================================================
# 22. ASSUMPTIONS AND LIMITATIONS
# ============================================================

assumptions_df = pd.DataFrame(
    {
        "Type": [
            "Assumption",
            "Assumption",
            "Assumption",
            "Limitation",
            "Limitation",
            "Limitation"
        ],

        "Explanation": [
            (
                "Historical sales pattern continues during the "
                "next three months."
            ),
            (
                "No major pricing, market, supply-chain or "
                "economic disruption occurs."
            ),
            (
                "When future targets are unavailable, historical "
                "target trend is extrapolated."
            ),
            (
                "Only 12 months of historical data is available; "
                "full seasonal behaviour cannot be validated."
            ),
            (
                "Forecast confidence intervals are estimated using "
                "historical model residual error."
            ),
            (
                "Unexpected promotions, stockouts and competitor "
                "actions are not included in the model."
            )
        ]
    }
)


# ============================================================
# 23. CREATE ACTUAL + FORECAST TABLE
# ============================================================

historical_output = monthly_business_df.copy()

historical_output = historical_output.merge(
    historical_targets,
    on="Month",
    how="left"
)

historical_output["Record_Type"] = "Actual"

forecast_output = forecast_df.copy()

forecast_output["Actual_Revenue"] = np.nan
forecast_output["Actual_Orders"] = np.nan
forecast_output["Actual_Units"] = np.nan
forecast_output["Record_Type"] = "Forecast"

combined_output = pd.concat(
    [
        historical_output,
        forecast_output
    ],
    ignore_index=True,
    sort=False
).sort_values("Month")


# ============================================================
# 24. ROUND NUMERIC RESULTS
# ============================================================

for dataframe in [
    forecast_df,
    product_forecast_df,
    next_quarter_product_summary,
    combined_output
]:
    numeric_columns = dataframe.select_dtypes(
        include=[np.number]
    ).columns

    dataframe[numeric_columns] = dataframe[
        numeric_columns
    ].round(2)


# ============================================================
# 25. SAVE CSV
# ============================================================

forecast_df.to_csv(
    CSV_OUTPUT,
    index=False
)


# ============================================================
# 26. SAVE EXCEL REPORT
# ============================================================

with pd.ExcelWriter(
    EXCEL_OUTPUT,
    engine="openpyxl"
) as writer:

    model_summary.to_excel(
        writer,
        sheet_name="Executive_Summary",
        index=False
    )

    forecast_df.to_excel(
        writer,
        sheet_name="Next_3_Months",
        index=False
    )

    combined_output.to_excel(
        writer,
        sheet_name="Actual_Forecast_Target",
        index=False
    )

    next_quarter_product_summary.to_excel(
        writer,
        sheet_name="Product_Demand_Summary",
        index=False
    )

    product_forecast_df.to_excel(
        writer,
        sheet_name="Product_Monthly_Forecast",
        index=False
    )

    assumptions_df.to_excel(
        writer,
        sheet_name="Assumptions",
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
            ].width = min(max_length + 2, 50)


# ============================================================
# 27. REVENUE FORECAST CHART
# ============================================================

sns.set_theme(style="whitegrid")

plt.figure(figsize=(13, 7))

plt.plot(
    monthly_business_df["Month"],
    monthly_business_df["Actual_Revenue"],
    marker="o",
    linewidth=2,
    label="Actual Revenue"
)

plt.plot(
    forecast_df["Month"],
    forecast_df["Revenue_Forecast"],
    marker="o",
    linewidth=2,
    color="orange",
    label="Forecast Revenue"
)

plt.plot(
    forecast_df["Month"],
    forecast_df["Revenue_Target"],
    marker="s",
    linestyle="--",
    color="red",
    label="Revenue Target"
)

plt.fill_between(
    forecast_df["Month"],
    forecast_df["Revenue_CI_Lower"],
    forecast_df["Revenue_CI_Upper"],
    color="orange",
    alpha=0.20,
    label="95% Confidence Interval"
)

plt.title(
    "Monthly Revenue: Actual vs Forecast vs Target",
    fontsize=15,
    fontweight="bold"
)

plt.xlabel("Month")
plt.ylabel("Revenue")
plt.legend()
plt.xticks(rotation=30)
plt.tight_layout()

plt.savefig(
    OUTPUT_FOLDER / "01_Revenue_Forecast.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 28. ORDERS FORECAST CHART
# ============================================================

plt.figure(figsize=(13, 7))

plt.plot(
    monthly_business_df["Month"],
    monthly_business_df["Actual_Orders"],
    marker="o",
    linewidth=2,
    label="Actual Orders"
)

plt.plot(
    forecast_df["Month"],
    forecast_df["Orders_Forecast"],
    marker="o",
    color="green",
    linewidth=2,
    label="Forecast Orders"
)

plt.plot(
    forecast_df["Month"],
    forecast_df["Order_Target"],
    marker="s",
    linestyle="--",
    color="red",
    label="Order Target"
)

plt.fill_between(
    forecast_df["Month"],
    forecast_df["Orders_CI_Lower"],
    forecast_df["Orders_CI_Upper"],
    color="green",
    alpha=0.20,
    label="95% Confidence Interval"
)

plt.title(
    "Monthly Orders: Actual vs Forecast vs Target",
    fontsize=15,
    fontweight="bold"
)

plt.xlabel("Month")
plt.ylabel("Orders")
plt.legend()
plt.xticks(rotation=30)
plt.tight_layout()

plt.savefig(
    OUTPUT_FOLDER / "02_Orders_Forecast.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 29. PRODUCT DEMAND FORECAST CHART
# ============================================================

top_products = (
    next_quarter_product_summary
    .head(15)
)

plt.figure(figsize=(12, 8))

sns.barplot(
    data=top_products,
    y="Product_Name",
    x="Next_Quarter_Demand",
    palette="Blues_r"
)

plt.title(
    "Top 15 Products by Forecasted Next-Quarter Demand",
    fontsize=15,
    fontweight="bold"
)

plt.xlabel("Forecasted Units")
plt.ylabel("Product")
plt.tight_layout()

plt.savefig(
    OUTPUT_FOLDER / "03_Product_Demand_Forecast.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 30. PRINT FINAL RESULTS
# ============================================================

print("\n" + "=" * 78)
print("NEXT 3-MONTH FORECAST")
print("=" * 78)

display_columns = [
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

print(
    forecast_df[
        display_columns
    ].to_string(index=False)
)

print("\n" + "=" * 78)
print("NEXT-QUARTER SUMMARY")
print("=" * 78)

print(
    f"\nRevenue forecast: "
    f"{next_quarter_revenue_forecast:,.2f}"
)

print(
    f"Revenue target: "
    f"{next_quarter_revenue_target:,.2f}"
)

print(
    f"Revenue target achievement: "
    f"{quarter_revenue_achievement:,.2f}%"
)

print(
    f"\nOrders forecast: "
    f"{next_quarter_orders_forecast:,.0f}"
)

print(
    f"Order target: "
    f"{next_quarter_order_target:,.0f}"
)

print(
    f"Order target achievement: "
    f"{quarter_order_achievement:,.2f}%"
)

print(
    f"\nProduct demand forecast: "
    f"{next_quarter_demand_forecast:,.0f} units"
)

print(
    f"\nManagement conclusion: "
    f"{quarter_target_conclusion}"
)

print("\n" + "=" * 78)
print("TOP 10 FORECASTED PRODUCTS")
print("=" * 78)

print(
    next_quarter_product_summary[
        [
            "Demand_Rank",
            "Product_ID",
            "Product_Name",
            "Category",
            "Next_Quarter_Demand",
            "Average_Demand_Trend_Percentage"
        ]
    ].head(10).to_string(index=False)
)

print("\n" + "=" * 78)
print("FORECASTING COMPLETED SUCCESSFULLY")
print("=" * 78)

print(f"\nExcel report saved in:\n{EXCEL_OUTPUT}")
print(f"\nCSV forecast saved in:\n{CSV_OUTPUT}")
print(f"\nCharts saved in:\n{OUTPUT_FOLDER}")