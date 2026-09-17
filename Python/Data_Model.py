from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# ============================================================
# PATH CONFIGURATION
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

OUTPUT_FOLDER = PROJECT_ROOT / "Data_Model"
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

MARKDOWN_FILE = OUTPUT_FOLDER / "Enterprise_Data_Model.md"
PNG_FILE = OUTPUT_FOLDER / "Enterprise_Data_Model.png"
PDF_FILE = OUTPUT_FOLDER / "Enterprise_Data_Model.pdf"

# ============================================================
# TABLE DEFINITIONS
# ============================================================

tables = [
    (
        "region_master",
        "Dimension",
        "Region_ID",
        "Region and warehouse details",
    ),
    (
        "customer_master",
        "Dimension",
        "Customer_ID",
        "Customer details and regional assignment",
    ),
    (
        "product_master",
        "Dimension",
        "Product_ID",
        "Product, category, supplier, price and cost",
    ),
    (
        "employee_master",
        "Dimension",
        "Employee_ID",
        "Employee, manager and regional details",
    ),
    (
        "suppliers",
        "Dimension",
        "Supplier_ID",
        "Supplier descriptive information",
    ),
    (
        "orders",
        "Fact",
        "Order_ID",
        "One row per customer order",
    ),
    (
        "order_items",
        "Bridge / Fact",
        "Order_Item_ID",
        "One row per order and product combination",
    ),
    (
        "sales",
        "Fact",
        "Sale_ID",
        "One row per sales transaction",
    ),
    (
        "returns",
        "Fact",
        "Return_ID",
        "One row per returned order item",
    ),
    (
        "invoices",
        "Fact",
        "Invoice_ID",
        "One row per customer invoice",
    ),
    (
        "payments",
        "Fact",
        "Payment_ID",
        "One row per payment transaction",
    ),
    (
        "purchases",
        "Fact",
        "Purchase_ID",
        "One row per supplier purchase",
    ),
    (
        "inventory",
        "Snapshot Fact",
        "Inventory_ID",
        "One row per product, warehouse and snapshot date",
    ),
    (
        "marketing_campaigns",
        "Fact",
        "Campaign_ID",
        "One row per marketing campaign",
    ),
    (
        "website_activity",
        "Event Fact",
        "Event_ID",
        "One row per website event",
    ),
    (
        "customer_complaints",
        "Fact",
        "Complaint_ID",
        "One row per customer complaint",
    ),
    (
        "employee_attendance",
        "Fact",
        "Attendance_ID",
        "One row per employee attendance date",
    ),
    (
        "monthly_targets",
        "Fact",
        "Target_ID",
        "One row per region and target month",
    ),
]

