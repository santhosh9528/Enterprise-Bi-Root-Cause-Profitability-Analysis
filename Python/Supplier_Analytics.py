from getpass import getpass
# ============================================================
# PART 13: SUPPLIER ANALYTICS
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
# 2. PERFORMANCE SCORE WEIGHTS
# ============================================================

ON_TIME_WEIGHT = 0.30
QUALITY_WEIGHT = 0.25
LEAD_TIME_WEIGHT = 0.20
PRICE_STABILITY_WEIGHT = 0.15
REJECTION_WEIGHT = 0.10


# ============================================================
# 3. OUTPUT LOCATION
# ============================================================

CURRENT_FOLDER = Path(__file__).resolve().parent
PROJECT_FOLDER = CURRENT_FOLDER.parent

OUTPUT_FOLDER = PROJECT_FOLDER / "Supplier_Analysis"
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

EXCEL_OUTPUT = OUTPUT_FOLDER / "Supplier_Analytics_Report.xlsx"
CSV_OUTPUT = OUTPUT_FOLDER / "Supplier_Performance_Summary.csv"

print("=" * 75)
print("SUPPLIER ANALYTICS STARTED")
print("=" * 75)


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
# 5. LOAD DATA
# ============================================================

purchases_df = pd.read_sql(
    "SELECT * FROM purchases",
    connection
)

suppliers_df = pd.read_sql(
    "SELECT * FROM suppliers",
    connection
)

connection.close()

print(f"Purchase records loaded: {len(purchases_df):,}")
print(f"Supplier records loaded: {len(suppliers_df):,}")
print("MySQL connection closed.")


# ============================================================
# 6. COLUMN HELPER FUNCTIONS
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


def min_max_score(series, higher_is_better=True):
    series = pd.to_numeric(
        series,
        errors="coerce"
    ).fillna(0)

    minimum_value = series.min()
    maximum_value = series.max()

    if maximum_value == minimum_value:
        return pd.Series(
            100,
            index=series.index,
            dtype=float
        )

    normalized_score = (
        series - minimum_value
    ) / (
        maximum_value - minimum_value
    ) * 100

    if higher_is_better:
        return normalized_score

    return 100 - normalized_score


# ============================================================
# 7. IDENTIFY PURCHASE COLUMNS
# ============================================================

purchase_supplier_col = find_column(
    purchases_df,
    ["Supplier_ID", "SupplierID"]
)

purchase_product_col = find_column(
    purchases_df,
    ["Product_ID", "ProductID"]
)

purchase_date_col = find_column(
    purchases_df,
    ["Purchase_Date", "Order_Date", "Date"]
)

purchase_quantity_col = find_column(
    purchases_df,
    [
        "Quantity",
        "Purchase_Quantity",
        "Ordered_Quantity"
    ]
)

unit_cost_col = find_column(
    purchases_df,
    [
        "Unit_Cost",
        "Purchase_Price",
        "Unit_Price",
        "Price"
    ]
)

purchase_value_col = find_column(
    purchases_df,
    [
        "Total_Cost",
        "Purchase_Value",
        "Total_Amount",
        "Amount"
    ],
    required=False
)

expected_delivery_col = find_column(
    purchases_df,
    [
        "Expected_Date",
        "Expected_Delivery_Date",
        "Scheduled_Delivery_Date",
        "ExpectedDeliveryDate"
    ]
)

actual_delivery_col = find_column(
    purchases_df,
    [
        "Delivery_Date",
        "Actual_Delivery_Date",
        "ActualDeliveryDate"
    ]
)
rejected_quantity_col = find_column(
    purchases_df,
    [
        "Rejected_Quantity",
        "Rejection_Quantity",
        "Rejected_Qty",
        "Defective_Quantity"
    ],
    required=False
)

quality_col = find_column(
    purchases_df,
    [
        "Quality_Score",
        "Quality_Rating",
        "Quality"
    ],
    required=False
)


