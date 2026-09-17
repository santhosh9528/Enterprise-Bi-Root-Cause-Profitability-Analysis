from getpass import getpass
# ============================================================
# PART 15: MULTI-FACTOR ANOMALY DETECTION
# Sales, Refunds, Discounts, Payments and Inventory
# ============================================================

from pathlib import Path
import warnings

import mysql.connector
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler

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
# 2. MODEL CONFIGURATION
# ============================================================

RANDOM_STATE = 42
CONTAMINATION_RATE = 0.01
TOP_RECORDS_PER_DATASET = 500


# ============================================================
# 3. OUTPUT LOCATION
# ============================================================

CURRENT_FOLDER = Path(__file__).resolve().parent
PROJECT_FOLDER = CURRENT_FOLDER.parent

OUTPUT_FOLDER = PROJECT_FOLDER / "Anomaly_Analysis"
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

EXCEL_OUTPUT = OUTPUT_FOLDER / "Anomaly_Detection_Report.xlsx"
CSV_OUTPUT = OUTPUT_FOLDER / "Top_Suspicious_Records.csv"

print("=" * 78)
print("MULTI-FACTOR ANOMALY DETECTION STARTED")
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
# 5. LOAD DATA
# ============================================================

sales_df = pd.read_sql(
    "SELECT * FROM vw_sales_profitability",
    connection
)

payments_df = pd.read_sql(
    "SELECT * FROM payments",
    connection
)

inventory_df = pd.read_sql(
    "SELECT * FROM inventory",
    connection
)

connection.close()

print(f"Sales records loaded: {len(sales_df):,}")
print(f"Payment records loaded: {len(payments_df):,}")
print(f"Inventory records loaded: {len(inventory_df):,}")
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


def robust_z_score(series):
    series = pd.to_numeric(
        series,
        errors="coerce"
    ).fillna(0)

    median_value = series.median()

    median_absolute_deviation = (
        series - median_value
    ).abs().median()

    if median_absolute_deviation == 0:
        standard_deviation = series.std()

        if standard_deviation == 0:
            return pd.Series(
                0,
                index=series.index,
                dtype=float
            )

        return (
            series - series.mean()
        ) / standard_deviation

    return (
        0.6745
        * (series - median_value)
        / median_absolute_deviation
    )


def percentile_score(series):
    return (
        pd.Series(series)
        .rank(
            method="average",
            pct=True
        )
        * 100
    )


def run_isolation_forest(
    dataframe,
    feature_columns
):
    feature_data = dataframe[
        feature_columns
    ].copy()

    feature_data = feature_data.replace(
        [np.inf, -np.inf],
        np.nan
    ).fillna(0)

    scaler = RobustScaler()

    scaled_features = scaler.fit_transform(
        feature_data
    )

    model = IsolationForest(
        n_estimators=200,
        contamination=CONTAMINATION_RATE,
        random_state=RANDOM_STATE,
        n_jobs=-1
    )

    model.fit(scaled_features)

    raw_anomaly_score = (
        -model.decision_function(
            scaled_features
        )
    )

    anomaly_prediction = model.predict(
        scaled_features
    )

    model_score = percentile_score(
        raw_anomaly_score
    )

    return (
        model_score,
        anomaly_prediction
    )


def assign_priority(score):
    if score >= 90:
        return "Critical"

    if score >= 75:
        return "High"

    if score >= 60:
        return "Medium"

    return "Low"


# ============================================================
# 7. IDENTIFY SALES COLUMNS
# ============================================================

sale_id_col = find_column(
    sales_df,
    ["Sale_ID", "Sales_ID", "Transaction_ID"]
)

sale_order_col = find_column(
    sales_df,
    ["Order_ID"]
)

sale_customer_col = find_column(
    sales_df,
    ["Customer_ID"]
)

sale_product_col = find_column(
    sales_df,
    ["Product_ID"]
)

sale_date_col = find_column(
    sales_df,
    ["Sale_Date", "Sales_Date", "Order_Date"]
)

sale_quantity_col = find_column(
    sales_df,
    ["Quantity", "Sales_Quantity"]
)

sale_revenue_col = find_column(
    sales_df,
    ["Revenue", "Sales_Amount", "Net_Sales"]
)

