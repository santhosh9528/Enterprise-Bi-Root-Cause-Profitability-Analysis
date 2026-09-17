import pandas as pd
from pathlib import Path
from datetime import datetime

PROJECT_FOLDER = Path(__file__).resolve().parents[1]
RAW_FOLDER = PROJECT_FOLDER / "Raw_Data"
OUTPUT_FOLDER = PROJECT_FOLDER / "Data_Quality"

OUTPUT_FOLDER.mkdir(exist_ok=True)

TODAY = pd.Timestamp(datetime.today().date())

date_issues = []
negative_issues = []
foreign_key_issues = []
summary = []

# Negative value check panna vendiya columns
negative_columns = {
    "Quantity",
    "Return_Quantity",
    "Unit_Price",
    "List_Price",
    "Standard_Cost",
    "Gross_Amount",
    "Net_Amount",
    "Gross_Sales",
    "Net_Sales",
    "Discount",
    "Product_Cost",
    "Shipping_Cost",
    "Payment_Fee",
    "Payment_Amount",
    "Invoice_Amount",
    "Tax_Amount",
    "Opening_Stock",
    "Purchases",
    "Units_Sold",
    "Closing_Stock",
    "Unit_Cost",
    "Stock_Value",
    "Spend",
    "Worked_Hours",
    "Monthly_Salary",
    "Credit_Limit"
}

# Parent table key values load pannudhu
parent_keys = {
    "Customer_ID": set(
        pd.read_csv(
            RAW_FOLDER / "customer_master.csv",
            usecols=["Customer_ID"]
        )["Customer_ID"].dropna().astype(str)
    ),

    "Product_ID": set(
        pd.read_csv(
            RAW_FOLDER / "product_master.csv",
            usecols=["Product_ID"]
        )["Product_ID"].dropna().astype(str)
    ),

    "Employee_ID": set(
        pd.read_csv(
            RAW_FOLDER / "employee_master.csv",
            usecols=["Employee_ID"]
        )["Employee_ID"].dropna().astype(str)
    ),

    "Region_ID": set(
        pd.read_csv(
            RAW_FOLDER / "region_master.csv",
            usecols=["Region_ID"]
        )["Region_ID"].dropna().astype(str)
    ),

    "Warehouse_ID": set(
        pd.read_csv(
            RAW_FOLDER / "region_master.csv",
            usecols=["Warehouse_ID"]
        )["Warehouse_ID"].dropna().astype(str)
    ),

    "Supplier_ID": set(
        pd.read_csv(
            RAW_FOLDER / "suppliers.csv",
            usecols=["Supplier_ID"]
        )["Supplier_ID"].dropna().astype(str)
    ),

    "Order_ID": set(
        pd.read_csv(
            RAW_FOLDER / "orders.csv",
            usecols=["Order_ID"]
        )["Order_ID"].dropna().astype(str)
    ),

    "Order_Item_ID": set(
        pd.read_csv(
            RAW_FOLDER / "order_items.csv",
            usecols=["Order_Item_ID"]
        )["Order_Item_ID"].dropna().astype(str)
    ),

    "Invoice_ID": set(
        pd.read_csv(
            RAW_FOLDER / "invoices.csv",
            usecols=["Invoice_ID"]
        )["Invoice_ID"].dropna().astype(str)
    )
}

# Dataset foreign-key mapping
foreign_keys = {
    "orders.csv": [
        "Customer_ID", "Region_ID", "Sales_Employee_ID"
    ],

    "order_items.csv": [
        "Order_ID", "Product_ID"
    ],

    "sales.csv": [
        "Order_ID", "Order_Item_ID", "Customer_ID",
        "Product_ID", "Employee_ID", "Region_ID"
    ],

    "returns.csv": [
        "Order_ID", "Order_Item_ID",
        "Customer_ID", "Product_ID"
    ],

    "invoices.csv": [
        "Order_ID", "Customer_ID"
    ],

    "payments.csv": [
        "Invoice_ID", "Customer_ID"
    ],

    "product_master.csv": [
        "Supplier_ID"
    ],

    "purchases.csv": [
        "Supplier_ID", "Product_ID", "Warehouse_ID"
    ],

    "inventory.csv": [
        "Product_ID", "Warehouse_ID"
    ],

    "website_activity.csv": [
        "Customer_ID", "Order_ID"
    ],

    "customer_complaints.csv": [
        "Customer_ID", "Order_ID"
    ],

    "employee_attendance.csv": [
        "Employee_ID"
    ],

    "monthly_targets.csv": [
        "Region_ID"
    ]
}