# ============================================================
# 8. IDENTIFY SUPPLIER MASTER COLUMNS
# ============================================================

supplier_id_col = find_column(
    suppliers_df,
    ["Supplier_ID", "SupplierID"]
)

supplier_name_col = find_column(
    suppliers_df,
    ["Supplier_Name", "SupplierName", "Name"]
)

supplier_region_col = find_column(
    suppliers_df,
    ["Region", "Region_ID", "Location"],
    required=False
)

supplier_rating_col = find_column(
    suppliers_df,
    [
        "Rating",
        "Supplier_Rating",
        "Quality_Rating"
    ],
    required=False
)


# ============================================================
# 9. CLEAN PURCHASE DATA
# ============================================================

purchases_df[purchase_date_col] = pd.to_datetime(
    purchases_df[purchase_date_col],
    errors="coerce"
)

purchases_df[expected_delivery_col] = pd.to_datetime(
    purchases_df[expected_delivery_col],
    errors="coerce"
)

purchases_df[actual_delivery_col] = pd.to_datetime(
    purchases_df[actual_delivery_col],
    errors="coerce"
)

purchases_df["Quantity_Clean"] = numeric_series(
    purchases_df,
    purchase_quantity_col
)

purchases_df["Unit_Cost_Clean"] = numeric_series(
    purchases_df,
    unit_cost_col
)

purchases_df["Rejected_Quantity_Clean"] = (
    numeric_series(
        purchases_df,
        rejected_quantity_col
    )
)

if purchase_value_col:
    purchases_df["Purchase_Value_Clean"] = numeric_series(
        purchases_df,
        purchase_value_col
    )
else:
    purchases_df["Purchase_Value_Clean"] = (
        purchases_df["Quantity_Clean"]
        * purchases_df["Unit_Cost_Clean"]
    )

purchases_df["Delivery_Time_Days"] = (
    purchases_df[actual_delivery_col]
    - purchases_df[purchase_date_col]
).dt.days

purchases_df["Delivery_Delay_Days"] = (
    purchases_df[actual_delivery_col]
    - purchases_df[expected_delivery_col]
).dt.days

purchases_df["On_Time_Flag"] = np.where(
    purchases_df["Delivery_Delay_Days"] <= 0,
    1,
    0
)

purchases_df["Rejection_Rate"] = np.where(
    purchases_df["Quantity_Clean"] > 0,
    purchases_df["Rejected_Quantity_Clean"]
    / purchases_df["Quantity_Clean"]
    * 100,
    0
)

if quality_col:
    purchases_df["Purchase_Quality_Score"] = (
        numeric_series(
            purchases_df,
            quality_col
        )
    )
else:
    purchases_df["Purchase_Quality_Score"] = (
        100 - purchases_df["Rejection_Rate"]
    ).clip(lower=0, upper=100)


# ============================================================
# 10. PRICE VARIATION BY SUPPLIER
# ============================================================

price_statistics = (
    purchases_df
    .groupby(purchase_supplier_col)
    .agg(
        Average_Unit_Cost=(
            "Unit_Cost_Clean",
            "mean"
        ),
        Unit_Cost_Standard_Deviation=(
            "Unit_Cost_Clean",
            "std"
        ),
        Minimum_Unit_Cost=(
            "Unit_Cost_Clean",
            "min"
        ),
        Maximum_Unit_Cost=(
            "Unit_Cost_Clean",
            "max"
        )
    )
    .reset_index()
    .rename(
        columns={
            purchase_supplier_col: "Supplier_ID"
        }
    )
)

price_statistics[
    "Unit_Cost_Standard_Deviation"
] = price_statistics[
    "Unit_Cost_Standard_Deviation"
].fillna(0)

price_statistics["Price_Variation_Percentage"] = np.where(
    price_statistics["Average_Unit_Cost"] > 0,
    price_statistics[
        "Unit_Cost_Standard_Deviation"
    ]
    / price_statistics["Average_Unit_Cost"]
    * 100,
    0
)