sale_discount_col = find_column(
    sales_df,
    ["Discount", "Discount_Amount"],
    required=False
)

sale_refund_col = find_column(
    sales_df,
    ["Refunds", "Refund", "Refund_Amount"],
    required=False
)

sale_profit_col = find_column(
    sales_df,
    ["Net_Profit", "Profit"],
    required=False
)


# ============================================================
# 8. PREPARE SALES FEATURES
# ============================================================

sales_analysis = pd.DataFrame(
    {
        "Record_ID": sales_df[sale_id_col],
        "Order_ID": sales_df[sale_order_col],
        "Customer_ID": sales_df[sale_customer_col],
        "Product_ID": sales_df[sale_product_col],
        "Transaction_Date": pd.to_datetime(
            sales_df[sale_date_col],
            errors="coerce"
        ),
        "Quantity": numeric_series(
            sales_df,
            sale_quantity_col
        ),
        "Transaction_Amount": numeric_series(
            sales_df,
            sale_revenue_col
        ),
        "Discount": numeric_series(
            sales_df,
            sale_discount_col
        ),
        "Refund": numeric_series(
            sales_df,
            sale_refund_col
        ),
        "Net_Profit": numeric_series(
            sales_df,
            sale_profit_col
        )
    }
)

sales_analysis["Discount_Rate"] = np.where(
    sales_analysis["Transaction_Amount"] > 0,
    sales_analysis["Discount"]
    / sales_analysis["Transaction_Amount"]
    * 100,
    0
)

sales_analysis["Refund_Rate"] = np.where(
    sales_analysis["Transaction_Amount"] > 0,
    sales_analysis["Refund"]
    / sales_analysis["Transaction_Amount"]
    * 100,
    0
)

sales_analysis["Customer_Transaction_Frequency"] = (
    sales_analysis["Customer_ID"]
    .map(
        sales_analysis[
            "Customer_ID"
        ].value_counts()
    )
)

sales_analysis["Product_Transaction_Frequency"] = (
    sales_analysis["Product_ID"]
    .map(
        sales_analysis[
            "Product_ID"
        ].value_counts()
    )
)

sales_analysis["Hour"] = (
    sales_analysis["Transaction_Date"]
    .dt.hour
    .fillna(0)
)

sales_analysis["Weekend_Flag"] = (
    sales_analysis["Transaction_Date"]
    .dt.dayofweek
    .isin([5, 6])
    .astype(int)
)

customer_average_amount = (
    sales_analysis
    .groupby("Customer_ID")[
        "Transaction_Amount"
    ]
    .transform("mean")
)

customer_amount_std = (
    sales_analysis
    .groupby("Customer_ID")[
        "Transaction_Amount"
    ]
    .transform("std")
    .replace(0, np.nan)
)

sales_analysis[
    "Customer_Behaviour_Deviation"
] = (
    (
        sales_analysis["Transaction_Amount"]
        - customer_average_amount
    )
    / customer_amount_std
).replace(
    [np.inf, -np.inf],
    0
).fillna(0).abs()

product_average_amount = (
    sales_analysis
    .groupby("Product_ID")[
        "Transaction_Amount"
    ]
    .transform("mean")
)

product_amount_std = (
    sales_analysis
    .groupby("Product_ID")[
        "Transaction_Amount"
    ]
    .transform("std")
    .replace(0, np.nan)
)

sales_analysis[
    "Product_Behaviour_Deviation"
] = (
    (
        sales_analysis["Transaction_Amount"]
        - product_average_amount
    )
    / product_amount_std
).replace(
    [np.inf, -np.inf],
    0
).fillna(0).abs()

sales_analysis["Amount_Robust_Z"] = (
    robust_z_score(
        sales_analysis["Transaction_Amount"]
    ).abs()
)

sales_analysis["Discount_Robust_Z"] = (
    robust_z_score(
        sales_analysis["Discount_Rate"]
    ).abs()
)

sales_analysis["Refund_Robust_Z"] = (
    robust_z_score(
        sales_analysis["Refund_Rate"]
    ).abs()
)

sales_analysis["Quantity_Robust_Z"] = (
    robust_z_score(
        sales_analysis["Quantity"]
    ).abs()
)


# ============================================================
# 9. SALES ISOLATION FOREST
# ============================================================