# Parent table, parent key, child table, child key, relationship
relationships = [
    (
        "region_master",
        "Region_ID",
        "customer_master",
        "Region_ID",
        "One-to-Many",
    ),
    (
        "region_master",
        "Region_ID",
        "employee_master",
        "Region_ID",
        "One-to-Many",
    ),
    (
        "region_master",
        "Region_ID",
        "orders",
        "Region_ID",
        "One-to-Many",
    ),
    (
        "region_master",
        "Region_ID",
        "sales",
        "Region_ID",
        "One-to-Many",
    ),
    (
        "region_master",
        "Region_ID",
        "monthly_targets",
        "Region_ID",
        "One-to-Many",
    ),
    (
        "customer_master",
        "Customer_ID",
        "orders",
        "Customer_ID",
        "One-to-Many",
    ),
    (
        "customer_master",
        "Customer_ID",
        "sales",
        "Customer_ID",
        "One-to-Many",
    ),
    (
        "customer_master",
        "Customer_ID",
        "returns",
        "Customer_ID",
        "One-to-Many",
    ),
    (
        "customer_master",
        "Customer_ID",
        "invoices",
        "Customer_ID",
        "One-to-Many",
    ),
    (
        "customer_master",
        "Customer_ID",
        "payments",
        "Customer_ID",
        "One-to-Many",
    ),
    (
        "customer_master",
        "Customer_ID",
        "website_activity",
        "Customer_ID",
        "One-to-Many",
    ),
    (
        "customer_master",
        "Customer_ID",
        "customer_complaints",
        "Customer_ID",
        "One-to-Many",
    ),
    (
        "employee_master",
        "Employee_ID",
        "orders",
        "Sales_Employee_ID",
        "One-to-Many",
    ),
    (
        "employee_master",
        "Employee_ID",
        "sales",
        "Employee_ID",
        "One-to-Many",
    ),
    (
        "employee_master",
        "Employee_ID",
        "employee_attendance",
        "Employee_ID",
        "One-to-Many",
    ),
    (
        "suppliers",
        "Supplier_ID",
        "product_master",
        "Supplier_ID",
        "One-to-Many",
    ),
    (
        "suppliers",
        "Supplier_ID",
        "purchases",
        "Supplier_ID",
        "One-to-Many",
    ),
    (
        "orders",
        "Order_ID",
        "order_items",
        "Order_ID",
        "One-to-Many",
    ),
    (
        "orders",
        "Order_ID",
        "sales",
        "Order_ID",
        "One-to-Many",
    ),
    (
        "orders",
        "Order_ID",
        "returns",
        "Order_ID",
        "One-to-Many",
    ),
    (
        "orders",
        "Order_ID",
        "invoices",
        "Order_ID",
        "One-to-Many",
    ),
    (
        "orders",
        "Order_ID",
        "website_activity",
        "Order_ID",
        "One-to-Many Optional",
    ),
    (
        "orders",
        "Order_ID",
        "customer_complaints",
        "Order_ID",
        "One-to-Many",
    ),
    (
        "order_items",
        "Order_Item_ID",
        "sales",
        "Order_Item_ID",
        "One-to-Many",
    ),
    (
        "order_items",
        "Order_Item_ID",
        "returns",
        "Order_Item_ID",
        "One-to-Many",
    ),
    (
        "product_master",
        "Product_ID",
        "order_items",
        "Product_ID",
        "One-to-Many",
    ),
    (
        "product_master",
        "Product_ID",
        "sales",
        "Product_ID",
        "One-to-Many",
    ),
    (
        "product_master",
        "Product_ID",
        "returns",
        "Product_ID",
        "One-to-Many",
    ),
    (
        "product_master",
        "Product_ID",
        "purchases",
        "Product_ID",
        "One-to-Many",
    ),
    (
        "product_master",
        "Product_ID",
        "inventory",
        "Product_ID",
        "One-to-Many",
    ),
    (
        "invoices",
        "Invoice_ID",
        "payments",
        "Invoice_ID",
        "One-to-Many",
    ),
]

# ============================================================
# CREATE MARKDOWN DOCUMENT
# ============================================================

markdown_lines = []

markdown_lines.append(
    "# Enterprise Business Intelligence Data Model"
)
markdown_lines.append("")

markdown_lines.append("## 1. Model Objective")
markdown_lines.append("")
markdown_lines.append(
    "This analytical model supports revenue, profitability, customer, "
    "product, inventory, supplier, marketing, employee and finance "
    "analysis for the Enterprise Business Intelligence project."
)
markdown_lines.append("")
markdown_lines.append(
    "The model connects all 18 datasets using primary-key and "
    "foreign-key relationships."
)
markdown_lines.append("")

markdown_lines.append("## 2. Modeling Approach")
markdown_lines.append("")
markdown_lines.append(
    "- Dimension tables contain descriptive business entities."
)
markdown_lines.append(
    "- Fact tables contain transactions, balances, events and measures."
)
markdown_lines.append(
    "- Bridge tables resolve many-to-many relationships."
)
markdown_lines.append(
    "- Inventory is modeled as a product-warehouse-date snapshot fact."
)
markdown_lines.append(
    "- Power BI uses a Date table for time-based calculations."
)
markdown_lines.append("")

markdown_lines.append("## 3. Fact and Dimension Tables")
markdown_lines.append("")
markdown_lines.append(
    "| Table | Table Type | Primary Key | Analytical Purpose |"
)
markdown_lines.append(
    "|---|---|---|---|"
)

for table_name, table_type, primary_key, purpose in tables:
    markdown_lines.append(
        f"| `{table_name}` | {table_type} | "
        f"`{primary_key}` | {purpose} |"
    )