# ============================================================
# 11. SUPPLIER PURCHASE PERFORMANCE
# ============================================================

supplier_purchase_summary = (
    purchases_df
    .groupby(purchase_supplier_col)
    .agg(
        Purchase_Order_Count=(
            purchase_supplier_col,
            "size"
        ),
        Product_Count=(
            purchase_product_col,
            "nunique"
        ),
        Purchase_Quantity=(
            "Quantity_Clean",
            "sum"
        ),
        Purchase_Value=(
            "Purchase_Value_Clean",
            "sum"
        ),
        Average_Delivery_Time_Days=(
            "Delivery_Time_Days",
            "mean"
        ),
        Average_Delivery_Delay_Days=(
            "Delivery_Delay_Days",
            "mean"
        ),
        On_Time_Deliveries=(
            "On_Time_Flag",
            "sum"
        ),
        Total_Deliveries=(
            "On_Time_Flag",
            "count"
        ),
        Rejected_Quantity=(
            "Rejected_Quantity_Clean",
            "sum"
        ),
        Average_Quality_Score=(
            "Purchase_Quality_Score",
            "mean"
        )
    )
    .reset_index()
    .rename(
        columns={
            purchase_supplier_col: "Supplier_ID"
        }
    )
)

supplier_purchase_summary[
    "On_Time_Delivery_Percentage"
] = np.where(
    supplier_purchase_summary["Total_Deliveries"] > 0,
    supplier_purchase_summary["On_Time_Deliveries"]
    / supplier_purchase_summary["Total_Deliveries"]
    * 100,
    0
)

supplier_purchase_summary[
    "Rejection_Rate_Percentage"
] = np.where(
    supplier_purchase_summary["Purchase_Quantity"] > 0,
    supplier_purchase_summary["Rejected_Quantity"]
    / supplier_purchase_summary["Purchase_Quantity"]
    * 100,
    0
)


# ============================================================
# 12. PREPARE SUPPLIER MASTER
# ============================================================

supplier_columns = [
    supplier_id_col,
    supplier_name_col
]

if supplier_region_col:
    supplier_columns.append(supplier_region_col)

if supplier_rating_col:
    supplier_columns.append(supplier_rating_col)

supplier_master = suppliers_df[
    supplier_columns
].copy()

supplier_rename = {
    supplier_id_col: "Supplier_ID",
    supplier_name_col: "Supplier_Name"
}

if supplier_region_col:
    supplier_rename[
        supplier_region_col
    ] = "Supplier_Region"

if supplier_rating_col:
    supplier_rename[
        supplier_rating_col
    ] = "Master_Supplier_Rating"

supplier_master = supplier_master.rename(
    columns=supplier_rename
)


# ============================================================
# 13. MERGE SUPPLIER DATA
# ============================================================

supplier_performance = supplier_master.merge(
    supplier_purchase_summary,
    on="Supplier_ID",
    how="left"
)

supplier_performance = supplier_performance.merge(
    price_statistics,
    on="Supplier_ID",
    how="left"
)

numeric_columns = supplier_performance.select_dtypes(
    include=[np.number]
).columns

supplier_performance[numeric_columns] = (
    supplier_performance[numeric_columns]
    .fillna(0)
)


# ============================================================
# 14. CREATE COMPONENT SCORES
# ============================================================

supplier_performance["On_Time_Score"] = (
    supplier_performance[
        "On_Time_Delivery_Percentage"
    ].clip(lower=0, upper=100)
)

supplier_performance["Quality_Score"] = (
    supplier_performance[
        "Average_Quality_Score"
    ].clip(lower=0, upper=100)
)

supplier_performance["Lead_Time_Score"] = min_max_score(
    supplier_performance[
        "Average_Delivery_Time_Days"
    ],
    higher_is_better=False
)