sales_features = [
    "Transaction_Amount",
    "Quantity",
    "Discount_Rate",
    "Refund_Rate",
    "Net_Profit",
    "Customer_Transaction_Frequency",
    "Product_Transaction_Frequency",
    "Customer_Behaviour_Deviation",
    "Product_Behaviour_Deviation",
    "Hour",
    "Weekend_Flag"
]

(
    sales_model_score,
    sales_prediction
) = run_isolation_forest(
    sales_analysis,
    sales_features
)

sales_analysis["Model_Anomaly_Score"] = (
    sales_model_score.values
)

sales_analysis["Model_Prediction"] = (
    sales_prediction
)

sales_factor_score = (
    percentile_score(
        sales_analysis["Amount_Robust_Z"]
    )
    + percentile_score(
        sales_analysis["Discount_Robust_Z"]
    )
    + percentile_score(
        sales_analysis["Refund_Robust_Z"]
    )
    + percentile_score(
        sales_analysis["Quantity_Robust_Z"]
    )
    + percentile_score(
        sales_analysis[
            "Customer_Behaviour_Deviation"
        ]
    )
    + percentile_score(
        sales_analysis[
            "Product_Behaviour_Deviation"
        ]
    )
) / 6

sales_analysis["Anomaly_Score"] = (
    sales_analysis["Model_Anomaly_Score"]
    * 0.60
    + sales_factor_score
    * 0.40
).clip(0, 100)

sales_analysis["Priority"] = (
    sales_analysis["Anomaly_Score"]
    .apply(assign_priority)
)


# ============================================================
# 10. SALES ANOMALY REASONS
# ============================================================

sales_amount_limit = sales_analysis[
    "Amount_Robust_Z"
].quantile(0.95)

sales_discount_limit = sales_analysis[
    "Discount_Robust_Z"
].quantile(0.95)

sales_refund_limit = sales_analysis[
    "Refund_Robust_Z"
].quantile(0.95)

sales_quantity_limit = sales_analysis[
    "Quantity_Robust_Z"
].quantile(0.95)


def sales_anomaly_reason(row):
    reasons = []

    if row["Amount_Robust_Z"] >= sales_amount_limit:
        reasons.append("Unusual transaction amount")

    if row["Discount_Robust_Z"] >= sales_discount_limit:
        reasons.append("Unusual discount")

    if row["Refund_Robust_Z"] >= sales_refund_limit:
        reasons.append("Unusual refund")

    if row["Quantity_Robust_Z"] >= sales_quantity_limit:
        reasons.append("Unusual quantity")

    if row["Customer_Behaviour_Deviation"] >= 3:
        reasons.append(
            "Different from customer history"
        )

    if row["Product_Behaviour_Deviation"] >= 3:
        reasons.append(
            "Different from product behaviour"
        )

    if row["Net_Profit"] < 0:
        reasons.append("Negative-profit transaction")

    if not reasons:
        reasons.append(
            "Multiple moderate-risk factors"
        )

    return "; ".join(reasons)


sales_analysis["Anomaly_Reason"] = (
    sales_analysis.apply(
        sales_anomaly_reason,
        axis=1
    )
)

sales_analysis["Dataset"] = "Sales"


# ============================================================
# 11. IDENTIFY PAYMENT COLUMNS
# ============================================================

payment_id_col = find_column(
    payments_df,
    ["Payment_ID", "Transaction_ID"]
)

payment_invoice_col = find_column(
    payments_df,
    ["Invoice_ID"]
)

payment_customer_col = find_column(
    payments_df,
    ["Customer_ID"]
)

payment_date_col = find_column(
    payments_df,
    ["Payment_Date", "Date"]
)

payment_amount_col = find_column(
    payments_df,
    [
        "Payment_Amount",
        "Amount",
        "Paid_Amount"
    ]
)

payment_status_col = find_column(
    payments_df,
    ["Payment_Status", "Status"],
    required=False
)


# ============================================================
# 12. PREPARE PAYMENT FEATURES
# ============================================================

payments_analysis = pd.DataFrame(
    {
        "Record_ID": payments_df[payment_id_col],
        "Invoice_ID": payments_df[payment_invoice_col],
        "Customer_ID": payments_df[payment_customer_col],
        "Transaction_Date": pd.to_datetime(
            payments_df[payment_date_col],
            errors="coerce"
        ),
        "Payment_Amount": numeric_series(
            payments_df,
            payment_amount_col
        )
    }
)

