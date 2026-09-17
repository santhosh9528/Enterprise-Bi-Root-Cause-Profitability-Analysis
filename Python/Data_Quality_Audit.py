import pandas as pd
from pathlib import Path

# Project folders
PROJECT_FOLDER = Path(__file__).resolve().parents[1]
RAW_FOLDER = PROJECT_FOLDER / "Raw_Data"
OUTPUT_FOLDER = PROJECT_FOLDER / "Data_Quality"

OUTPUT_FOLDER.mkdir(exist_ok=True)

# Dataset → Primary Key mapping
primary_keys = {
    "customer_master.csv": "Customer_ID",
    "product_master.csv": "Product_ID",
    "employee_master.csv": "Employee_ID",
    "region_master.csv": "Region_ID",
    "orders.csv": "Order_ID",
    "order_items.csv": "Order_Item_ID",
    "sales.csv": "Sale_ID",
    "returns.csv": "Return_ID",
    "payments.csv": "Payment_ID",
    "invoices.csv": "Invoice_ID",
    "purchases.csv": "Purchase_ID",
    "inventory.csv": "Inventory_ID",
    "suppliers.csv": "Supplier_ID",
    "marketing_campaigns.csv": "Campaign_ID",
    "website_activity.csv": "Event_ID",
    "customer_complaints.csv": "Complaint_ID",
    "employee_attendance.csv": "Attendance_ID",
    "monthly_targets.csv": "Target_ID"
}

summary_results = []
missing_results = []
duplicate_results = []

for file_path in RAW_FOLDER.glob("*.csv"):

    file_name = file_path.name
    print(f"Checking: {file_name}")

    df = pd.read_csv(file_path, low_memory=False)

    total_records = len(df)

    # Missing values
    missing_cells = int(df.isnull().sum().sum())

    for column in df.columns:
        missing_count = int(df[column].isnull().sum())

        if missing_count > 0:
            missing_results.append({
                "Dataset": file_name,
                "Column": column,
                "Missing_Count": missing_count,
                "Missing_Percentage":
                    round((missing_count / total_records) * 100, 2)
            })

    # Primary-key checks
    primary_key = primary_keys.get(file_name)

    missing_primary_keys = 0
    duplicate_records = 0

    if primary_key and primary_key in df.columns:

        missing_primary_keys = int(
            df[primary_key].isnull().sum()
        )

        duplicate_records = int(
            df.duplicated(subset=[primary_key], keep=False).sum()
        )

        duplicate_rows = df[
            df.duplicated(subset=[primary_key], keep=False)
        ].copy()

        if not duplicate_rows.empty:
            duplicate_rows.insert(0, "Dataset", file_name)
            duplicate_results.append(duplicate_rows)

    # Entire-row duplicates
    exact_duplicate_records = int(
        df.duplicated(keep=False).sum()
    )

    invalid_records = (
        missing_primary_keys +
        duplicate_records +
        exact_duplicate_records
    )

    valid_records = max(total_records - invalid_records, 0)

    quality_percentage = round(
        (valid_records / total_records) * 100, 2
    ) if total_records > 0 else 0

    summary_results.append({
        "Dataset": file_name,
        "Total_Records": total_records,
        "Valid_Records": valid_records,
        "Invalid_Records": invalid_records,
        "Duplicate_Records": duplicate_records,
        "Exact_Duplicate_Records": exact_duplicate_records,
        "Missing_Primary_Keys": missing_primary_keys,
        "Missing_Cells": missing_cells,
        "Quality_Percentage": quality_percentage
    })

# Create summary report
summary_df = pd.DataFrame(summary_results)

summary_df.to_csv(
    OUTPUT_FOLDER / "Data_Quality_Summary.csv",
    index=False
)

# Create missing-value report
missing_df = pd.DataFrame(missing_results)

missing_df.to_csv(
    OUTPUT_FOLDER / "Missing_Value_Report.csv",
    index=False
)

# Create duplicate report
if duplicate_results:

    duplicates_df = pd.concat(
        duplicate_results,
        ignore_index=True
    )

    duplicates_df.to_csv(
        OUTPUT_FOLDER / "Duplicate_Records.csv",
        index=False
    )

print("\nData Quality Audit completed successfully!")
print(f"Reports saved in: {OUTPUT_FOLDER}")