supplier_performance["Price_Stability_Score"] = min_max_score(
    supplier_performance[
        "Price_Variation_Percentage"
    ],
    higher_is_better=False
)

supplier_performance["Rejection_Score"] = (
    100
    - supplier_performance[
        "Rejection_Rate_Percentage"
    ]
).clip(lower=0, upper=100)


# ============================================================
# 15. FINAL SUPPLIER PERFORMANCE SCORE
# ============================================================

supplier_performance[
    "Supplier_Performance_Score"
] = (
    supplier_performance["On_Time_Score"]
    * ON_TIME_WEIGHT

    + supplier_performance["Quality_Score"]
    * QUALITY_WEIGHT

    + supplier_performance["Lead_Time_Score"]
    * LEAD_TIME_WEIGHT

    + supplier_performance["Price_Stability_Score"]
    * PRICE_STABILITY_WEIGHT

    + supplier_performance["Rejection_Score"]
    * REJECTION_WEIGHT
)


# ============================================================
# 16. SUPPLIER RANKING
# ============================================================

supplier_performance["Supplier_Rank"] = (
    supplier_performance[
        "Supplier_Performance_Score"
    ]
    .rank(
        method="dense",
        ascending=False
    )
    .astype(int)
)


# ============================================================
# 17. SUPPLIER CLASSIFICATION
# ============================================================

def supplier_classification(score):
    if score >= 85:
        return "Preferred Supplier"

    if score >= 70:
        return "Good Supplier"

    if score >= 55:
        return "Monitor"

    if score >= 40:
        return "Renegotiate"

    return "Critical Review"


supplier_performance["Supplier_Status"] = (
    supplier_performance[
        "Supplier_Performance_Score"
    ].apply(supplier_classification)
)


# ============================================================
# 18. SPLIT DATA INTO PREVIOUS AND RECENT PERIODS
# ============================================================

minimum_date = purchases_df[
    purchase_date_col
].min()

maximum_date = purchases_df[
    purchase_date_col
].max()

midpoint_date = minimum_date + (
    maximum_date - minimum_date
) / 2

purchases_df["Analysis_Period"] = np.where(
    purchases_df[purchase_date_col] <= midpoint_date,
    "Previous Period",
    "Recent Period"
)

period_summary = (
    purchases_df
    .groupby(
        [
            purchase_supplier_col,
            "Analysis_Period"
        ]
    )
    .agg(
        Average_Unit_Cost=(
            "Unit_Cost_Clean",
            "mean"
        ),
        Average_Delivery_Time_Days=(
            "Delivery_Time_Days",
            "mean"
        ),
        On_Time_Delivery_Percentage=(
            "On_Time_Flag",
            "mean"
        ),
        Rejection_Rate_Percentage=(
            "Rejection_Rate",
            "mean"
        ),
        Average_Quality_Score=(
            "Purchase_Quality_Score",
            "mean"
        ),
        Purchase_Value=(
            "Purchase_Value_Clean",
            "sum"
        )
    )
    .reset_index()
)

period_summary[
    "On_Time_Delivery_Percentage"
] = (
    period_summary[
        "On_Time_Delivery_Percentage"
    ] * 100
)


# ============================================================
# 19. CREATE PREVIOUS VS RECENT COMPARISON
# ============================================================

period_pivot = period_summary.pivot(
    index=purchase_supplier_col,
    columns="Analysis_Period"
)

period_pivot.columns = [
    f"{metric}_{period.replace(' ', '_')}"
    for metric, period in period_pivot.columns
]

period_pivot = (
    period_pivot
    .reset_index()
    .rename(
        columns={
            purchase_supplier_col: "Supplier_ID"
        }
    )
)

required_comparison_columns = [
    "Average_Unit_Cost_Previous_Period",
    "Average_Unit_Cost_Recent_Period",
    "Average_Delivery_Time_Days_Previous_Period",
    "Average_Delivery_Time_Days_Recent_Period",
    "On_Time_Delivery_Percentage_Previous_Period",
    "On_Time_Delivery_Percentage_Recent_Period",
    "Rejection_Rate_Percentage_Previous_Period",
    "Rejection_Rate_Percentage_Recent_Period",
    "Average_Quality_Score_Previous_Period",
    "Average_Quality_Score_Recent_Period"
]