if payment_status_col:
    payments_analysis["Payment_Status"] = (
        payments_df[payment_status_col]
        .fillna("Unknown")
        .astype(str)
    )
else:
    payments_analysis[
        "Payment_Status"
    ] = "Unknown"

payments_analysis["Customer_Payment_Frequency"] = (
    payments_analysis["Customer_ID"]
    .map(
        payments_analysis[
            "Customer_ID"
        ].value_counts()
    )
)

payments_analysis["Invoice_Payment_Frequency"] = (
    payments_analysis["Invoice_ID"]
    .map(
        payments_analysis[
            "Invoice_ID"
        ].value_counts()
    )
)

payments_analysis["Payment_Day"] = (
    payments_analysis["Transaction_Date"]
    .dt.day
    .fillna(0)
)

payments_analysis["Weekend_Flag"] = (
    payments_analysis["Transaction_Date"]
    .dt.dayofweek
    .isin([5, 6])
    .astype(int)
)

customer_payment_average = (
    payments_analysis
    .groupby("Customer_ID")[
        "Payment_Amount"
    ]
    .transform("mean")
)

customer_payment_std = (
    payments_analysis
    .groupby("Customer_ID")[
        "Payment_Amount"
    ]
    .transform("std")
    .replace(0, np.nan)
)

payments_analysis[
    "Customer_Payment_Deviation"
] = (
    (
        payments_analysis["Payment_Amount"]
        - customer_payment_average
    )
    / customer_payment_std
).replace(
    [np.inf, -np.inf],
    0
).fillna(0).abs()

payments_analysis["Amount_Robust_Z"] = (
    robust_z_score(
        payments_analysis["Payment_Amount"]
    ).abs()
)

payments_analysis["Frequency_Robust_Z"] = (
    robust_z_score(
        payments_analysis[
            "Customer_Payment_Frequency"
        ]
    ).abs()
)


# ============================================================
# 13. PAYMENT ISOLATION FOREST
# ============================================================

payment_features = [
    "Payment_Amount",
    "Customer_Payment_Frequency",
    "Invoice_Payment_Frequency",
    "Customer_Payment_Deviation",
    "Payment_Day",
    "Weekend_Flag"
]

(
    payment_model_score,
    payment_prediction
) = run_isolation_forest(
    payments_analysis,
    payment_features
)

payments_analysis["Model_Anomaly_Score"] = (
    payment_model_score.values
)

payments_analysis["Model_Prediction"] = (
    payment_prediction
)

payment_factor_score = (
    percentile_score(
        payments_analysis["Amount_Robust_Z"]
    )
    + percentile_score(
        payments_analysis["Frequency_Robust_Z"]
    )
    + percentile_score(
        payments_analysis[
            "Customer_Payment_Deviation"
        ]
    )
    + percentile_score(
        payments_analysis[
            "Invoice_Payment_Frequency"
        ]
    )
) / 4

payments_analysis["Anomaly_Score"] = (
    payments_analysis["Model_Anomaly_Score"]
    * 0.60
    + payment_factor_score
    * 0.40
).clip(0, 100)

payments_analysis["Priority"] = (
    payments_analysis["Anomaly_Score"]
    .apply(assign_priority)
)


# ============================================================
# 14. PAYMENT ANOMALY REASONS
# ============================================================

payment_amount_limit = payments_analysis[
    "Amount_Robust_Z"
].quantile(0.95)

payment_frequency_limit = payments_analysis[
    "Customer_Payment_Frequency"
].quantile(0.95)


def payment_anomaly_reason(row):
    reasons = []

    if row["Amount_Robust_Z"] >= payment_amount_limit:
        reasons.append("Unusual payment amount")

    if (
        row["Customer_Payment_Frequency"]
        >= payment_frequency_limit
    ):
        reasons.append("High payment frequency")

    if row["Invoice_Payment_Frequency"] > 1:
        reasons.append(
            "Multiple payments for same invoice"
        )

    if row["Customer_Payment_Deviation"] >= 3:
        reasons.append(
            "Different from customer payment history"
        )

    if row["Payment_Amount"] <= 0:
        reasons.append(
            "Zero or negative payment"
        )

    if not reasons:
        reasons.append(
            "Multiple moderate-risk factors"
        )

    return "; ".join(reasons)