# Different column name → parent key name
parent_key_mapping = {
    "Sales_Employee_ID": "Employee_ID"
}

for file_path in RAW_FOLDER.glob("*.csv"):

    file_name = file_path.name
    print(f"Advanced checking: {file_name}")

    df = pd.read_csv(file_path, low_memory=False)

    file_date_issues = 0
    file_negative_issues = 0
    file_fk_issues = 0

    # Date validation
    date_columns = [
        column for column in df.columns
        if "Date" in column or "Month" == column
    ]

    for column in date_columns:

        original_values = df[column]

        converted_dates = pd.to_datetime(
            original_values,
            errors="coerce"
        )

        invalid_mask = (
            original_values.notna() &
            converted_dates.isna()
        )

        future_mask = (
            converted_dates.notna() &
            (converted_dates > TODAY)
        )

        for index in df.index[invalid_mask]:
            date_issues.append({
                "Dataset": file_name,
                "Source_Row": index + 2,
                "Column": column,
                "Value": original_values.loc[index],
                "Issue": "Invalid Date"
            })
            file_date_issues += 1

        for index in df.index[future_mask]:
            date_issues.append({
                "Dataset": file_name,
                "Source_Row": index + 2,
                "Column": column,
                "Value": original_values.loc[index],
                "Issue": "Future Date"
            })
            file_date_issues += 1

    # Negative-value validation
    for column in df.columns:

        if column in negative_columns:

            numeric_values = pd.to_numeric(
                df[column],
                errors="coerce"
            )

            negative_mask = numeric_values < 0

            for index in df.index[negative_mask]:

                negative_issues.append({
                    "Dataset": file_name,
                    "Source_Row": index + 2,
                    "Column": column,
                    "Value": df.loc[index, column],
                    "Issue": "Negative Value"
                })

                file_negative_issues += 1

    # Foreign-key validation
    for column in foreign_keys.get(file_name, []):

        if column not in df.columns:
            continue

        parent_column = parent_key_mapping.get(
            column,
            column
        )

        valid_parent_values = parent_keys[parent_column]

        child_values = df[column].astype("string")

        unmatched_mask = (
            child_values.notna() &
            ~child_values.isin(valid_parent_values)
        )

        for index in df.index[unmatched_mask]:

            foreign_key_issues.append({
                "Dataset": file_name,
                "Source_Row": index + 2,
                "Column": column,
                "Invalid_Value": child_values.loc[index],
                "Expected_Parent_Key": parent_column,
                "Issue": "Unmatched Foreign Key"
            })

            file_fk_issues += 1

    summary.append({
        "Dataset": file_name,
        "Total_Records": len(df),
        "Date_Issues": file_date_issues,
        "Negative_Value_Issues": file_negative_issues,
        "Foreign_Key_Issues": file_fk_issues,
        "Total_Advanced_Issues":
            file_date_issues +
            file_negative_issues +
            file_fk_issues
    })

# Reports export
pd.DataFrame(summary).to_csv(
    OUTPUT_FOLDER / "Advanced_Data_Quality_Summary.csv",
    index=False
)

pd.DataFrame(date_issues).to_csv(
    OUTPUT_FOLDER / "Invalid_Date_Report.csv",
    index=False
)

pd.DataFrame(negative_issues).to_csv(
    OUTPUT_FOLDER / "Negative_Value_Report.csv",
    index=False
)

pd.DataFrame(foreign_key_issues).to_csv(
    OUTPUT_FOLDER / "Unmatched_Foreign_Keys.csv",
    index=False
)

print("\nAdvanced Data Quality Audit completed!")
print(f"Reports saved in: {OUTPUT_FOLDER}")