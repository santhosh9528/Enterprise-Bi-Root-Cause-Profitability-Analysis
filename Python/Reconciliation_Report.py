from pathlib import Path
import pandas as pd

# ============================================================
# PATH CONFIGURATION
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

OUTPUT_FOLDER = PROJECT_ROOT / "Reconciliation_Report"
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

EXCEL_FILE = OUTPUT_FOLDER / "Revenue_Reconciliation_Report.xlsx"
CSV_FILE = OUTPUT_FOLDER / "Revenue_Reconciliation_Summary.csv"

# ============================================================
# VERIFIED RECONCILIATION VALUES
# ============================================================

management_revenue = 520_000_000.80
database_gross_sales = 499_235_746.94
returns_amount = 14_976_750.82
database_revenue_after_returns = 484_259_046.67
refunds_amount = 3_249_066.95

adjusted_database_revenue = (
    database_revenue_after_returns - refunds_amount
)

reconciliation_difference = (
    management_revenue - adjusted_database_revenue
)

unmatched_transaction_count = 798
unmatched_transaction_amount = 3_511_040.84

# ============================================================
# SUMMARY TABLE
# ============================================================

summary_df = pd.DataFrame(
    [
        {
            "Reconciliation_Component": "Management Revenue",
            "Amount_INR": management_revenue,
            "Amount_Crore": management_revenue / 10_000_000,
            "Explanation": (
                "Revenue reported by management."
            ),
        },
        {
            "Reconciliation_Component": "Database Gross Sales",
            "Amount_INR": database_gross_sales,
            "Amount_Crore": database_gross_sales / 10_000_000,
            "Explanation": (
                "Gross sales value recorded in the sales database."
            ),
        },
        {
            "Reconciliation_Component": "Returns",
            "Amount_INR": returns_amount,
            "Amount_Crore": returns_amount / 10_000_000,
            "Explanation": (
                "Returned sales deducted from database gross sales."
            ),
        },
        {
            "Reconciliation_Component": (
                "Database Revenue After Returns"
            ),
            "Amount_INR": database_revenue_after_returns,
            "Amount_Crore": (
                database_revenue_after_returns / 10_000_000
            ),
            "Explanation": (
                "Database sales revenue after return adjustments."
            ),
        },
        {
            "Reconciliation_Component": "Refunds",
            "Amount_INR": refunds_amount,
            "Amount_Crore": refunds_amount / 10_000_000,
            "Explanation": (
                "Customer refunds deducted from revenue."
            ),
        },
        {
            "Reconciliation_Component": (
                "Adjusted Database Revenue"
            ),
            "Amount_INR": adjusted_database_revenue,
            "Amount_Crore": (
                adjusted_database_revenue / 10_000_000
            ),
            "Explanation": (
                "Database revenue after returns and refunds."
            ),
        },
        {
            "Reconciliation_Component": (
                "Unmatched Transaction Amount"
            ),
            "Amount_INR": unmatched_transaction_amount,
            "Amount_Crore": (
                unmatched_transaction_amount / 10_000_000
            ),
            "Explanation": (
                f"Value associated with "
                f"{unmatched_transaction_count} unmatched transactions."
            ),
        },
        {
            "Reconciliation_Component": (
                "Final Reconciliation Difference"
            ),
            "Amount_INR": reconciliation_difference,
            "Amount_Crore": (
                reconciliation_difference / 10_000_000
            ),
            "Explanation": (
                "Difference between management revenue and "
                "adjusted database revenue."
            ),
        },
    ]
)

# ============================================================
# RECONCILIATION BRIDGE
# ============================================================

bridge_df = pd.DataFrame(
    [
        {
            "Step": 1,
            "Description": "Management Revenue",
            "Adjustment_INR": management_revenue,
            "Running_Balance_INR": management_revenue,
        },
        {
            "Step": 2,
            "Description": "Less: Database Gross Sales",
            "Adjustment_INR": -database_gross_sales,
            "Running_Balance_INR": (
                management_revenue - database_gross_sales
            ),
        },
        {
            "Step": 3,
            "Description": "Add: Returns Adjustment",
            "Adjustment_INR": returns_amount,
            "Running_Balance_INR": (
                management_revenue
                - database_gross_sales
                + returns_amount
            ),
        },
        {
            "Step": 4,
            "Description": "Add: Refund Adjustment",
            "Adjustment_INR": refunds_amount,
            "Running_Balance_INR": reconciliation_difference,
        },
    ]
)

# ============================================================
# ROOT-CAUSE TABLE
# ============================================================