for column in required_comparison_columns:
    if column not in period_pivot.columns:
        period_pivot[column] = 0


# ============================================================
# 20. CALCULATE PERFORMANCE CHANGES
# ============================================================

period_pivot["Unit_Cost_Change_Percentage"] = np.where(
    period_pivot[
        "Average_Unit_Cost_Previous_Period"
    ] > 0,

    (
        period_pivot[
            "Average_Unit_Cost_Recent_Period"
        ]
        - period_pivot[
            "Average_Unit_Cost_Previous_Period"
        ]
    )
    / period_pivot[
        "Average_Unit_Cost_Previous_Period"
    ]
    * 100,

    0
)

period_pivot["Delivery_Time_Change_Days"] = (
    period_pivot[
        "Average_Delivery_Time_Days_Recent_Period"
    ]
    - period_pivot[
        "Average_Delivery_Time_Days_Previous_Period"
    ]
)

period_pivot["On_Time_Change_Percentage_Points"] = (
    period_pivot[
        "On_Time_Delivery_Percentage_Recent_Period"
    ]
    - period_pivot[
        "On_Time_Delivery_Percentage_Previous_Period"
    ]
)

period_pivot["Rejection_Rate_Change"] = (
    period_pivot[
        "Rejection_Rate_Percentage_Recent_Period"
    ]
    - period_pivot[
        "Rejection_Rate_Percentage_Previous_Period"
    ]
)

period_pivot["Quality_Change"] = (
    period_pivot[
        "Average_Quality_Score_Recent_Period"
    ]
    - period_pivot[
        "Average_Quality_Score_Previous_Period"
    ]
)


# ============================================================
# 21. IDENTIFY DECLINING SUPPLIERS
# Purchase cost ↑ + Delivery ↓ + Quality ↓
# ============================================================

period_pivot["Cost_Increased"] = np.where(
    period_pivot["Unit_Cost_Change_Percentage"] > 0,
    1,
    0
)

period_pivot["Delivery_Performance_Decreased"] = np.where(
    (
        period_pivot["Delivery_Time_Change_Days"] > 0
    )
    |
    (
        period_pivot[
            "On_Time_Change_Percentage_Points"
        ] < 0
    ),
    1,
    0
)

period_pivot["Quality_Decreased"] = np.where(
    (
        period_pivot["Quality_Change"] < 0
    )
    |
    (
        period_pivot["Rejection_Rate_Change"] > 0
    ),
    1,
    0
)

period_pivot["Decline_Factor_Count"] = (
    period_pivot["Cost_Increased"]
    + period_pivot[
        "Delivery_Performance_Decreased"
    ]
    + period_pivot["Quality_Decreased"]
)

period_pivot["Trend_Status"] = np.select(
    [
        period_pivot["Decline_Factor_Count"] == 3,
        period_pivot["Decline_Factor_Count"] == 2,
        period_pivot["Decline_Factor_Count"] == 1
    ],
    [
        "Cost Up + Delivery Down + Quality Down",
        "Multiple Performance Issues",
        "One Performance Issue"
    ],
    default="Stable / Improving"
)


# ============================================================
# 22. MERGE TREND WITH SUPPLIER PERFORMANCE
# ============================================================

supplier_performance = supplier_performance.merge(
    period_pivot[
        [
            "Supplier_ID",
            "Unit_Cost_Change_Percentage",
            "Delivery_Time_Change_Days",
            "On_Time_Change_Percentage_Points",
            "Rejection_Rate_Change",
            "Quality_Change",
            "Decline_Factor_Count",
            "Trend_Status"
        ]
    ],
    on="Supplier_ID",
    how="left"
)

