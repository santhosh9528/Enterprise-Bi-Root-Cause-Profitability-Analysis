import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
RAW_FOLDER = PROJECT / "Raw_Data"
CLEAN_FOLDER = PROJECT / "Cleaned_Data"
REJECT_FOLDER = PROJECT / "Data_Quality" / "Rejected_Records"

CLEAN_FOLDER.mkdir(exist_ok=True)
REJECT_FOLDER.mkdir(parents=True, exist_ok=True)

TODAY = pd.Timestamp.today().normalize()

# Processing order important:
# Parent/master tables first; transaction tables next.
processing_order = [
    "region_master.csv",
    "customer_master.csv",
    "employee_master.csv",
    "suppliers.csv",
    "product_master.csv",
    "orders.csv",
    "order_items.csv",
    "sales.csv",
    "returns.csv",
    "invoices.csv",
    "payments.csv",
    "purchases.csv",
    "inventory.csv",
    "marketing_campaigns.csv",
    "website_activity.csv",
    "customer_complaints.csv",
    "employee_attendance.csv",
    "monthly_targets.csv"
]

primary_keys = {
    "region_master.csv": "Region_ID",
    "customer_master.csv": "Customer_ID",
    "employee_master.csv": "Employee_ID",
    "suppliers.csv": "Supplier_ID",
    "product_master.csv": "Product_ID",
    "orders.csv": "Order_ID",
    "order_items.csv": "Order_Item_ID",
    "sales.csv": "Sale_ID",
    "returns.csv": "Return_ID",
    "invoices.csv": "Invoice_ID",
    "payments.csv": "Payment_ID",
    "purchases.csv": "Purchase_ID",
    "inventory.csv": "Inventory_ID",
    "marketing_campaigns.csv": "Campaign_ID",
    "website_activity.csv": "Event_ID",
    "customer_complaints.csv": "Complaint_ID",
    "employee_attendance.csv": "Attendance_ID",
    "monthly_targets.csv": "Target_ID"
}

foreign_keys = {
    "product_master.csv": {
        "Supplier_ID": "Supplier_ID"
    },
    "orders.csv": {
        "Customer_ID": "Customer_ID",
        "Region_ID": "Region_ID",
        "Sales_Employee_ID": "Employee_ID"
    },
    "order_items.csv": {
        "Order_ID": "Order_ID",
        "Product_ID": "Product_ID"
    },
    "sales.csv": {
        "Order_ID": "Order_ID",
        "Order_Item_ID": "Order_Item_ID",
        "Customer_ID": "Customer_ID",
        "Product_ID": "Product_ID",
        "Employee_ID": "Employee_ID",
        "Region_ID": "Region_ID"
    },
    "returns.csv": {
        "Order_ID": "Order_ID",
        "Order_Item_ID": "Order_Item_ID",
        "Customer_ID": "Customer_ID",
        "Product_ID": "Product_ID"
    },
    "invoices.csv": {
        "Order_ID": "Order_ID",
        "Customer_ID": "Customer_ID"
    },
    "payments.csv": {
        "Invoice_ID": "Invoice_ID",
        "Customer_ID": "Customer_ID"
    },
    "purchases.csv": {
        "Supplier_ID": "Supplier_ID",
        "Product_ID": "Product_ID",
        "Warehouse_ID": "Warehouse_ID"
    },
    "inventory.csv": {
        "Product_ID": "Product_ID",
        "Warehouse_ID": "Warehouse_ID"
    },
    "website_activity.csv": {
        "Customer_ID": "Customer_ID",
        "Order_ID": "Order_ID"
    },
    "customer_complaints.csv": {
        "Customer_ID": "Customer_ID",
        "Order_ID": "Order_ID"
    },
    "employee_attendance.csv": {
        "Employee_ID": "Employee_ID"
    },
    "monthly_targets.csv": {
        "Region_ID": "Region_ID"
    }
}

# Indha columns negative-ah irukka koodadhu
non_negative_columns = {
    "Quantity",
    "Return_Quantity",
    "Unit_Price",
    "List_Price",
    "Standard_Cost",
    "Gross_Amount",
    "Net_Amount",
    "Gross_Sales",
    "Net_Sales",
    "Product_Cost",
    "Shipping_Cost",
    "Payment_Fee",
    "Payment_Amount",
    "Invoice_Amount",
    "Tax_Amount",
    "Opening_Stock",
    "Purchases",
    "Units_Sold",
    "Unit_Cost",
    "Spend",
    "Worked_Hours",
    "Monthly_Salary",
    "Credit_Limit"
}

# Future date allow panna koodatha actual event dates
actual_event_dates = {
    "Join_Date",
    "Launch_Date",
    "Hire_Date",
    "Contract_Start",
    "Order_Date",
    "Sale_Date",
    "Return_Date",
    "Invoice_Date",
    "Payment_Date",
    "Purchase_Date",
    "Delivery_Date",
    "Snapshot_Date",
    "Campaign_Date",
    "Event_Time",
    "Complaint_Date",
    "Resolution_Date",
    "Attendance_Date"
}

# Cleaned parent keys inga store aagum
valid_keys = {}

cleaning_summary = []