root_cause_df = pd.DataFrame(
    [
        {
            "Issue_ID": "REC-001",
            "Issue": "Different Revenue Definitions",
            "Root_Cause": (
                "Management and database reports do not use "
                "the same revenue definition."
            ),
            "Business_Impact": (
                "Reported company revenue is overstated compared "
                "with adjusted database revenue."
            ),
            "Priority": "Critical",
            "Recommended_Action": (
                "Create one approved revenue definition covering "
                "sales, returns, refunds, invoices and payments."
            ),
        },
        {
            "Issue_ID": "REC-002",
            "Issue": "Returns Not Consistently Adjusted",
            "Root_Cause": (
                "Gross sales and management revenue do not apply "
                "return adjustments consistently."
            ),
            "Business_Impact": (
                "Revenue and profitability can be overstated."
            ),
            "Priority": "Critical",
            "Recommended_Action": (
                "Deduct validated returns in the reporting period "
                "in which the return was approved."
            ),
        },
        {
            "Issue_ID": "REC-003",
            "Issue": "Refund Treatment Difference",
            "Root_Cause": (
                "Refunds are not treated consistently between "
                "management and database reports."
            ),
            "Business_Impact": (
                "The final revenue difference increases by the "
                "refund amount."
            ),
            "Priority": "Critical",
            "Recommended_Action": (
                "Link every refund to a return, payment and invoice "
                "before month-end reporting."
            ),
        },
        {
            "Issue_ID": "REC-004",
            "Issue": "Unmatched Transactions",
            "Root_Cause": (
                f"{unmatched_transaction_count} transactions do not "
                "fully match across the order-to-cash tables."
            ),
            "Business_Impact": (
                "Unmatched transaction value is INR "
                f"{unmatched_transaction_amount:,.2f}."
            ),
            "Priority": "High",
            "Recommended_Action": (
                "Create an automated exception report for orders, "
                "sales, invoices and payments that do not match."
            ),
        },
        {
            "Issue_ID": "REC-005",
            "Issue": "Lack of Automated Reconciliation",
            "Root_Cause": (
                "Reports are prepared independently by different "
                "departments."
            ),
            "Business_Impact": (
                "Management receives inconsistent revenue values."
            ),
            "Priority": "Critical",
            "Recommended_Action": (
                "Run an automated order-to-cash reconciliation "
                "before publishing the monthly management report."
            ),
        },
    ]
)

# ============================================================
# MANAGEMENT CONCLUSION
# ============================================================

conclusion_df = pd.DataFrame(
    [
        {
            "Metric": "Management Revenue",
            "Result": f"INR {management_revenue:,.2f}",
        },
        {
            "Metric": "Adjusted Database Revenue",
            "Result": f"INR {adjusted_database_revenue:,.2f}",
        },
        {
            "Metric": "Final Reconciliation Difference",
            "Result": f"INR {reconciliation_difference:,.2f}",
        },
        {
            "Metric": "Difference in Crore",
            "Result": (
                f"INR {reconciliation_difference / 10_000_000:,.2f} Cr"
            ),
        },
        {
            "Metric": "Unmatched Transactions",
            "Result": f"{unmatched_transaction_count:,}",
        },
        {
            "Metric": "Management Conclusion",
            "Result": (
                "Revenue reports do not reconcile because management "
                "and database reports use different revenue definitions "
                "and apply returns, refunds and unmatched transactions "
                "differently."
            ),
        },
    ]
)

# ============================================================
# SAVE CSV
# ============================================================

summary_df.to_csv(
    CSV_FILE,
    index=False,
)

# ============================================================
# SAVE EXCEL REPORT
# ============================================================

with pd.ExcelWriter(
    EXCEL_FILE,
    engine="openpyxl",
) as writer:

    summary_df.to_excel(
        writer,
        sheet_name="Reconciliation Summary",
        index=False,
    )

    bridge_df.to_excel(
        writer,
        sheet_name="Reconciliation Bridge",
        index=False,
    )

    root_cause_df.to_excel(
        writer,
        sheet_name="Root Cause",
        index=False,
    )

    conclusion_df.to_excel(
        writer,
        sheet_name="Management Conclusion",
        index=False,
    )

    workbook = writer.book

    # Apply formatting to every worksheet.
    for worksheet in workbook.worksheets:

        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions

        # Header formatting.
        for cell in worksheet[1]:
            cell.font = cell.font.copy(
                bold=True,
                color="FFFFFF",
            )

            cell.fill = cell.fill.copy(
                fill_type="solid",
                fgColor="17365D",
            )

            cell.alignment = cell.alignment.copy(
                horizontal="center",
                vertical="center",
                wrap_text=True,
            )

        # Cell alignment.
        for row in worksheet.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = cell.alignment.copy(
                    vertical="top",
                    wrap_text=True,
                )

        # Set column widths automatically.
        for column_cells in worksheet.columns:
            column_letter = column_cells[0].column_letter

            maximum_length = 0

            for cell in column_cells:
                if cell.value is not None:
                    maximum_length = max(
                        maximum_length,
                        len(str(cell.value)),
                    )

            worksheet.column_dimensions[column_letter].width = min(
                maximum_length + 3,
                55,
            )

    # Number formatting for summary.
    summary_sheet = workbook["Reconciliation Summary"]

    for cell in summary_sheet["B"][1:]:
        cell.number_format = '#,##0.00'

    for cell in summary_sheet["C"][1:]:
        cell.number_format = '0.00'

    # Number formatting for bridge.
    bridge_sheet = workbook["Reconciliation Bridge"]

    for cell in bridge_sheet["C"][1:]:
        cell.number_format = '#,##0.00;[Red]-#,##0.00'

    for cell in bridge_sheet["D"][1:]:
        cell.number_format = '#,##0.00;[Red]-#,##0.00'

    # Highlight final difference.
    final_row = summary_sheet.max_row

    for cell in summary_sheet[final_row]:
        cell.font = cell.font.copy(
            bold=True,
            color="FFFFFF",
        )

        cell.fill = cell.fill.copy(
            fill_type="solid",
            fgColor="D64545",
        )

# ============================================================
# FINAL OUTPUT
# ============================================================

print("=" * 78)
print("REVENUE RECONCILIATION REPORT CREATED SUCCESSFULLY")
print("=" * 78)
print()
print("Excel report saved in:")
print(EXCEL_FILE)
print()
print("CSV summary saved in:")
print(CSV_FILE)
print()
print("Final reconciliation difference:")
print(f"INR {reconciliation_difference:,.2f}")
print(
    f"INR {reconciliation_difference / 10_000_000:,.2f} Crore"
)