trend_numeric_columns = [
    "Unit_Cost_Change_Percentage",
    "Delivery_Time_Change_Days",
    "On_Time_Change_Percentage_Points",
    "Rejection_Rate_Change",
    "Quality_Change",
    "Decline_Factor_Count"
]

supplier_performance[
    trend_numeric_columns
] = supplier_performance[
    trend_numeric_columns
].fillna(0)

supplier_performance["Trend_Status"] = (
    supplier_performance["Trend_Status"]
    .fillna("Insufficient Trend Data")
)


# ============================================================
# 23. FINAL REVIEW PRIORITY
# ============================================================

def review_priority(row):
    if (
        row["Decline_Factor_Count"] == 3
        or row["Supplier_Status"] == "Critical Review"
    ):
        return "Critical"

    if (
        row["Decline_Factor_Count"] == 2
        or row["Supplier_Status"] == "Renegotiate"
    ):
        return "High"

    if row["Supplier_Status"] == "Monitor":
        return "Medium"

    return "Low"


supplier_performance["Review_Priority"] = (
    supplier_performance.apply(
        review_priority,
        axis=1
    )
)


# ============================================================
# 24. RECOMMENDED ACTION
# ============================================================

def recommended_action(row):
    if row["Decline_Factor_Count"] == 3:
        return (
            "Renegotiate pricing and SLA immediately; conduct "
            "quality audit and evaluate alternate supplier."
        )

    if row["Supplier_Status"] == "Critical Review":
        return (
            "Place supplier under formal review and shift critical "
            "purchase volume to better-performing suppliers."
        )

    if row["Supplier_Status"] == "Renegotiate":
        return (
            "Renegotiate price, lead time and rejection terms "
            "before contract renewal."
        )

    if row["Supplier_Status"] == "Monitor":
        return (
            "Monitor monthly score and create corrective-action "
            "targets for delivery and quality."
        )

    if row["Supplier_Status"] == "Preferred Supplier":
        return (
            "Consider increasing purchase allocation while "
            "maintaining price and quality controls."
        )

    return (
        "Continue current relationship with periodic monitoring."
    )


supplier_performance["Recommended_Action"] = (
    supplier_performance.apply(
        recommended_action,
        axis=1
    )
)


# ============================================================
# 25. SORT AND CREATE OUTPUT TABLES
# ============================================================

supplier_performance = supplier_performance.sort_values(
    [
        "Supplier_Performance_Score",
        "Purchase_Value"
    ],
    ascending=[False, False]
).reset_index(drop=True)

top_suppliers = supplier_performance.head(20).copy()

bottom_suppliers = supplier_performance.sort_values(
    "Supplier_Performance_Score"
).head(20).copy()

declining_suppliers = supplier_performance[
    supplier_performance[
        "Decline_Factor_Count"
    ] == 3
].copy()

declining_suppliers = declining_suppliers.sort_values(
    [
        "Unit_Cost_Change_Percentage",
        "Supplier_Performance_Score"
    ],
    ascending=[False, True]
)

review_suppliers = supplier_performance[
    supplier_performance[
        "Review_Priority"
    ].isin(["Critical", "High"])
].copy()


# ============================================================
# 26. STATUS SUMMARY
# ============================================================

status_summary = (
    supplier_performance
    .groupby(
        [
            "Supplier_Status",
            "Review_Priority"
        ]
    )
    .agg(
        Supplier_Count=(
            "Supplier_ID",
            "nunique"
        ),
        Purchase_Value=(
            "Purchase_Value",
            "sum"
        ),
        Average_Performance_Score=(
            "Supplier_Performance_Score",
            "mean"
        ),
        Average_On_Time_Rate=(
            "On_Time_Delivery_Percentage",
            "mean"
        ),
        Average_Rejection_Rate=(
            "Rejection_Rate_Percentage",
            "mean"
        ),
        Average_Lead_Time=(
            "Average_Delivery_Time_Days",
            "mean"
        )
    )
    .reset_index()
)