markdown_lines.append("")

markdown_lines.append(
    "## 4. Primary-Key and Foreign-Key Relationships"
)
markdown_lines.append("")
markdown_lines.append(
    "| Parent Key | Child Foreign Key | Relationship |"
)
markdown_lines.append("|---|---|---|")

for (
    parent_table,
    parent_key,
    child_table,
    child_key,
    relationship_type,
) in relationships:

    markdown_lines.append(
        f"| `{parent_table}.{parent_key}` | "
        f"`{child_table}.{child_key}` | "
        f"{relationship_type} |"
    )

markdown_lines.append("")

markdown_lines.append("## 5. Customer Purchase Flow")
markdown_lines.append("")
markdown_lines.append("```text")
markdown_lines.append("Customer Master")
markdown_lines.append("    |")
markdown_lines.append("    | Customer_ID")
markdown_lines.append("    v")
markdown_lines.append("Orders")
markdown_lines.append("    |")
markdown_lines.append("    | Order_ID")
markdown_lines.append("    v")
markdown_lines.append("Order Items")
markdown_lines.append("    |")
markdown_lines.append("    | Product_ID")
markdown_lines.append("    v")
markdown_lines.append("Product Master")
markdown_lines.append("```")
markdown_lines.append("")
markdown_lines.append(
    "This flow supports customer purchases, average order value, "
    "purchase frequency, customer lifetime value and product analysis."
)
markdown_lines.append("")

markdown_lines.append(
    "## 6. Product, Inventory and Warehouse Flow"
)
markdown_lines.append("")
markdown_lines.append("```text")
markdown_lines.append("Product Master")
markdown_lines.append("    |")
markdown_lines.append("    | Product_ID")
markdown_lines.append("    v")
markdown_lines.append("Inventory")
markdown_lines.append("    |")
markdown_lines.append("    | Warehouse_ID")
markdown_lines.append("    v")
markdown_lines.append("Warehouse / Region")
markdown_lines.append("```")
markdown_lines.append("")
markdown_lines.append(
    "This flow supports stock value, stockout rate, excess inventory, "
    "days inventory and inventory turnover."
)
markdown_lines.append("")

markdown_lines.append(
    "## 7. Customer, Marketing and Conversion Flow"
)
markdown_lines.append("")
markdown_lines.append("```text")
markdown_lines.append("Customer Master")
markdown_lines.append("    |")
markdown_lines.append("    | Customer_ID")
markdown_lines.append("    v")
markdown_lines.append("Website Activity")
markdown_lines.append("    |")
markdown_lines.append("    | Channel and Session_ID")
markdown_lines.append("    v")
markdown_lines.append("Marketing Attribution")
markdown_lines.append("    |")
markdown_lines.append("    | Converted Order_ID")
markdown_lines.append("    v")
markdown_lines.append("Orders and Sales")
markdown_lines.append("```")
markdown_lines.append("")
markdown_lines.append(
    "This flow supports first-touch, last-touch and linear attribution."
)
markdown_lines.append("")
markdown_lines.append(
    "`Order_ID` can legitimately be blank for non-converted website "
    "sessions. Therefore, a blank website Order_ID is not automatically "
    "an invalid foreign key."
)
markdown_lines.append("")

markdown_lines.append("## 8. Many-to-Many Relationships")
markdown_lines.append("")

markdown_lines.append("### Orders and Products")
markdown_lines.append("")
markdown_lines.append(
    "An order can contain multiple products and a product can appear "
    "in multiple orders. The order_items bridge resolves this relationship."
)
markdown_lines.append("")
markdown_lines.append("```text")
markdown_lines.append(
    "Orders 1 ---- M Order Items M ---- 1 Product Master"
)
markdown_lines.append("```")
markdown_lines.append("")

markdown_lines.append("### Customers and Marketing Channels")
markdown_lines.append("")
markdown_lines.append(
    "A customer can interact with multiple channels and each channel "
    "can interact with many customers."
)
markdown_lines.append("")
markdown_lines.append("```text")
markdown_lines.append(
    "Customer 1 ---- M Website Activity M ---- 1 Channel"
)
markdown_lines.append("```")
markdown_lines.append("")

