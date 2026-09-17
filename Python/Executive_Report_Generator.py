from pathlib import Path
from datetime import datetime

import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
    Image,
)

# ============================================================
# PATH CONFIGURATION
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

OUTPUT_PDF = PROJECT_ROOT / "Executive_Report.pdf"
CHART_FOLDER = PROJECT_ROOT / "_Executive_Report_Charts"
CHART_FOLDER.mkdir(exist_ok=True)

# ============================================================
# COLOURS
# ============================================================

DARK_BLUE = colors.HexColor("#17365D")
BLUE = colors.HexColor("#2774AE")
RED = colors.HexColor("#D64545")
GREEN = colors.HexColor("#1B8A5A")
ORANGE = colors.HexColor("#E67E22")
LIGHT_GREY = colors.HexColor("#F3F5F7")
LIGHT_GREEN = colors.HexColor("#DFF2E8")
LIGHT_RED = colors.HexColor("#FCE4E4")
DARK_GREY = colors.HexColor("#444444")
WHITE = colors.white
BLACK = colors.black

# ============================================================
# REPORT STYLES
# ============================================================

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    name="ReportTitle",
    parent=styles["Title"],
    fontName="Helvetica-Bold",
    fontSize=23,
    leading=29,
    textColor=DARK_BLUE,
    alignment=TA_CENTER,
    spaceAfter=15,
)

cover_subtitle_style = ParagraphStyle(
    name="CoverSubtitle",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=15,
    leading=20,
    textColor=BLUE,
    alignment=TA_CENTER,
    spaceAfter=12,
)

section_style = ParagraphStyle(
    name="Section",
    parent=styles["Heading1"],
    fontName="Helvetica-Bold",
    fontSize=16,
    leading=20,
    textColor=DARK_BLUE,
    spaceBefore=5,
    spaceAfter=12,
)

subsection_style = ParagraphStyle(
    name="Subsection",
    parent=styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=12,
    leading=16,
    textColor=BLUE,
    spaceBefore=10,
    spaceAfter=7,
)

body_style = ParagraphStyle(
    name="Body",
    parent=styles["BodyText"],
    fontName="Helvetica",
    fontSize=9.5,
    leading=14,
    textColor=BLACK,
    alignment=TA_LEFT,
    spaceAfter=7,
)

small_style = ParagraphStyle(
    name="Small",
    parent=body_style,
    fontSize=8,
    leading=10.5,
)

note_style = ParagraphStyle(
    name="Note",
    parent=body_style,
    fontSize=8.5,
    leading=12,
    textColor=DARK_GREY,
    backColor=LIGHT_GREY,
    borderColor=colors.HexColor("#BFBFBF"),
    borderWidth=0.5,
    borderPadding=7,
    spaceBefore=6,
    spaceAfter=8,
)

critical_style = ParagraphStyle(
    name="Critical",
    parent=body_style,
    fontName="Helvetica-Bold",
    textColor=RED,
    backColor=LIGHT_RED,
    borderColor=RED,
    borderWidth=0.5,
    borderPadding=7,
    spaceBefore=6,
    spaceAfter=8,
)

recommendation_style = ParagraphStyle(
    name="Recommendation",
    parent=body_style,
    backColor=LIGHT_GREEN,
    borderColor=GREEN,
    borderWidth=0.5,
    borderPadding=7,
    spaceBefore=6,
    spaceAfter=8,
)

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def paragraph(text, style=body_style):
    return Paragraph(str(text), style)


def convert_table_data(rows):
    converted = []

    for row in rows:
        converted.append(
            [
                Paragraph("" if value is None else str(value), small_style)
                for value in row
            ]
        )

    return converted


def make_table(rows, widths=None, header=True):
    table = Table(
        convert_table_data(rows),
        colWidths=widths,
        repeatRows=1 if header else 0,
        hAlign="LEFT",
    )

    commands = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B8B8B8")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]

    if header:
        commands.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )

        for row_number in range(1, len(rows)):
            if row_number % 2 == 0:
                commands.append(
                    (
                        "BACKGROUND",
                        (0, row_number),
                        (-1, row_number),
                        LIGHT_GREY,
                    )
                )

    table.setStyle(TableStyle(commands))
    return table