status_summary["Supplier_Percentage"] = (
    status_summary["Supplier_Count"]
    / supplier_performance[
        "Supplier_ID"
    ].nunique()
    * 100
)


# ============================================================
# 27. EXECUTIVE SUMMARY
# ============================================================

best_supplier = supplier_performance.iloc[0]

worst_supplier = supplier_performance.sort_values(
    "Supplier_Performance_Score"
).iloc[0]

executive_summary = pd.DataFrame(
    {
        "Metric": [
            "Total Suppliers",
            "Total Purchase Value",
            "Average Delivery Time (Days)",
            "Overall On-Time Delivery (%)",
            "Overall Rejection Rate (%)",
            "Average Supplier Score",
            "Preferred Suppliers",
            "Suppliers for Critical Review",
            "Declining Suppliers",
            "Best Supplier",
            "Best Supplier Score",
            "Lowest-Ranked Supplier",
            "Lowest Supplier Score"
        ],

        "Value": [
            supplier_performance[
                "Supplier_ID"
            ].nunique(),

            supplier_performance[
                "Purchase_Value"
            ].sum(),

            supplier_performance[
                "Average_Delivery_Time_Days"
            ].mean(),

            supplier_performance[
                "On_Time_Delivery_Percentage"
            ].mean(),

            supplier_performance[
                "Rejection_Rate_Percentage"
            ].mean(),

            supplier_performance[
                "Supplier_Performance_Score"
            ].mean(),

            (
                supplier_performance[
                    "Supplier_Status"
                ] == "Preferred Supplier"
            ).sum(),

            (
                supplier_performance[
                    "Review_Priority"
                ] == "Critical"
            ).sum(),

            len(declining_suppliers),

            best_supplier["Supplier_Name"],

            best_supplier[
                "Supplier_Performance_Score"
            ],

            worst_supplier["Supplier_Name"],

            worst_supplier[
                "Supplier_Performance_Score"
            ]
        ]
    }
)


# ============================================================
# 28. ROUND NUMERIC COLUMNS
# ============================================================

for dataframe in [
    supplier_performance,
    top_suppliers,
    bottom_suppliers,
    declining_suppliers,
    review_suppliers,
    status_summary,
    period_pivot
]:
    numeric_cols = dataframe.select_dtypes(
        include=[np.number]
    ).columns

    dataframe[numeric_cols] = dataframe[
        numeric_cols
    ].round(2)


# ============================================================
# 29. SAVE CSV
# ============================================================