markdown_lines.append("### Products and Warehouses")
markdown_lines.append("")
markdown_lines.append(
    "A product can be stored in several warehouses and each warehouse "
    "can store many products."
)
markdown_lines.append("")
markdown_lines.append("```text")
markdown_lines.append(
    "Product 1 ---- M Inventory M ---- 1 Warehouse"
)
markdown_lines.append("```")
markdown_lines.append("")

markdown_lines.append("## 9. Analytical Fact Grain")
markdown_lines.append("")
markdown_lines.append("| Fact Table | Grain |")
markdown_lines.append("|---|---|")
markdown_lines.append("| `orders` | One row per order |")
markdown_lines.append(
    "| `order_items` | One row per order-product line |"
)
markdown_lines.append(
    "| `sales` | One row per sales transaction |"
)
markdown_lines.append(
    "| `returns` | One row per return transaction |"
)
markdown_lines.append(
    "| `invoices` | One row per invoice |"
)
markdown_lines.append(
    "| `payments` | One row per payment transaction |"
)
markdown_lines.append(
    "| `purchases` | One row per supplier purchase |"
)
markdown_lines.append(
    "| `inventory` | One row per product-warehouse-date snapshot |"
)
markdown_lines.append(
    "| `marketing_campaigns` | One row per campaign |"
)
markdown_lines.append(
    "| `website_activity` | One row per website event |"
)
markdown_lines.append(
    "| `customer_complaints` | One row per complaint |"
)
markdown_lines.append(
    "| `employee_attendance` | One row per employee-date |"
)
markdown_lines.append(
    "| `monthly_targets` | One row per region-month |"
)
markdown_lines.append("")

markdown_lines.append("## 10. Order-to-Cash Reconciliation")
markdown_lines.append("")
markdown_lines.append("```text")
markdown_lines.append("Orders")
markdown_lines.append("   |")
markdown_lines.append("   v")
markdown_lines.append("Sales")
markdown_lines.append("   |")
markdown_lines.append("   v")
markdown_lines.append("Returns")
markdown_lines.append("   |")
markdown_lines.append("   v")
markdown_lines.append("Invoices")
markdown_lines.append("   |")
markdown_lines.append("   v")
markdown_lines.append("Payments")
markdown_lines.append("```")
markdown_lines.append("")
markdown_lines.append(
    "This flow supports revenue reconciliation, collections, refunds, "
    "outstanding payments and unmatched-transaction analysis."
)
markdown_lines.append("")

markdown_lines.append("## 11. Relationship Direction")
markdown_lines.append("")
markdown_lines.append(
    "Power BI uses single-direction filtering from dimensions to facts "
    "wherever possible."
)
markdown_lines.append("")
markdown_lines.append(
    "- Customer Master filters Orders, Sales and Website Activity."
)
markdown_lines.append(
    "- Product Master filters Order Items, Sales, Returns and Inventory."
)
markdown_lines.append(
    "- Region Master filters Customers, Employees, Orders and Targets."
)
markdown_lines.append(
    "- Supplier Master filters Products and Purchases."
)
markdown_lines.append(
    "- Date Table filters facts using the relevant transaction date."
)
markdown_lines.append(
    "- Direct bidirectional fact-to-fact relationships are avoided."
)
markdown_lines.append("")

markdown_lines.append("## 12. Data Model Controls")
markdown_lines.append("")
markdown_lines.append(
    "- Primary keys must be unique and not null."
)
markdown_lines.append(
    "- Required foreign keys must match a valid parent record."
)
markdown_lines.append(
    "- Optional foreign keys may be blank for valid business reasons."
)
markdown_lines.append(
    "- Invalid and unmatched records are recorded in Data Quality reports."
)
markdown_lines.append(
    "- Negative inventory is retained as a data-quality exception."
)
markdown_lines.append(
    "- Transaction dates are validated before analytical use."
)
markdown_lines.append(
    "- Ambiguous active Power BI relationship paths are avoided."
)
markdown_lines.append("")