def add_page_number(canvas, document):
    canvas.saveState()

    page_number = canvas.getPageNumber()
    page_width, page_height = A4

    canvas.setStrokeColor(colors.HexColor("#CCCCCC"))
    canvas.setLineWidth(0.5)
    canvas.line(38, 34, page_width - 38, 34)

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(DARK_GREY)

    canvas.drawString(
        38,
        21,
        "Enterprise BI - Executive Report",
    )

    canvas.drawRightString(
        page_width - 38,
        21,
        f"Page {page_number}",
    )

    canvas.restoreState()


# ============================================================
# CHART CREATION
# ============================================================

def create_profitability_chart():
    labels = [
        "Revenue",
        "Product Cost",
        "Other Costs",
        "Net Profit",
    ]

    values = [
        48.43,
        31.51,
        20.17,
        -3.25,
    ]

    # Matplotlib expects #RRGGBB values.
    chart_colours = [
        "#2774AE",
        "#E67E22",
        "#8E44AD",
        "#D64545",
    ]

    plt.figure(figsize=(8, 4.3))

    bars = plt.bar(
        labels,
        values,
        color=chart_colours,
    )

    plt.axhline(
        y=0,
        color="black",
        linewidth=0.8,
    )

    plt.ylabel("INR Crore")
    plt.title("Company Profitability Overview")
    plt.grid(
        axis="y",
        linestyle="--",
        alpha=0.25,
    )

    for bar, value in zip(bars, values):
        if value >= 0:
            text_position = value + 0.6
            vertical_alignment = "bottom"
        else:
            text_position = value - 0.6
            vertical_alignment = "top"

        plt.text(
            bar.get_x() + bar.get_width() / 2,
            text_position,
            f"{value:.2f}",
            ha="center",
            va=vertical_alignment,
            fontsize=9,
            fontweight="bold",
        )

    plt.tight_layout()

    output_file = CHART_FOLDER / "profitability_overview.png"

    plt.savefig(
        output_file,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close()

    return output_file


def create_root_cause_chart():
    problem_names = [
        "Supplier\nExposure",
        "Excess\nInventory",
        "Overdue\nReceivables",
        "Revenue\nDifference",
        "Net Loss",
    ]

    financial_values = [
        2539.43,
        79.77,
        4.52,
        3.90,
        3.25,
    ]

    chart_colours = [
        "#D64545",
        "#E67E22",
        "#2774AE",
        "#8E44AD",
        "#C0392B",
    ]

    plt.figure(figsize=(8.2, 4.4))

    bars = plt.bar(
        problem_names,
        financial_values,
        color=chart_colours,
    )

    # Log scale allows small and large values to be visible.
    plt.yscale("log")

    plt.ylabel("Financial Exposure in INR Crore - Log Scale")
    plt.title("Five Largest Business Problems")

    plt.grid(
        axis="y",
        linestyle="--",
        alpha=0.25,
    )

    for bar, value in zip(bars, financial_values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            value * 1.12,
            f"{value:,.2f}",
            ha="center",
            fontsize=8,
            fontweight="bold",
        )

    plt.tight_layout()

    output_file = CHART_FOLDER / "root_cause_summary.png"

    plt.savefig(
        output_file,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close()

    return output_file


# ============================================================
# REPORT CONTENT
# ============================================================

story = []

# ------------------------------------------------------------
# COVER PAGE
# ------------------------------------------------------------

story.append(Spacer(1, 0.75 * inch))

story.append(
    paragraph(
        "ENTERPRISE BUSINESS INTELLIGENCE",
        title_style,
    )
)

story.append(
    paragraph(
        "Root Cause and Profitability Analysis",
        title_style,
    )
)

story.append(Spacer(1, 0.2 * inch))

story.append(
    paragraph(
        "Executive Management Report",
        cover_subtitle_style,
    )
)

story.append(Spacer(1, 0.45 * inch))

cover_information = [
    ["Prepared By", "Santhosh Kumar M"],
    ["Role", "Data Analyst"],
    ["Analysis Period", "September 2025 to August 2026"],
    ["Datasets Analyzed", "18 enterprise datasets"],
    ["Tools Used", "MySQL, Python, Power BI and Excel"],
    ["Report Generated", datetime.now().strftime("%d %B %Y")],
]

story.append(
    make_table(
        cover_information,
        widths=[
            1.8 * inch,
            3.8 * inch,
        ],
        header=False,
    )
)

story.append(Spacer(1, 0.6 * inch))

story.append(
    paragraph(
        "Confidential - Prepared for Senior Management",
        ParagraphStyle(
            name="Confidential",
            parent=cover_subtitle_style,
            fontSize=11,
            textColor=RED,
        ),
    )
)

story.append(PageBreak())

# ------------------------------------------------------------
# 1. EXECUTIVE SUMMARY
# ------------------------------------------------------------

story.append(
    paragraph(
        "1. Executive Summary",
        section_style,
    )
)

story.append(
    paragraph(
        "The analysis confirms that the company has a strong revenue base, "
        "but it is not converting revenue into profit. Total analyzed revenue "
        "was INR 48.43 crore, while the company recorded a net loss of "
        "INR 3.25 crore and a net profit margin of -6.70%."
    )
)

executive_summary = [
    ["KPI", "Result", "Management Interpretation"],
    ["Revenue", "INR 48.43 Cr", "Strong sales volume"],
    ["Net Profit", "INR -3.25 Cr", "Company is loss-making"],
    ["Profit Margin", "-6.70%", "Cost structure is unsustainable"],
    [
        "Revenue Reconciliation Gap",
        "INR 3.90 Cr",
        "Revenue reports do not reconcile",
    ],
    [
        "Overdue Receivables >180 Days",
        "INR 4.52 Cr",
        "High collection and credit risk",
    ],
    [
        "Excess Inventory Value",
        "INR 79.77 Cr",
        "Significant working-capital blockage",
    ],
    [
        "Supplier On-Time Delivery",
        "11.22%",
        "Supplier performance is unacceptable",
    ],
    [
        "Next-Quarter Revenue Forecast",
        "INR 12.31 Cr",
        "98.15% of target; target is at risk",
    ],
]

story.append(
    make_table(
        executive_summary,
        widths=[
            1.65 * inch,
            1.35 * inch,
            3.45 * inch,
        ],
    )
)

story.append(Spacer(1, 0.12 * inch))

story.append(
    paragraph(
        "<b>Primary conclusion:</b> Revenue growth alone is not creating "
        "business value. Product cost, marketing cost, excess inventory, "
        "supplier delays, returns, discounts and collection delays are "
        "reducing profitability and cash flow.",
        recommendation_style,
    )
)

story.append(PageBreak())

# ------------------------------------------------------------
# 2. DATA QUALITY
# ------------------------------------------------------------

story.append(
    paragraph(
        "2. Data Quality Investigation",
        section_style,
    )
)

story.append(
    paragraph(
        "An automated data-quality audit was performed across all 18 datasets. "
        "The audit checked duplicate records, missing keys, invalid dates, "
        "future dates, negative quantities, invalid prices, unmatched records "
        "and broken foreign-key relationships."
    )
)

data_quality_rows = [
    ["Dataset", "Records"],
    ["Customer Complaints", "10,036"],
    ["Customer Master", "19,354"],
    ["Employee Attendance", "49,444"],
    ["Employee Master", "499"],
    ["Inventory", "118,469"],
    ["Invoices", "101,080"],
    ["Marketing Campaigns", "4,941"],
    ["Monthly Targets", "240"],
    ["Order Items", "245,340"],
    ["Orders", "99,266"],
    ["Payments", "76,362"],
    ["Product Master", "992"],
    ["Purchases", "23,588"],
    ["Region Master", "20"],
    ["Returns", "14,751"],
    ["Sales", "244,188"],
    ["Suppliers", "200"],
    ["Website Activity", "198,400"],
]

story.append(
    make_table(
        data_quality_rows,
        widths=[
            3.5 * inch,
            2.0 * inch,
        ],
    )
)

story.append(Spacer(1, 0.1 * inch))

story.append(
    paragraph(
        "The audit identified duplicate records, missing values, invalid zero "
        "dates, unmatched references and negative inventory. Cleaning and "
        "quality scoring were completed using automated scripts without "
        "manually modifying individual source records.",
        note_style,
    )
)

story.append(PageBreak())

# ------------------------------------------------------------
# 3. REVENUE RECONCILIATION
# ------------------------------------------------------------

story.append(
    paragraph(
        "3. Revenue Reconciliation",
        section_style,
    )
)

reconciliation_rows = [
    ["Reconciliation Component", "Result"],
    ["Management Revenue", "INR 52.00 Cr"],
    ["Database Gross Sales", "INR 49.92 Cr"],
    ["Sales Revenue after adjustment", "INR 48.43 Cr"],
    ["Returns", "INR 1.50 Cr"],
    ["Refunds", "INR 0.32 Cr"],
    ["Unmatched Transactions", "798 records"],
    ["Final Reconciliation Difference", "INR 3.90 Cr"],
]

story.append(
    make_table(
        reconciliation_rows,
        widths=[
            3.6 * inch,
            2.3 * inch,
        ],
    )
)

story.append(Spacer(1, 0.12 * inch))

story.append(
    paragraph(
        "<b>Root cause:</b> Management and database reports use different "
        "revenue definitions. Unmatched transactions and inconsistent treatment "
        "of returns, refunds, invoices and payments contribute to the difference."
    )
)

story.append(
    paragraph(
        "<b>Recommended action:</b> Establish one governed revenue definition "
        "and automate order-to-cash reconciliation before publishing monthly "
        "management reports.",
        recommendation_style,
    )
)

story.append(PageBreak())

# ------------------------------------------------------------
# 4. PROFITABILITY
# ------------------------------------------------------------

story.append(
    paragraph(
        "4. Profitability Investigation",
        section_style,
    )
)

profitability_rows = [
    ["Profitability Component", "Amount"],
    ["Revenue", "INR 48.43 Cr"],
    ["Discounts", "INR 1.50 Cr"],
    ["Refunds", "INR 0.32 Cr"],
    ["Product Cost", "INR 31.51 Cr"],
    ["Shipping Cost", "INR 1.59 Cr"],
    ["Payment Fees", "INR 0.87 Cr"],
    ["Allocated Marketing Cost", "INR 17.38 Cr"],
    ["Net Profit", "INR -3.25 Cr"],
    ["Net Profit Margin", "-6.70%"],
]

story.append(
    make_table(
        profitability_rows,
        widths=[
            3.6 * inch,
            2.3 * inch,
        ],
    )
)

profitability_chart = create_profitability_chart()

story.append(Spacer(1, 0.1 * inch))

story.append(
    Image(
        str(profitability_chart),
        width=6.3 * inch,
        height=3.35 * inch,
    )
)

story.append(
    paragraph(
        "Marketing cost and product cost are the largest profitability pressures. "
        "All major categories and regions generated negative net profit. "
        "Approximately 990 products were classified as negative-profit products.",
        critical_style,
    )
)

story.append(PageBreak())

# ------------------------------------------------------------
# 5. CUSTOMER AND COHORT
# ------------------------------------------------------------

story.append(
    paragraph(
        "5. Customer and Cohort Analytics",
        section_style,
    )
)

customer_rows = [
    [
        "Customer Segment",
        "Customers",
        "Revenue",
        "Net Profit",
        "Margin",
    ],
    [
        "At Risk",
        "7,834",
        "INR 18.73 Cr",
        "INR -1.27 Cr",
        "-6.79%",
    ],
    [
        "Regular",
        "6,963",
        "INR 14.94 Cr",
        "INR -1.09 Cr",
        "-7.27%",
    ],
    [
        "Low Value",
        "3,905",
        "INR 11.79 Cr",
        "INR -0.70 Cr",
        "-5.96%",
    ],
    [
        "High Value",
        "1,007",
        "INR 2.89 Cr",
        "INR -0.18 Cr",
        "-6.16%",
    ],
    [
        "Churned",
        "46",
        "INR 0.07 Cr",
        "INR -0.005 Cr",
        "-7.75%",
    ],
]

story.append(
    make_table(
        customer_rows,
        widths=[
            1.2 * inch,
            0.8 * inch,
            1.3 * inch,
            1.3 * inch,
            0.8 * inch,
        ],
    )
)

story.append(
    paragraph(
        "Cohort Retention Findings",
        subsection_style,
    )
)

cohort_rows = [
    ["Cohort", "Customers", "Month-1 Retention", "Trend"],
    ["September 2025", "12,152", "42.59%", "First cohort"],
    ["October 2025", "7,245", "40.29%", "Declining"],
    ["November 2025", "340", "1.18%", "Sharp decline"],
    ["December 2025", "14", "50.00%", "Small cohort"],
    ["January 2026", "4", "25.00%", "Small cohort"],
]

story.append(
    make_table(
        cohort_rows,
        widths=[
            1.5 * inch,
            1.0 * inch,
            1.6 * inch,
            1.6 * inch,
        ],
    )
)

story.append(
    paragraph(
        "The November 2025 cohort experienced the largest retention decline. "
        "December 2025 and January 2026 contain very small cohorts and should "
        "not be used for strong management conclusions.",
        note_style,
    )
)

story.append(PageBreak())

# ------------------------------------------------------------
# 6. PRODUCT AND MARKETING
# ------------------------------------------------------------

story.append(
    paragraph(
        "6. Product and Marketing Analysis",
        section_style,
    )
)

product_rows = [
    ["Product Finding", "Result"],
    ["Products Analyzed", "992"],
    ["Negative-Profit Products", "990"],
    ["Highest-Revenue Category", "Accessories - INR 8.27 Cr"],
    ["Category Profitability", "All major categories negative"],
    ["Category Margin Range", "Approximately -6.65% to -6.75%"],
    ["Main Product Issue", "Revenue increasing without positive profit"],
]

story.append(
    make_table(
        product_rows,
        widths=[
            2.6 * inch,
            3.5 * inch,
        ],
    )
)

story.append(
    paragraph(
        "Marketing Attribution",
        subsection_style,
    )
)

marketing_rows = [
    ["Channel", "Linear Revenue", "Linear Profit", "Profit ROI"],
    ["Instagram", "INR 82.51 L", "INR -5.50 L", "-1.60%"],
    ["Google Ads", "INR 79.69 L", "INR -5.51 L", "-1.63%"],
    ["Email", "INR 85.80 L", "INR -5.70 L", "-1.64%"],
    ["Organic Search", "INR 83.89 L", "INR -5.73 L", "-1.60%"],
    ["Referral", "INR 88.59 L", "INR -5.78 L", "-1.64%"],
]

story.append(
    make_table(
        marketing_rows,
        widths=[
            1.4 * inch,
            1.6 * inch,
            1.6 * inch,
            1.1 * inch,
        ],
    )
)

story.append(
    paragraph(
        "Instagram produced the least negative attributed profit. However, "
        "no marketing channel produced positive attributed profit. Therefore, "
        "Instagram should not be described as a profitable channel.",
        critical_style,
    )
)

story.append(PageBreak())

# ------------------------------------------------------------
# 7. A/B TEST
# ------------------------------------------------------------

story.append(
    paragraph(
        "7. A/B Test Investigation",
        section_style,
    )
)

ab_group_rows = [
    ["Metric", "Control", "Treatment"],
    ["Sessions", "50,000", "49,993"],
    ["Conversions", "4,302", "4,328"],
    ["Conversion Rate", "8.6040%", "8.6572%"],
    [
        "95% Group Confidence Interval",
        "8.3582% to 8.8498%",
        "8.4107% to 8.9037%",
    ],
]

story.append(
    make_table(
        ab_group_rows,
        widths=[
            2.0 * inch,
            2.0 * inch,
            2.0 * inch,
        ],
    )
)

story.append(Spacer(1, 0.12 * inch))

ab_result_rows = [
    ["Statistical Measure", "Result"],
    ["Absolute Lift", "0.0532 percentage points"],
    ["Relative Lift", "0.6185%"],
    ["Z Statistic", "0.299601"],
    ["P-Value", "0.764481"],
    ["95% CI for Difference", "-0.2949% to 0.4013%"],
    ["Cohen's H", "0.001895 - negligible effect"],
    ["Statistical Decision", "Not statistically significant"],
]

story.append(
    make_table(
        ab_result_rows,
        widths=[
            2.6 * inch,
            3.5 * inch,
        ],
    )
)

story.append(
    paragraph(
        "<b>Management decision:</b> Do not permanently implement the treatment "
        "checkout design yet. Continue testing because the observed improvement "
        "is extremely small and the p-value is greater than 0.05.",
        recommendation_style,
    )
)

story.append(PageBreak())

# ------------------------------------------------------------
# 8. INVENTORY
# ------------------------------------------------------------

story.append(
    paragraph(
        "8. Inventory Investigation",
        section_style,
    )
)

inventory_rows = [
    ["Inventory Metric", "Result"],
    ["Inventory Turnover", "0.12 times"],
    ["Days Inventory", "2,966.72 days"],
    ["Stockout Rate", "11.66%"],
    ["Critical Products", "9"],
    ["Dead-Stock Products", "62"],
    ["Negative Inventory Products", "120"],
    ["Excess Inventory Units", "123,207.55"],
    ["Excess Inventory Value", "INR 79.77 Cr"],
]

story.append(
    make_table(
        inventory_rows,
        widths=[
            3.5 * inch,
            2.3 * inch,
        ],
    )
)

story.append(
    paragraph(
        "The company simultaneously holds substantial excess inventory and "
        "experiences stockout risk for high-demand products. This indicates "
        "ineffective demand planning and reorder policies.",
        critical_style,
    )
)

story.append(
    paragraph(
        "<b>Recommended action:</b> Freeze purchases for dead-stock products, "
        "liquidate excess stock, correct negative inventory records and introduce "
        "demand-based reorder points using supplier lead time.",
        recommendation_style,
    )
)

story.append(PageBreak())

# ------------------------------------------------------------
# 9. SUPPLIER ANALYTICS
# ------------------------------------------------------------

story.append(
    paragraph(
        "9. Supplier Analytics",
        section_style,
    )
)

supplier_rows = [
    ["Supplier Metric", "Result"],
    ["Total Suppliers", "200"],
    ["Total Purchase Value", "INR 4,066.00 Cr"],
    ["Average Delivery Time", "24.46 days"],
    ["Overall On-Time Delivery", "11.22%"],
    ["Overall Rejection Rate", "0.81%"],
    ["Average Supplier Score", "54.97"],
    ["Suppliers Requiring Review", "121"],
    ["Best Supplier", "Supplier 075 - Score 68.34"],
    ["Lowest-Ranked Supplier", "Supplier 134 - Score 38.89"],
    ["Declining Supplier", "Supplier 061"],
]

story.append(
    make_table(
        supplier_rows,
        widths=[
            3.2 * inch,
            2.7 * inch,
        ],
    )
)

story.append(
    paragraph(
        "Supplier 061 demonstrated increasing cost with declining delivery and "
        "quality indicators. Supplier 134 received the lowest overall performance "
        "score and requires formal review."
    )
)

story.append(
    paragraph(
        "<b>Recommended action:</b> Renegotiate pricing and service-level "
        "agreements, introduce delivery penalties, perform quality audits and "
        "shift critical purchase volume to better-performing suppliers.",
        recommendation_style,
    )
)

story.append(PageBreak())

# ------------------------------------------------------------
# 10. FORECASTING
# ------------------------------------------------------------

story.append(
    paragraph(
        "10. Forecasting and Target Achievement",
        section_style,
    )
)

forecast_rows = [
    [
        "Forecast Month",
        "Revenue Forecast",
        "Revenue Target",
        "Achievement",
        "Status",
    ],
    [
        "September 2026",
        "INR 4.10 Cr",
        "INR 4.36 Cr",
        "93.89%",
        "At Risk",
    ],
    [
        "October 2026",
        "INR 4.10 Cr",
        "INR 4.18 Cr",
        "98.15%",
        "At Risk",
    ],
    [
        "November 2026",
        "INR 4.11 Cr",
        "INR 4.00 Cr",
        "102.80%",
        "Above Target",
    ],
    [
        "Next Quarter",
        "INR 12.31 Cr",
        "INR 12.55 Cr",
        "98.15%",
        "At Risk",
    ],
]

story.append(
    make_table(
        forecast_rows,
        widths=[
            1.3 * inch,
            1.35 * inch,
            1.3 * inch,
            1.1 * inch,
            1.15 * inch,
        ],
    )
)

story.append(
    paragraph(
        "The next-quarter revenue forecast is INR 12.31 crore against a target "
        "of INR 12.55 crore. Forecast achievement is 98.15%, leaving a forecast "
        "shortfall of approximately INR 0.23 crore."
    )
)

story.append(
    paragraph(
        "The forecast uses only 12 months of monthly history. Seasonality, "
        "promotions, market changes, pricing decisions and data corrections "
        "may materially affect actual performance.",
        note_style,
    )
)

story.append(PageBreak())

# ------------------------------------------------------------
# 11. ANOMALY DETECTION
# ------------------------------------------------------------

story.append(
    paragraph(
        "11. Multi-Factor Anomaly Detection",
        section_style,
    )
)

anomaly_rows = [
    [
        "Dataset",
        "Total Records",
        "Model Flagged",
        "Critical / High Risk",
        "Maximum Score",
    ],
    [
        "Sales",
        "246,370",
        "2,464",
        "1,456 critical",
        "97.24",
    ],
    [
        "Payments",
        "76,510",
        "766",
        "9,764 high-risk",
        "89.36",
    ],
    [
        "Inventory",
        "119,040",
        "1,188",
        "3,807 rule-critical",
        "99.09",
    ],
]

story.append(
    make_table(
        anomaly_rows,
        widths=[
            1.05 * inch,
            1.25 * inch,
            1.2 * inch,
            1.65 * inch,
            1.1 * inch,
        ],
    )
)

story.append(
    paragraph(
        "The anomaly score used transaction amount, transaction frequency, "
        "historical customer behaviour, product behaviour, discount and refund "
        "behaviour, time patterns, inventory movements and an Isolation Forest "
        "machine-learning score."
    )
)

story.append(
    paragraph(
        "The highest-risk records involved negative closing stock, unusual "
        "inventory movement, abnormal stock-value changes and negative inventory "
        "value. The maximum observed anomaly score was 99.09.",
        critical_style,
    )
)

story.append(PageBreak())

# ------------------------------------------------------------
# 12. EXECUTIVE EXCEPTION ENGINE
# ------------------------------------------------------------

story.append(
    paragraph(
        "12. Executive Exception Engine",
        section_style,
    )
)

exception_rows = [
    ["Exception Metric", "Result"],
    ["Total Exceptions", "14,367"],
    ["Critical Exceptions", "2,122"],
    ["High-Priority Exceptions", "12,245"],
    ["Negative-Profit Products", "990"],
    ["Critical Inventory Products", "9"],
    ["Negative Inventory Products", "120"],
    ["Unique Overdue Invoices >180 Days", "11,771"],
    ["Total Overdue Amount >180 Days", "INR 4.52 Cr"],
    ["Suppliers Requiring Review", "121"],
    ["Critical Anomalies", "1,000"],
]

story.append(
    make_table(
        exception_rows,
        widths=[
            3.7 * inch,
            2.2 * inch,
        ],
    )
)

story.append(
    paragraph(
        "Gross exception exposure contains overlapping business issues and "
        "must not be interpreted as unique company loss. The same inventory, "
        "supplier or product exposure may appear under multiple exception types.",
        note_style,
    )
)

story.append(PageBreak())

# ------------------------------------------------------------
# 13. FIVE ROOT CAUSES
# ------------------------------------------------------------

story.append(
    paragraph(
        "13. Five Largest Business Problems",
        section_style,
    )
)

root_cause_rows = [
    [
        "Rank",
        "Business Problem",
        "Actual Result",
        "Impact / Exposure",
    ],
    [
        "1",
        "Revenue generated but company remains unprofitable",
        "INR 3.25 Cr loss",
        "INR 3.25 Cr",
    ],
    [
        "2",
        "Excess inventory and extremely low turnover",
        "INR 79.77 Cr excess",
        "INR 79.77 Cr",
    ],
    [
        "3",
        "Supplier delivery performance is unacceptable",
        "11.22% on-time",
        "INR 2,539.43 Cr purchase exposure",
    ],
    [
        "4",
        "Revenue reports do not reconcile",
        "INR 3.90 Cr gap",
        "INR 3.90 Cr",
    ],
    [
        "5",
        "Long-overdue customer receivables",
        "INR 4.52 Cr overdue",
        "INR 4.52 Cr",
    ],
]

story.append(
    make_table(
        root_cause_rows,
        widths=[
            0.45 * inch,
            2.8 * inch,
            1.45 * inch,
            1.65 * inch,
        ],
    )
)

root_cause_chart = create_root_cause_chart()

story.append(Spacer(1, 0.1 * inch))

story.append(
    Image(
        str(root_cause_chart),
        width=6.3 * inch,
        height=3.35 * inch,
    )
)

story.append(
    paragraph(
        "Supplier purchase exposure represents the purchase value influenced "
        "by supplier-performance issues. It is not equivalent to realized "
        "financial loss.",
        note_style,
    )
)

story.append(PageBreak())

# ------------------------------------------------------------
# 14. MANAGEMENT RECOMMENDATIONS
# ------------------------------------------------------------

story.append(
    paragraph(
        "14. Management Recommendations",
        section_style,
    )
)

recommendation_rows = [
    [
        "Priority",
        "Recommended Action",
        "Expected Benefit",
    ],
    [
        "Critical",
        "Correct loss-making prices and control product, shipping, payment and marketing costs.",
        "Restore positive contribution margin.",
    ],
    [
        "Critical",
        "Automate order-to-cash reconciliation using one governed revenue definition.",
        "Eliminate inconsistent revenue reporting.",
    ],
    [
        "Critical",
        "Freeze dead-stock purchases and introduce demand-based reorder points.",
        "Release working capital and reduce stock risk.",
    ],
    [
        "Critical",
        "Renegotiate low-performing suppliers and enforce service-level penalties.",
        "Improve availability and delivery reliability.",
    ],
    [
        "High",
        "Create ageing-based collection workflows and review customer credit limits.",
        "Reduce overdue receivables and improve cash flow.",
    ],
    [
        "High",
        "Redesign marketing campaigns that generate negative attributed profit.",
        "Improve customer acquisition economics.",
    ],
    [
        "High",
        "Investigate critical anomalies before transaction approval or reporting.",
        "Reduce fraud, errors and operational leakage.",
    ],
    [
        "Medium",
        "Continue the checkout A/B test using a predefined sample-size requirement.",
        "Avoid unsupported implementation decisions.",
    ],
]

story.append(
    make_table(
        recommendation_rows,
        widths=[
            0.85 * inch,
            3.45 * inch,
            2.05 * inch,
        ],
    )
)

story.append(PageBreak())

# ------------------------------------------------------------
# 15. LIMITATIONS AND CONCLUSION
# ------------------------------------------------------------

story.append(
    paragraph(
        "15. Assumptions, Limitations and Conclusion",
        section_style,
    )
)

limitations = [
    "The source data intentionally contained duplicates, missing values, invalid dates and reconciliation problems.",
    "Financial results depend on the available fields and the analytical calculation logic used in this project.",
    "Allocated marketing cost is an analytical allocation and may differ from accounting treatment.",
    "Forecasting uses only 12 months of monthly history and should be refreshed as more data becomes available.",
    "Supplier purchase exposure and gross exception exposure are not equivalent to realized financial loss.",
    "A/B test conclusions apply only to the available experiment population and test period.",
    "Cohorts containing very few customers should not drive major management decisions.",
]

for number, limitation in enumerate(limitations, start=1):
    story.append(
        paragraph(
            f"{number}. {limitation}"
        )
    )

story.append(Spacer(1, 0.15 * inch))

story.append(
    paragraph(
        "<b>Final conclusion:</b> The company has a strong revenue base, but "
        "cost control, inventory planning, supplier performance, collections "
        "and data governance require immediate improvement. Management should "
        "prioritize profitability and cash conversion instead of focusing only "
        "on revenue growth.",
        recommendation_style,
    )
)

story.append(
    paragraph(
        "Supporting evidence is available in the Data Quality, SQL, Python, "
        "Power BI, Reconciliation, Exception, Forecasting, Inventory, Marketing, "
        "Supplier, Anomaly and Root Cause Analysis folders.",
        note_style,
    )
)

# ============================================================
# CREATE PDF
# ============================================================

document = SimpleDocTemplate(
    str(OUTPUT_PDF),
    pagesize=A4,
    rightMargin=38,
    leftMargin=38,
    topMargin=42,
    bottomMargin=48,
    title="Enterprise BI Root Cause and Profitability Analysis",
    author="Santhosh Kumar M",
    subject="Executive Business Intelligence Report",
)

document.build(
    story,
    onFirstPage=add_page_number,
    onLaterPages=add_page_number,
)

print("=" * 78)
print("EXECUTIVE REPORT CREATED SUCCESSFULLY")
print("=" * 78)
print()
print("PDF saved in:")
print(OUTPUT_PDF)
print()
print("Open the PDF and verify all pages before final submission.")