payments_analysis["Anomaly_Reason"] = (
    payments_analysis.apply(
        payment_anomaly_reason,
        axis=1
    )
)

payments_analysis["Dataset"] = "Payments"


# ============================================================
# 15. IDENTIFY INVENTORY COLUMNS
# ============================================================

inventory_product_col = find_column(
    inventory_df,
    ["Product_ID"]
)

inventory_warehouse_col = find_column(
    inventory_df,
    ["Warehouse_ID"]
)

inventory_date_col = find_column(
    inventory_df,
    ["Snapshot_Date", "Inventory_Date", "Date"]
)

opening_stock_col = find_column(
    inventory_df,
    ["Opening_Stock"],
    required=False
)

closing_stock_col = find_column(
    inventory_df,
    ["Closing_Stock"]
)

inventory_value_col = find_column(
    inventory_df,
    ["Stock_Value", "Inventory_Value"]
)


# ============================================================
# 16. PREPARE INVENTORY FEATURES
# ============================================================

inventory_analysis = pd.DataFrame(
    {
        "Product_ID": inventory_df[
            inventory_product_col
        ],
        "Warehouse_ID": inventory_df[
            inventory_warehouse_col
        ],
        "Transaction_Date": pd.to_datetime(
            inventory_df[inventory_date_col],
            errors="coerce"
        ),
        "Opening_Stock": numeric_series(
            inventory_df,
            opening_stock_col
        ),
        "Closing_Stock": numeric_series(
            inventory_df,
            closing_stock_col
        ),
        "Stock_Value": numeric_series(
            inventory_df,
            inventory_value_col
        )
    }
)

inventory_analysis = inventory_analysis.sort_values(
    [
        "Product_ID",
        "Warehouse_ID",
        "Transaction_Date"
    ]
).reset_index(drop=True)

inventory_analysis["Record_ID"] = (
    inventory_analysis["Product_ID"].astype(str)
    + "-"
    + inventory_analysis["Warehouse_ID"].astype(str)
    + "-"
    + inventory_analysis[
        "Transaction_Date"
    ].astype(str)
)

inventory_analysis["Stock_Movement"] = (
    inventory_analysis["Closing_Stock"]
    - inventory_analysis["Opening_Stock"]
)

inventory_analysis["Previous_Closing_Stock"] = (
    inventory_analysis
    .groupby(
        [
            "Product_ID",
            "Warehouse_ID"
        ]
    )["Closing_Stock"]
    .shift(1)
)

inventory_analysis[
    "Closing_Stock_Change"
] = (
    inventory_analysis["Closing_Stock"]
    - inventory_analysis[
        "Previous_Closing_Stock"
    ]
).fillna(0)

inventory_analysis["Stock_Value_Change"] = (
    inventory_analysis
    .groupby(
        [
            "Product_ID",
            "Warehouse_ID"
        ]
    )["Stock_Value"]
    .diff()
    .fillna(0)
)

inventory_analysis["Negative_Stock_Flag"] = np.where(
    inventory_analysis["Closing_Stock"] < 0,
    1,
    0
)

inventory_analysis["Stock_Movement_Robust_Z"] = (
    robust_z_score(
        inventory_analysis["Stock_Movement"]
    ).abs()
)

inventory_analysis["Stock_Change_Robust_Z"] = (
    robust_z_score(
        inventory_analysis["Closing_Stock_Change"]
    ).abs()
)

inventory_analysis["Value_Change_Robust_Z"] = (
    robust_z_score(
        inventory_analysis["Stock_Value_Change"]
    ).abs()
)

inventory_analysis["Stock_Value_Robust_Z"] = (
    robust_z_score(
        inventory_analysis["Stock_Value"]
    ).abs()
)


# ============================================================
# 17. INVENTORY ISOLATION FOREST
# ============================================================

inventory_features = [
    "Opening_Stock",
    "Closing_Stock",
    "Stock_Value",
    "Stock_Movement",
    "Closing_Stock_Change",
    "Stock_Value_Change",
    "Negative_Stock_Flag"
]