markdown_lines.append("## 13. Model Conclusion")
markdown_lines.append("")
markdown_lines.append(
    "The model supports customer, product, revenue, profitability, "
    "marketing, inventory, supplier, employee and finance analysis "
    "while maintaining traceable relationships from dimensions to facts."
)
markdown_lines.append("")

MARKDOWN_FILE.write_text(
    "\n".join(markdown_lines),
    encoding="utf-8",
)

# ============================================================
# CREATE ER DIAGRAM
# ============================================================

diagram_tables = {
    "REGION": {
        "position": (0.5, 8.0),
        "colour": "#D6EAF8",
        "text": "region_master\nPK: Region_ID\nWarehouse_ID",
    },
    "CUSTOMER": {
        "position": (3.3, 8.0),
        "colour": "#D6EAF8",
        "text": (
            "customer_master\nPK: Customer_ID\nFK: Region_ID"
        ),
    },
    "EMPLOYEE": {
        "position": (6.1, 8.0),
        "colour": "#D6EAF8",
        "text": (
            "employee_master\nPK: Employee_ID\nFK: Region_ID"
        ),
    },
    "SUPPLIER": {
        "position": (8.9, 8.0),
        "colour": "#D6EAF8",
        "text": "suppliers\nPK: Supplier_ID",
    },
    "PRODUCT": {
        "position": (11.7, 8.0),
        "colour": "#D6EAF8",
        "text": (
            "product_master\nPK: Product_ID\nFK: Supplier_ID"
        ),
    },
    "WEBSITE": {
        "position": (0.5, 5.2),
        "colour": "#E8DAEF",
        "text": (
            "website_activity\nPK: Event_ID\nFK: Customer_ID\n"
            "FK: Order_ID optional"
        ),
    },
    "ORDERS": {
        "position": (3.3, 5.2),
        "colour": "#FCF3CF",
        "text": (
            "orders\nPK: Order_ID\nFK: Customer_ID\n"
            "FK: Region_ID\nFK: Employee_ID"
        ),
    },
    "ORDER_ITEMS": {
        "position": (6.1, 5.2),
        "colour": "#FADBD8",
        "text": (
            "order_items\nPK: Order_Item_ID\nFK: Order_ID\n"
            "FK: Product_ID"
        ),
    },
    "SALES": {
        "position": (8.9, 5.2),
        "colour": "#FCF3CF",
        "text": (
            "sales\nPK: Sale_ID\nFK: Order_ID\nFK: Product_ID"
        ),
    },
    "RETURNS": {
        "position": (11.7, 5.2),
        "colour": "#FCF3CF",
        "text": (
            "returns\nPK: Return_ID\nFK: Order_Item_ID\n"
            "FK: Product_ID"
        ),
    },
    "INVOICES": {
        "position": (0.5, 2.4),
        "colour": "#FCF3CF",
        "text": (
            "invoices\nPK: Invoice_ID\nFK: Order_ID\n"
            "FK: Customer_ID"
        ),
    },
    "PAYMENTS": {
        "position": (3.3, 2.4),
        "colour": "#FCF3CF",
        "text": (
            "payments\nPK: Payment_ID\nFK: Invoice_ID"
        ),
    },
    "PURCHASES": {
        "position": (6.1, 2.4),
        "colour": "#FCF3CF",
        "text": (
            "purchases\nPK: Purchase_ID\nFK: Supplier_ID\n"
            "FK: Product_ID"
        ),
    },
    "INVENTORY": {
        "position": (8.9, 2.4),
        "colour": "#FCF3CF",
        "text": (
            "inventory\nPK: Inventory_ID\nFK: Product_ID\n"
            "FK: Warehouse_ID"
        ),
    },
    "TARGETS": {
        "position": (11.7, 2.4),
        "colour": "#FCF3CF",
        "text": (
            "monthly_targets\nPK: Target_ID\nFK: Region_ID"
        ),
    },
}

box_width = 2.1
box_height = 1.4

figure, axis = plt.subplots(figsize=(18, 12))

axis.set_xlim(0, 14.5)
axis.set_ylim(0.4, 10.5)
axis.axis("off")

axis.set_title(
    "Enterprise Business Intelligence - Analytical Data Model",
    fontsize=20,
    fontweight="bold",
    color="#17365D",
    pad=20,
)

