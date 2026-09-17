import pandas as pd
from pathlib import Path
from datetime import datetime

PROJECT = Path(__file__).resolve().parents[1]
RAW = PROJECT / "Raw_Data"
OUTPUT = PROJECT / "Data_Quality"

TODAY = pd.Timestamp(datetime.today().date())

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

negative_columns = {
    "Quantity", "Return_Quantity", "Unit_Price",
    "List_Price", "Standard_Cost", "Gross_Amount",
    "Net_Amount", "Gross_Sales", "Net_Sales",
    "Product_Cost", "Shipping_Cost", "Payment_Fee",
    "Payment_Amount", "Invoice_Amount",
    "Opening_Stock", "Purchases", "Units_Sold",
    "Closing_Stock", "Unit_Cost", "Stock_Value",
    "Spend", "Worked_Hours", "Monthly_Salary"
}

results = []

for file_path in RAW.glob("*.csv"):

    file_name = file_path.name
    print(f"Calculating score: {file_name}")

    df = pd.read_csv(file_path, low_memory=False)

    # Oru row-la multiple issues irundhaalum
    # unique-ah identify panna Boolean mask
    invalid_mask = pd.Series(False, index=df.index)

    # Missing values
    missing_mask = df.isnull().any(axis=1)
    invalid_mask = invalid_mask | missing_mask

    # Exact duplicate records
    exact_duplicate_mask = df.duplicated(keep=False)
    invalid_mask = invalid_mask | exact_duplicate_mask

    # Primary-key problems
    primary_key = primary_keys[file_name]

    missing_pk_mask = df[primary_key].isnull()

    duplicate_pk_mask = df.duplicated(
        subset=[primary_key],
        keep=False
    )

    invalid_mask = (
        invalid_mask |
        missing_pk_mask |
        duplicate_pk_mask
    )

    # Invalid and future dates
    date_issue_mask = pd.Series(False, index=df.index)

    date_columns = [
        column for column in df.columns
        if "Date" in column or column == "Month"
    ]

    for column in date_columns:

        converted = pd.to_datetime(
            df[column],
            errors="coerce"
        )

        invalid_date = (
            df[column].notna() &
            converted.isna()
        )

        future_date = (
            converted.notna() &
            (converted > TODAY)
        )

        date_issue_mask = (
            date_issue_mask |
            invalid_date |
            future_date
        )

    invalid_mask = invalid_mask | date_issue_mask

    # Negative values
    negative_mask = pd.Series(False, index=df.index)

    for column in df.columns:

        if column in negative_columns:

            numeric_data = pd.to_numeric(
                df[column],
                errors="coerce"
            )

            negative_mask = (
                negative_mask |
                (numeric_data < 0)
            )

    invalid_mask = invalid_mask | negative_mask

    total_records = len(df)
    invalid_records = int(invalid_mask.sum())
    valid_records = total_records - invalid_records

    quality_percentage = round(
        (valid_records / total_records) * 100,
        2
    ) if total_records > 0 else 0

    results.append({
        "Dataset": file_name,
        "Total_Records": total_records,
        "Valid_Records": valid_records,
        "Invalid_Records": invalid_records,
        "Rows_With_Missing_Values": int(missing_mask.sum()),
        "Duplicate_Primary_Key_Rows":
            int(duplicate_pk_mask.sum()),
        "Exact_Duplicate_Rows":
            int(exact_duplicate_mask.sum()),
        "Invalid_or_Future_Date_Rows":
            int(date_issue_mask.sum()),
        "Negative_Value_Rows":
            int(negative_mask.sum()),
        "Data_Quality_Percentage":
            quality_percentage
    })

quality_df = pd.DataFrame(results)

quality_df = quality_df.sort_values(
    "Data_Quality_Percentage",
    ascending=True
)

quality_df.to_csv(
    OUTPUT / "Final_Data_Quality_Score.csv",
    index=False
)

print("\nFinal Data Quality Score completed!")
print(quality_df)
print("\nSaved as Final_Data_Quality_Score.csv")