(
    inventory_model_score,
    inventory_prediction
) = run_isolation_forest(
    inventory_analysis,
    inventory_features
)

inventory_analysis["Model_Anomaly_Score"] = (
    inventory_model_score.values
)

inventory_analysis["Model_Prediction"] = (
    inventory_prediction
)

inventory_factor_score = (
    percentile_score(
        inventory_analysis[
            "Stock_Movement_Robust_Z"
        ]
    )
    + percentile_score(
        inventory_analysis[
            "Stock_Change_Robust_Z"
        ]
    )
    + percentile_score(
        inventory_analysis[
            "Value_Change_Robust_Z"
        ]
    )
    + percentile_score(
        inventory_analysis[
            "Stock_Value_Robust_Z"
        ]
    )
    + inventory_analysis[
        "Negative_Stock_Flag"
    ] * 100
) / 5

inventory_analysis["Anomaly_Score"] = (
    inventory_analysis["Model_Anomaly_Score"]
    * 0.60
    + inventory_factor_score
    * 0.40
).clip(0, 100)

inventory_analysis["Priority"] = (
    inventory_analysis["Anomaly_Score"]
    .apply(assign_priority)
)


# ============================================================
# 18. INVENTORY ANOMALY REASONS
# ============================================================

movement_limit = inventory_analysis[
    "Stock_Movement_Robust_Z"
].quantile(0.95)

stock_change_limit = inventory_analysis[
    "Stock_Change_Robust_Z"
].quantile(0.95)

value_change_limit = inventory_analysis[
    "Value_Change_Robust_Z"
].quantile(0.95)


def inventory_anomaly_reason(row):
    reasons = []

    if row["Closing_Stock"] < 0:
        reasons.append("Negative closing stock")

    if (
        row["Stock_Movement_Robust_Z"]
        >= movement_limit
    ):
        reasons.append(
            "Unusual inventory movement"
        )

    if (
        row["Stock_Change_Robust_Z"]
        >= stock_change_limit
    ):
        reasons.append(
            "Unusual closing-stock change"
        )

    if (
        row["Value_Change_Robust_Z"]
        >= value_change_limit
    ):
        reasons.append(
            "Unusual inventory-value change"
        )

    if row["Stock_Value"] < 0:
        reasons.append(
            "Negative inventory value"
        )

    if not reasons:
        reasons.append(
            "Multiple moderate-risk factors"
        )

    return "; ".join(reasons)


inventory_analysis["Anomaly_Reason"] = (
    inventory_analysis.apply(
        inventory_anomaly_reason,
        axis=1
    )
)

inventory_analysis["Dataset"] = "Inventory"


# ============================================================
# 19. SELECT TOP ANOMALIES
# ============================================================

top_sales_anomalies = (
    sales_analysis
    .sort_values(
        "Anomaly_Score",
        ascending=False
    )
    .head(TOP_RECORDS_PER_DATASET)
    .copy()
)

top_payment_anomalies = (
    payments_analysis
    .sort_values(
        "Anomaly_Score",
        ascending=False
    )
    .head(TOP_RECORDS_PER_DATASET)
    .copy()
)

top_inventory_anomalies = (
    inventory_analysis
    .sort_values(
        "Anomaly_Score",
        ascending=False
    )
    .head(TOP_RECORDS_PER_DATASET)
    .copy()
)


# ============================================================
# 20. CONSOLIDATED SUSPICIOUS RECORDS
# ============================================================

sales_consolidated = top_sales_anomalies[
    [
        "Dataset",
        "Record_ID",
        "Transaction_Date",
        "Customer_ID",
        "Product_ID",
        "Transaction_Amount",
        "Discount",
        "Refund",
        "Net_Profit",
        "Anomaly_Score",
        "Priority",
        "Anomaly_Reason"
    ]
].copy()

sales_consolidated[
    "Additional_Entity"
] = sales_consolidated["Customer_ID"]

payments_consolidated = top_payment_anomalies[
    [
        "Dataset",
        "Record_ID",
        "Transaction_Date",
        "Customer_ID",
        "Payment_Amount",
        "Anomaly_Score",
        "Priority",
        "Anomaly_Reason"
    ]
].copy()

payments_consolidated = payments_consolidated.rename(
    columns={
        "Payment_Amount": "Transaction_Amount"
    }
)

