# Enterprise Business Intelligence Data Model

## 1. Model Objective

This analytical model supports revenue, profitability, customer, product, inventory, supplier, marketing, employee and finance analysis for the Enterprise Business Intelligence project.

The model connects all 18 datasets using primary-key and foreign-key relationships.

## 2. Modeling Approach

- Dimension tables contain descriptive business entities.
- Fact tables contain transactions, balances, events and measures.
- Bridge tables resolve many-to-many relationships.
- Inventory is modeled as a product-warehouse-date snapshot fact.
- Power BI uses a Date table for time-based calculations.

## 3. Fact and Dimension Tables

| Table | Table Type | Primary Key | Analytical Purpose |
|---|---|---|---|
| `region_master` | Dimension | `Region_ID` | Region and warehouse details |
| `customer_master` | Dimension | `Customer_ID` | Customer details and regional assignment |
| `product_master` | Dimension | `Product_ID` | Product, category, supplier, price and cost |
| `employee_master` | Dimension | `Employee_ID` | Employee, manager and regional details |
| `suppliers` | Dimension | `Supplier_ID` | Supplier descriptive information |
| `orders` | Fact | `Order_ID` | One row per customer order |
| `order_items` | Bridge / Fact | `Order_Item_ID` | One row per order and product combination |
| `sales` | Fact | `Sale_ID` | One row per sales transaction |
| `returns` | Fact | `Return_ID` | One row per returned order item |
| `invoices` | Fact | `Invoice_ID` | One row per customer invoice |
| `payments` | Fact | `Payment_ID` | One row per payment transaction |
| `purchases` | Fact | `Purchase_ID` | One row per supplier purchase |
| `inventory` | Snapshot Fact | `Inventory_ID` | One row per product, warehouse and snapshot date |
| `marketing_campaigns` | Fact | `Campaign_ID` | One row per marketing campaign |
| `website_activity` | Event Fact | `Event_ID` | One row per website event |
| `customer_complaints` | Fact | `Complaint_ID` | One row per customer complaint |
| `employee_attendance` | Fact | `Attendance_ID` | One row per employee attendance date |
| `monthly_targets` | Fact | `Target_ID` | One row per region and target month |

## 4. Primary-Key and Foreign-Key Relationships

| Parent Key | Child Foreign Key | Relationship |
|---|---|---|
| `region_master.Region_ID` | `customer_master.Region_ID` | One-to-Many |
| `region_master.Region_ID` | `employee_master.Region_ID` | One-to-Many |
| `region_master.Region_ID` | `orders.Region_ID` | One-to-Many |
| `region_master.Region_ID` | `sales.Region_ID` | One-to-Many |
| `region_master.Region_ID` | `monthly_targets.Region_ID` | One-to-Many |
| `customer_master.Customer_ID` | `orders.Customer_ID` | One-to-Many |
| `customer_master.Customer_ID` | `sales.Customer_ID` | One-to-Many |
| `customer_master.Customer_ID` | `returns.Customer_ID` | One-to-Many |
| `customer_master.Customer_ID` | `invoices.Customer_ID` | One-to-Many |
| `customer_master.Customer_ID` | `payments.Customer_ID` | One-to-Many |
| `customer_master.Customer_ID` | `website_activity.Customer_ID` | One-to-Many |
| `customer_master.Customer_ID` | `customer_complaints.Customer_ID` | One-to-Many |
| `employee_master.Employee_ID` | `orders.Sales_Employee_ID` | One-to-Many |
| `employee_master.Employee_ID` | `sales.Employee_ID` | One-to-Many |
| `employee_master.Employee_ID` | `employee_attendance.Employee_ID` | One-to-Many |
| `suppliers.Supplier_ID` | `product_master.Supplier_ID` | One-to-Many |
| `suppliers.Supplier_ID` | `purchases.Supplier_ID` | One-to-Many |
| `orders.Order_ID` | `order_items.Order_ID` | One-to-Many |
| `orders.Order_ID` | `sales.Order_ID` | One-to-Many |
| `orders.Order_ID` | `returns.Order_ID` | One-to-Many |
| `orders.Order_ID` | `invoices.Order_ID` | One-to-Many |
| `orders.Order_ID` | `website_activity.Order_ID` | One-to-Many Optional |
| `orders.Order_ID` | `customer_complaints.Order_ID` | One-to-Many |
| `order_items.Order_Item_ID` | `sales.Order_Item_ID` | One-to-Many |
| `order_items.Order_Item_ID` | `returns.Order_Item_ID` | One-to-Many |
| `product_master.Product_ID` | `order_items.Product_ID` | One-to-Many |
| `product_master.Product_ID` | `sales.Product_ID` | One-to-Many |
| `product_master.Product_ID` | `returns.Product_ID` | One-to-Many |
| `product_master.Product_ID` | `purchases.Product_ID` | One-to-Many |
| `product_master.Product_ID` | `inventory.Product_ID` | One-to-Many |
| `invoices.Invoice_ID` | `payments.Invoice_ID` | One-to-Many |