centres = {}

for table_label, table_details in diagram_tables.items():
    x_position, y_position = table_details["position"]

    box = FancyBboxPatch(
        (x_position, y_position),
        box_width,
        box_height,
        boxstyle="round,pad=0.05,rounding_size=0.08",
        linewidth=1.5,
        edgecolor="#17365D",
        facecolor=table_details["colour"],
    )

    axis.add_patch(box)

    axis.text(
        x_position + box_width / 2,
        y_position + box_height / 2,
        table_details["text"],
        ha="center",
        va="center",
        fontsize=8.5,
    )

    centres[table_label] = (
        x_position + box_width / 2,
        y_position + box_height / 2,
    )


def connect(
    source,
    target,
    label="1:M",
    curve=0.0,
):
    source_x, source_y = centres[source]
    target_x, target_y = centres[target]

    arrow = FancyArrowPatch(
        (source_x, source_y),
        (target_x, target_y),
        arrowstyle="-|>",
        mutation_scale=12,
        linewidth=1.1,
        color="#566573",
        connectionstyle=f"arc3,rad={curve}",
        shrinkA=48,
        shrinkB=48,
    )

    axis.add_patch(arrow)

    middle_x = (source_x + target_x) / 2
    middle_y = (source_y + target_y) / 2

    axis.text(
        middle_x,
        middle_y,
        label,
        fontsize=7,
        color="#1B4F72",
        bbox={
            "facecolor": "white",
            "edgecolor": "none",
            "alpha": 0.8,
        },
    )


connect("REGION", "CUSTOMER")
connect("REGION", "EMPLOYEE")
connect("REGION", "TARGETS", curve=0.3)
connect("CUSTOMER", "ORDERS")
connect("CUSTOMER", "WEBSITE", curve=0.1)
connect("EMPLOYEE", "ORDERS", curve=0.1)
connect("SUPPLIER", "PRODUCT")
connect("SUPPLIER", "PURCHASES", curve=-0.1)
connect("PRODUCT", "ORDER_ITEMS")
connect("PRODUCT", "PURCHASES")
connect("PRODUCT", "INVENTORY")
connect("ORDERS", "ORDER_ITEMS")
connect("ORDERS", "INVOICES", curve=0.15)
connect("WEBSITE", "ORDERS", "Optional", curve=-0.1)
connect("ORDER_ITEMS", "SALES")
connect("ORDER_ITEMS", "RETURNS")
connect("INVOICES", "PAYMENTS")

axis.text(
    0.6,
    0.9,
    "Legend:",
    fontsize=10,
    fontweight="bold",
    color="#17365D",
)

axis.text(
    1.6,
    0.9,
    "Blue = Dimension",
    fontsize=9,
    bbox={
        "facecolor": "#D6EAF8",
        "edgecolor": "#17365D",
    },
)

axis.text(
    3.8,
    0.9,
    "Yellow = Fact",
    fontsize=9,
    bbox={
        "facecolor": "#FCF3CF",
        "edgecolor": "#17365D",
    },
)

axis.text(
    5.7,
    0.9,
    "Pink = Bridge",
    fontsize=9,
    bbox={
        "facecolor": "#FADBD8",
        "edgecolor": "#17365D",
    },
)

axis.text(
    7.6,
    0.9,
    "Purple = Event Fact",
    fontsize=9,
    bbox={
        "facecolor": "#E8DAEF",
        "edgecolor": "#17365D",
    },
)

plt.tight_layout()

plt.savefig(
    PNG_FILE,
    dpi=220,
    bbox_inches="tight",
    facecolor="white",
)

plt.savefig(
    PDF_FILE,
    bbox_inches="tight",
    facecolor="white",
)

plt.close()

# ============================================================
# FINAL OUTPUT
# ============================================================

print("=" * 78)
print("DATA MODEL DOCUMENTATION CREATED SUCCESSFULLY")
print("=" * 78)
print()
print("Markdown documentation:")
print(MARKDOWN_FILE)
print()
print("ER diagram image:")
print(PNG_FILE)
print()
print("ER diagram PDF:")
print(PDF_FILE)