payments_consolidated[
    "Product_ID"
] = np.nan

payments_consolidated["Discount"] = 0
payments_consolidated["Refund"] = 0
payments_consolidated["Net_Profit"] = 0

payments_consolidated[
    "Additional_Entity"
] = payments_consolidated["Customer_ID"]

inventory_consolidated = top_inventory_anomalies[
    [
        "Dataset",
        "Record_ID",
        "Transaction_Date",
        "Product_ID",
        "Warehouse_ID",
        "Stock_Value",
        "Anomaly_Score",
        "Priority",
        "Anomaly_Reason"
    ]
].copy()

inventory_consolidated = inventory_consolidated.rename(
    columns={
        "Stock_Value": "Transaction_Amount",
        "Warehouse_ID": "Additional_Entity"
    }
)

inventory_consolidated[
    "Customer_ID"
] = np.nan

inventory_consolidated["Discount"] = 0
inventory_consolidated["Refund"] = 0
inventory_consolidated["Net_Profit"] = 0

common_columns = [
    "Dataset",
    "Record_ID",
    "Transaction_Date",
    "Customer_ID",
    "Product_ID",
    "Additional_Entity",
    "Transaction_Amount",
    "Discount",
    "Refund",
    "Net_Profit",
    "Anomaly_Score",
    "Priority",
    "Anomaly_Reason"
]

consolidated_anomalies = pd.concat(
    [
        sales_consolidated[common_columns],
        payments_consolidated[common_columns],
        inventory_consolidated[common_columns]
    ],
    ignore_index=True
)

consolidated_anomalies = (
    consolidated_anomalies
    .sort_values(
        "Anomaly_Score",
        ascending=False
    )
    .reset_index(drop=True)
)


# ============================================================
# 21. SUMMARY
# ============================================================

summary_rows = []

for dataset_name, analysis_df in [
    ("Sales", sales_analysis),
    ("Payments", payments_analysis),
    ("Inventory", inventory_analysis)
]:
    summary_rows.append(
        {
            "Dataset": dataset_name,
            "Total_Records": len(analysis_df),

            "Model_Flagged_Records": (
                analysis_df[
                    "Model_Prediction"
                ] == -1
            ).sum(),

            "Critical_Records": (
                analysis_df["Priority"]
                == "Critical"
            ).sum(),

            "High_Risk_Records": (
                analysis_df["Priority"]
                == "High"
            ).sum(),

            "Average_Anomaly_Score":
                analysis_df[
                    "Anomaly_Score"
                ].mean(),

            "Maximum_Anomaly_Score":
                analysis_df[
                    "Anomaly_Score"
                ].max()
        }
    )

anomaly_summary = pd.DataFrame(
    summary_rows
)


# ============================================================
# 22. RECOMMENDED ACTIONS
# ============================================================

def recommended_action(row):
    if row["Dataset"] == "Sales":
        return (
            "Validate order, discount, refund and customer "
            "purchase history before approval."
        )

    if row["Dataset"] == "Payments":
        return (
            "Match payment with invoice and review duplicate, "
            "overpayment or unusual customer payment behaviour."
        )

    return (
        "Reconcile warehouse movement with purchase, sale and "
        "return records; physically validate stock."
    )


consolidated_anomalies[
    "Recommended_Action"
] = consolidated_anomalies.apply(
    recommended_action,
    axis=1
)


# ============================================================
# 23. ROUND RESULTS
# ============================================================

for dataframe in [
    sales_analysis,
    payments_analysis,
    inventory_analysis,
    top_sales_anomalies,
    top_payment_anomalies,
    top_inventory_anomalies,
    consolidated_anomalies,
    anomaly_summary
]:
    numeric_columns = dataframe.select_dtypes(
        include=[np.number]
    ).columns

    dataframe[numeric_columns] = dataframe[
        numeric_columns
    ].round(2)


# ============================================================
# 24. SAVE CSV
# ============================================================

consolidated_anomalies.to_csv(
    CSV_OUTPUT,
    index=False
)


# ============================================================
# 25. SAVE EXCEL REPORT
# ============================================================