## 5. Customer Purchase Flow

```text
Customer Master
    |
    | Customer_ID
    v
Orders
    |
    | Order_ID
    v
Order Items
    |
    | Product_ID
    v
Product Master
```

This flow supports customer purchases, average order value, purchase frequency, customer lifetime value and product analysis.

## 6. Product, Inventory and Warehouse Flow

```text
Product Master
    |
    | Product_ID
    v
Inventory
    |
    | Warehouse_ID
    v
Warehouse / Region
```

This flow supports stock value, stockout rate, excess inventory, days inventory and inventory turnover.

## 7. Customer, Marketing and Conversion Flow

```text
Customer Master
    |
    | Customer_ID
    v
Website Activity
    |
    | Channel and Session_ID
    v
Marketing Attribution
    |
    | Converted Order_ID
    v
Orders and Sales
```

This flow supports first-touch, last-touch and linear attribution.

`Order_ID` can legitimately be blank for non-converted website sessions. Therefore, a blank website Order_ID is not automatically an invalid foreign key.

## 8. Many-to-Many Relationships

### Orders and Products

An order can contain multiple products and a product can appear in multiple orders. The order_items bridge resolves this relationship.

```text
Orders 1 ---- M Order Items M ---- 1 Product Master
```

### Customers and Marketing Channels

A customer can interact with multiple channels and each channel can interact with many customers.

```text
Customer 1 ---- M Website Activity M ---- 1 Channel
```

### Products and Warehouses

A product can be stored in several warehouses and each warehouse can store many products.

```text
Product 1 ---- M Inventory M ---- 1 Warehouse
```

## 9. Analytical Fact Grain

| Fact Table | Grain |
|---|---|
| `orders` | One row per order |
| `order_items` | One row per order-product line |
| `sales` | One row per sales transaction |
| `returns` | One row per return transaction |
| `invoices` | One row per invoice |
| `payments` | One row per payment transaction |
| `purchases` | One row per supplier purchase |
| `inventory` | One row per product-warehouse-date snapshot |
| `marketing_campaigns` | One row per campaign |
| `website_activity` | One row per website event |
| `customer_complaints` | One row per complaint |
| `employee_attendance` | One row per employee-date |
| `monthly_targets` | One row per region-month |

## 10. Order-to-Cash Reconciliation

```text
Orders
   |
   v
Sales
   |
   v
Returns
   |
   v
Invoices
   |
   v
Payments
```

This flow supports revenue reconciliation, collections, refunds, outstanding payments and unmatched-transaction analysis.

## 11. Relationship Direction

Power BI uses single-direction filtering from dimensions to facts wherever possible.

- Customer Master filters Orders, Sales and Website Activity.
- Product Master filters Order Items, Sales, Returns and Inventory.
- Region Master filters Customers, Employees, Orders and Targets.
- Supplier Master filters Products and Purchases.
- Date Table filters facts using the relevant transaction date.
- Direct bidirectional fact-to-fact relationships are avoided.

## 12. Data Model Controls

- Primary keys must be unique and not null.
- Required foreign keys must match a valid parent record.
- Optional foreign keys may be blank for valid business reasons.
- Invalid and unmatched records are recorded in Data Quality reports.
- Negative inventory is retained as a data-quality exception.
- Transaction dates are validated before analytical use.
- Ambiguous active Power BI relationship paths are avoided.

## 13. Model Conclusion

The model supports customer, product, revenue, profitability, marketing, inventory, supplier, employee and finance analysis while maintaining traceable relationships from dimensions to facts.