supplier_performance.to_csv(
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

    executive_summary.to_excel(
        writer,
        sheet_name="Executive_Summary",
        index=False
    )

    status_summary.to_excel(
        writer,
        sheet_name="Status_Summary",
        index=False
    )

    supplier_performance.to_excel(
        writer,
        sheet_name="Supplier_Performance",
        index=False
    )

    top_suppliers.to_excel(
        writer,
        sheet_name="Top_Suppliers",
        index=False
    )

    bottom_suppliers.to_excel(
        writer,
        sheet_name="Bottom_Suppliers",
        index=False
    )

    declining_suppliers.to_excel(
        writer,
        sheet_name="Declining_Suppliers",
        index=False
    )

    review_suppliers.to_excel(
        writer,
        sheet_name="Review_Suppliers",
        index=False
    )

    period_pivot.to_excel(
        writer,
        sheet_name="Period_Comparison",
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
# 31. CREATE CHARTS
# ============================================================

sns.set_theme(style="whitegrid")


# Chart 1: Top supplier scores

chart_top = supplier_performance.head(15)

plt.figure(figsize=(12, 8))

sns.barplot(
    data=chart_top,
    y="Supplier_Name",
    x="Supplier_Performance_Score",
    palette="Greens_r"
)

plt.title(
    "Top 15 Suppliers by Performance Score",
    fontsize=15,
    fontweight="bold"
)

plt.xlabel("Supplier Performance Score")
plt.ylabel("Supplier")
plt.xlim(0, 100)
plt.tight_layout()

plt.savefig(
    OUTPUT_FOLDER / "01_Top_Suppliers.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# Chart 2: Bottom supplier scores

chart_bottom = supplier_performance.sort_values(
    "Supplier_Performance_Score"
).head(15)

plt.figure(figsize=(12, 8))

sns.barplot(
    data=chart_bottom,
    y="Supplier_Name",
    x="Supplier_Performance_Score",
    palette="Reds"
)

plt.title(
    "Bottom 15 Suppliers by Performance Score",
    fontsize=15,
    fontweight="bold"
)

plt.xlabel("Supplier Performance Score")
plt.ylabel("Supplier")
plt.xlim(0, 100)
plt.tight_layout()

plt.savefig(
    OUTPUT_FOLDER / "02_Bottom_Suppliers.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# Chart 3: Cost variation vs on-time delivery

plt.figure(figsize=(11, 7))

sns.scatterplot(
    data=supplier_performance,
    x="Price_Variation_Percentage",
    y="On_Time_Delivery_Percentage",
    hue="Supplier_Status",
    size="Purchase_Value",
    sizes=(30, 250),
    alpha=0.75
)

plt.title(
    "Supplier Price Variation vs On-Time Delivery",
    fontsize=15,
    fontweight="bold"
)

plt.xlabel("Price Variation (%)")
plt.ylabel("On-Time Delivery (%)")
plt.tight_layout()

plt.savefig(
    OUTPUT_FOLDER / "03_Price_vs_Delivery.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 32. PRINT RESULTS
# ============================================================

print("\n" + "=" * 75)
print("SUPPLIER EXECUTIVE SUMMARY")
print("=" * 75)

print(executive_summary.to_string(index=False))

print("\n" + "=" * 75)
print("SUPPLIER STATUS SUMMARY")
print("=" * 75)

print(status_summary.to_string(index=False))

display_columns = [
    "Supplier_Rank",
    "Supplier_ID",
    "Supplier_Name",
    "Purchase_Value",
    "Average_Delivery_Time_Days",
    "On_Time_Delivery_Percentage",
    "Rejection_Rate_Percentage",
    "Price_Variation_Percentage",
    "Average_Quality_Score",
    "Supplier_Performance_Score",
    "Supplier_Status",
    "Review_Priority"
]

print("\n" + "=" * 75)
print("TOP 10 SUPPLIERS")
print("=" * 75)

print(
    top_suppliers[
        display_columns
    ].head(10).to_string(index=False)
)

print("\n" + "=" * 75)
print("BOTTOM 10 SUPPLIERS")
print("=" * 75)

print(
    bottom_suppliers[
        display_columns
    ].head(10).to_string(index=False)
)

print("\n" + "=" * 75)
print("COST UP + DELIVERY DOWN + QUALITY DOWN")
print("=" * 75)

declining_display_columns = [
    "Supplier_ID",
    "Supplier_Name",
    "Unit_Cost_Change_Percentage",
    "Delivery_Time_Change_Days",
    "On_Time_Change_Percentage_Points",
    "Rejection_Rate_Change",
    "Quality_Change",
    "Supplier_Performance_Score",
    "Review_Priority",
    "Recommended_Action"
]

if declining_suppliers.empty:
    print(
        "All three decline conditions match panna "
        "supplier illa."
    )
else:
    print(
        declining_suppliers[
            declining_display_columns
        ].head(20).to_string(index=False)
    )

print("\n" + "=" * 75)
print("SUPPLIER ANALYTICS COMPLETED SUCCESSFULLY")
print("=" * 75)

print(f"\nExcel report saved in:\n{EXCEL_OUTPUT}")
print(f"\nCSV report saved in:\n{CSV_OUTPUT}")
print(f"\nCharts saved in:\n{OUTPUT_FOLDER}")