with pd.ExcelWriter(
    EXCEL_OUTPUT,
    engine="openpyxl"
) as writer:

    anomaly_summary.to_excel(
        writer,
        sheet_name="Executive_Summary",
        index=False
    )

    consolidated_anomalies.to_excel(
        writer,
        sheet_name="Top_Suspicious",
        index=False
    )

    top_sales_anomalies.to_excel(
        writer,
        sheet_name="Sales_Anomalies",
        index=False
    )

    top_payment_anomalies.to_excel(
        writer,
        sheet_name="Payment_Anomalies",
        index=False
    )

    top_inventory_anomalies.to_excel(
        writer,
        sheet_name="Inventory_Anomalies",
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
            ].width = min(max_length + 2, 60)


# ============================================================
# 26. CREATE CHARTS
# ============================================================

sns.set_theme(style="whitegrid")


# Chart 1: Flagged anomalies by dataset

plt.figure(figsize=(10, 6))

sns.barplot(
    data=anomaly_summary,
    x="Dataset",
    y="Model_Flagged_Records",
    palette="Reds_d"
)

plt.title(
    "Model-Flagged Anomalies by Dataset",
    fontsize=15,
    fontweight="bold"
)

plt.xlabel("Dataset")
plt.ylabel("Flagged Records")
plt.tight_layout()

plt.savefig(
    OUTPUT_FOLDER / "01_Anomalies_By_Dataset.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# Chart 2: Top suspicious records

top_chart_records = (
    consolidated_anomalies
    .head(20)
    .copy()
)

top_chart_records[
    "Chart_Label"
] = (
    top_chart_records["Dataset"]
    + " - "
    + top_chart_records[
        "Record_ID"
    ].astype(str)
)

plt.figure(figsize=(12, 9))

sns.barplot(
    data=top_chart_records,
    y="Chart_Label",
    x="Anomaly_Score",
    hue="Dataset",
    dodge=False
)

plt.title(
    "Top 20 Suspicious Records",
    fontsize=15,
    fontweight="bold"
)

plt.xlabel("Anomaly Score")
plt.ylabel("Record")
plt.xlim(0, 100)
plt.tight_layout()

plt.savefig(
    OUTPUT_FOLDER / "02_Top_Suspicious_Records.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# Chart 3: Sales amount vs anomaly score

sales_chart_sample = sales_analysis.sample(
    n=min(10000, len(sales_analysis)),
    random_state=RANDOM_STATE
)

plt.figure(figsize=(11, 7))

sns.scatterplot(
    data=sales_chart_sample,
    x="Transaction_Amount",
    y="Anomaly_Score",
    hue="Priority",
    alpha=0.65
)

plt.title(
    "Sales Amount vs Anomaly Score",
    fontsize=15,
    fontweight="bold"
)

plt.xlabel("Transaction Amount")
plt.ylabel("Anomaly Score")
plt.tight_layout()

plt.savefig(
    OUTPUT_FOLDER / "03_Sales_Anomaly_Scatter.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 27. PRINT FINAL RESULTS
# ============================================================

print("\n" + "=" * 78)
print("ANOMALY DETECTION SUMMARY")
print("=" * 78)

print(
    anomaly_summary.to_string(
        index=False
    )
)

print("\n" + "=" * 78)
print("TOP 20 SUSPICIOUS RECORDS")
print("=" * 78)

print(
    consolidated_anomalies[
        [
            "Dataset",
            "Record_ID",
            "Transaction_Date",
            "Customer_ID",
            "Product_ID",
            "Transaction_Amount",
            "Anomaly_Score",
            "Priority",
            "Anomaly_Reason"
        ]
    ].head(20).to_string(index=False)
)

print("\n" + "=" * 78)
print("ANOMALY DETECTION METHOD")
print("=" * 78)

print(
    """
Anomaly Score uses:
1. Transaction amount
2. Transaction frequency
3. Historical customer behaviour
4. Historical product behaviour
5. Discount and refund behaviour
6. Time pattern
7. Isolation Forest machine-learning score
8. Inventory movement and stock-value changes
"""
)

print("=" * 78)
print("ANOMALY DETECTION COMPLETED SUCCESSFULLY")
print("=" * 78)

print(f"\nExcel report saved in:\n{EXCEL_OUTPUT}")
print(f"\nCSV report saved in:\n{CSV_OUTPUT}")
print(f"\nCharts saved in:\n{OUTPUT_FOLDER}")