for file_name in processing_order:

    print(f"Cleaning: {file_name}")

    file_path = RAW_FOLDER / file_name

    df = pd.read_csv(
        file_path,
        low_memory=False
    )

    original_records = len(df)

    # Source row number retain pannuvom
    df.insert(0, "Source_Row", df.index + 2)

    # Text columns trim
    text_columns = df.select_dtypes(
        include=["object", "string"]
    ).columns

    for column in text_columns:
        df[column] = df[column].apply(
            lambda value:
            value.strip()
            if isinstance(value, str)
            else value
        )

        df[column] = df[column].replace(
            ["", "NULL", "null", "None", "N/A"],
            pd.NA
        )

    reject_reasons = pd.Series(
        "",
        index=df.index,
        dtype="string"
    )

    def add_reason(mask, reason):
        global reject_reasons

        reject_reasons.loc[mask] = (
            reject_reasons.loc[mask]
            .fillna("")
            .apply(
                lambda current:
                f"{current}; {reason}".strip("; ")
            )
        )

    primary_key = primary_keys[file_name]

    # Missing primary keys
    missing_pk = df[primary_key].isna()
    add_reason(missing_pk, "Missing Primary Key")

    # Duplicate primary keys
    duplicate_pk = (
        df[primary_key].notna() &
        df.duplicated(
            subset=[primary_key],
            keep="first"
        )
    )
    add_reason(duplicate_pk, "Duplicate Primary Key")

    # Exact duplicate rows
    columns_without_source = [
        column for column in df.columns
        if column != "Source_Row"
    ]

    exact_duplicates = df.duplicated(
        subset=columns_without_source,
        keep="first"
    )
    add_reason(exact_duplicates, "Exact Duplicate Record")

    # Date cleaning and validation
    date_columns = [
        column for column in df.columns
        if "Date" in column or
        column == "Month" or
        column == "Event_Time"
    ]

    for column in date_columns:

        original_date = df[column].copy()

        converted_date = pd.to_datetime(
            df[column],
            errors="coerce"
        )

        invalid_date = (
            original_date.notna() &
            converted_date.isna()
        )
        add_reason(
            invalid_date,
            f"Invalid Date: {column}"
        )

        if column in actual_event_dates:

            future_date = (
                converted_date.notna() &
                (converted_date > TODAY)
            )

            add_reason(
                future_date,
                f"Future Date: {column}"
            )

        df[column] = converted_date

    # Negative value validation
    for column in df.columns:

        if column in non_negative_columns:

            numeric_value = pd.to_numeric(
                df[column],
                errors="coerce"
            )

            negative_value = numeric_value < 0

            add_reason(
                negative_value,
                f"Negative Value: {column}"
            )

            df[column] = numeric_value

    # Foreign-key validation
    for child_column, parent_key in foreign_keys.get(
        file_name, {}
    ).items():

        if child_column not in df.columns:
            continue

        parent_values = valid_keys.get(
            parent_key,
            set()
        )

        child_values = df[child_column].astype("string")

        # Missing optional FK separate issue illa;
        # missing-value audit-la already capture pannirukkom.
        unmatched_fk = (
            child_values.notna() &
            ~child_values.isin(parent_values)
        )

        add_reason(
            unmatched_fk,
            f"Invalid Foreign Key: {child_column}"
        )

    rejected_mask = reject_reasons.str.len() > 0

    rejected_df = df[rejected_mask].copy()
    cleaned_df = df[~rejected_mask].copy()

    rejected_df.insert(
        1,
        "Reject_Reasons",
        reject_reasons[rejected_mask]
    )

    # Source_Row cleaned data-la thevai illa
    cleaned_df = cleaned_df.drop(
        columns=["Source_Row"]
    )

    # Rejected rows export
    if not rejected_df.empty:

        rejected_file = (
            REJECT_FOLDER /
            file_name.replace(
                ".csv",
                "_Rejected.csv"
            )
        )

        rejected_df.to_csv(
            rejected_file,
            index=False
        )

    # Cleaned file export
    cleaned_df.to_csv(
        CLEAN_FOLDER / file_name,
        index=False
    )

    # Cleaned primary keys store
    valid_keys[primary_key] = set(
        cleaned_df[primary_key]
        .dropna()
        .astype(str)
    )

    # Region table-la Warehouse_ID additional key
    if (
        file_name == "region_master.csv" and
        "Warehouse_ID" in cleaned_df.columns
    ):
        valid_keys["Warehouse_ID"] = set(
            cleaned_df["Warehouse_ID"]
            .dropna()
            .astype(str)
        )

    cleaning_summary.append({
        "Dataset": file_name,
        "Original_Records": original_records,
        "Cleaned_Records": len(cleaned_df),
        "Rejected_Records": len(rejected_df),
        "Retention_Percentage": round(
            len(cleaned_df) /
            original_records * 100,
            2
        )
    })

summary_df = pd.DataFrame(cleaning_summary)

summary_df.to_csv(
    PROJECT /
    "Data_Quality" /
    "Cleaning_Summary.csv",
    index=False
)

print("\nAll datasets cleaned successfully!")
print(summary_df)
print("\nClean files saved in Cleaned_Data")
print("Rejected records saved in Data_Quality/Rejected_Records")