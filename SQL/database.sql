USE enterprise_bi;

-- 1. REGION MASTER
CREATE TABLE IF NOT EXISTS region_master (
    Region_ID VARCHAR(10) PRIMARY KEY,
    Region_Name VARCHAR(50),
    State VARCHAR(100),
    Country VARCHAR(50),
    Warehouse_ID VARCHAR(10) UNIQUE,
    Regional_Manager VARCHAR(100)
);

-- 2. CUSTOMER MASTER
CREATE TABLE IF NOT EXISTS customer_master (
    Customer_ID VARCHAR(20) PRIMARY KEY,
    Customer_Name VARCHAR(100),
    Email VARCHAR(150),
    Phone VARCHAR(20),
    Join_Date DATE,
    City VARCHAR(100),
    State VARCHAR(100),
    Region_ID VARCHAR(10),
    Customer_Type VARCHAR(50),
    Credit_Limit DECIMAL(15,2),
    Status VARCHAR(30)
);

-- 3. EMPLOYEE MASTER
CREATE TABLE IF NOT EXISTS employee_master (
    Employee_ID VARCHAR(20) PRIMARY KEY,
    Employee_Name VARCHAR(100),
    Department VARCHAR(100),
    Manager_ID VARCHAR(20),
    Region_ID VARCHAR(10),
    Hire_Date DATE,
    Monthly_Salary DECIMAL(15,2),
    Status VARCHAR(30)
);

-- 4. SUPPLIERS
CREATE TABLE IF NOT EXISTS suppliers (
    Supplier_ID VARCHAR(20) PRIMARY KEY,
    Supplier_Name VARCHAR(150),
    Category VARCHAR(100),
    Region_ID VARCHAR(10),
    Contract_Start DATE,
    Standard_Lead_Days INT,
    Quality_Target DECIMAL(10,2),
    Status VARCHAR(30)
);

-- 5. PRODUCT MASTER
CREATE TABLE IF NOT EXISTS product_master (
    Product_ID VARCHAR(20) PRIMARY KEY,
    Product_Name VARCHAR(150),
    Category VARCHAR(100),
    Subcategory VARCHAR(100),
    Supplier_ID VARCHAR(20),
    List_Price DECIMAL(15,2),
    Standard_Cost DECIMAL(15,2),
    Launch_Date DATE,
    Lead_Time_Days INT,
    Status VARCHAR(30)
);

-- 6. ORDERS
CREATE TABLE IF NOT EXISTS orders (
    Order_ID VARCHAR(20) PRIMARY KEY,
    Customer_ID VARCHAR(20),
    Order_Date DATE,
    Region_ID VARCHAR(10),
    Sales_Employee_ID VARCHAR(20),
    Channel VARCHAR(50),
    Order_Status VARCHAR(30),
    Management_Order_Value DECIMAL(18,2)
);

-- 7. ORDER ITEMS
CREATE TABLE IF NOT EXISTS order_items (
    Order_Item_ID VARCHAR(20) PRIMARY KEY,
    Order_ID VARCHAR(20),
    Product_ID VARCHAR(20),
    Quantity INT,
    Unit_Price DECIMAL(15,2),
    Discount_Pct DECIMAL(10,4),
    Gross_Amount DECIMAL(18,2),
    Net_Amount DECIMAL(18,2)
);

-- 8. SALES
CREATE TABLE IF NOT EXISTS sales (
    Sale_ID VARCHAR(20) PRIMARY KEY,
    Order_ID VARCHAR(20),
    Order_Item_ID VARCHAR(20),
    Sale_Date DATE,
    Customer_ID VARCHAR(20),
    Product_ID VARCHAR(20),
    Employee_ID VARCHAR(20),
    Region_ID VARCHAR(10),
    Quantity INT,
    Gross_Sales DECIMAL(18,2),
    Discount DECIMAL(18,2),
    Net_Sales DECIMAL(18,2),
    Product_Cost DECIMAL(18,2),
    Shipping_Cost DECIMAL(18,2),
    Payment_Fee DECIMAL(18,2)
);

-- 9. RETURNS
CREATE TABLE IF NOT EXISTS returns (
    Return_ID VARCHAR(20) PRIMARY KEY,
    Order_ID VARCHAR(20),
    Order_Item_ID VARCHAR(20),
    Customer_ID VARCHAR(20),
    Product_ID VARCHAR(20),
    Return_Date DATE,
    Return_Quantity INT,
    Refund_Amount DECIMAL(18,2),
    Reason VARCHAR(100),
    Status VARCHAR(30)
);

-- 10. INVOICES
CREATE TABLE IF NOT EXISTS invoices (
    Invoice_ID VARCHAR(20) PRIMARY KEY,
    Order_ID VARCHAR(20),
    Customer_ID VARCHAR(20),
    Invoice_Date DATE,
    Due_Date DATE,
    Invoice_Amount DECIMAL(18,2),
    Tax_Amount DECIMAL(18,2),
    Invoice_Status VARCHAR(30)
);

-- 11. PAYMENTS
CREATE TABLE IF NOT EXISTS payments (
    Payment_ID VARCHAR(20) PRIMARY KEY,
    Invoice_ID VARCHAR(20),
    Customer_ID VARCHAR(20),
    Payment_Date DATE,
    Payment_Method VARCHAR(50),
    Payment_Amount DECIMAL(18,2),
    Payment_Fee DECIMAL(18,2),
    Payment_Status VARCHAR(30)
);

-- 12. PURCHASES
CREATE TABLE IF NOT EXISTS purchases (
    Purchase_ID VARCHAR(20) PRIMARY KEY,
    Supplier_ID VARCHAR(20),
    Product_ID VARCHAR(20),
    Warehouse_ID VARCHAR(10),
    Purchase_Date DATE,
    Quantity INT,
    Unit_Cost DECIMAL(18,2),
    Expected_Date DATE,
    Delivery_Date DATE,
    Rejected_Quantity INT
);

-- 13. INVENTORY
CREATE TABLE IF NOT EXISTS inventory (
    Inventory_ID VARCHAR(20) PRIMARY KEY,
    Snapshot_Date DATE,
    Warehouse_ID VARCHAR(10),
    Product_ID VARCHAR(20),
    Opening_Stock INT,
    Purchases INT,
    Units_Sold INT,
    Returns_In INT,
    Adjustments INT,
    Closing_Stock INT,
    Unit_Cost DECIMAL(18,2),
    Stock_Value DECIMAL(18,2),
    Stockout_Flag TINYINT
);

-- 14. MARKETING CAMPAIGNS
CREATE TABLE IF NOT EXISTS marketing_campaigns (
    Campaign_ID VARCHAR(20) PRIMARY KEY,
    Campaign_Date DATE,
    Channel VARCHAR(50),
    Campaign_Name VARCHAR(150),
    Spend DECIMAL(18,2),
    Impressions BIGINT,
    Clicks BIGINT,
    Leads BIGINT,
    Conversions BIGINT,
    Attributed_Revenue DECIMAL(18,2),
    Attributed_Profit DECIMAL(18,2)
);

-- 15. WEBSITE ACTIVITY
CREATE TABLE IF NOT EXISTS website_activity (
    Event_ID VARCHAR(20) PRIMARY KEY,
    Customer_ID VARCHAR(20),
    Session_ID VARCHAR(30),
    Event_Time DATETIME,
    Channel VARCHAR(50),
    Event_Type VARCHAR(50),
    Page VARCHAR(100),
    Experiment_Group VARCHAR(30),
    Converted TINYINT,
    Order_ID VARCHAR(20)
);

-- 16. CUSTOMER COMPLAINTS
CREATE TABLE IF NOT EXISTS customer_complaints (
    Complaint_ID VARCHAR(20) PRIMARY KEY,
    Customer_ID VARCHAR(20),
    Order_ID VARCHAR(20),
    Complaint_Date DATE,
    Category VARCHAR(100),
    Severity VARCHAR(30),
    Resolution_Date DATE,
    Resolution_Status VARCHAR(30),
    Satisfaction_Score DECIMAL(5,2)
);

-- 17. EMPLOYEE ATTENDANCE
CREATE TABLE IF NOT EXISTS employee_attendance (
    Attendance_ID VARCHAR(20) PRIMARY KEY,
    Employee_ID VARCHAR(20),
    Attendance_Date DATE,
    Shift VARCHAR(30),
    Scheduled_Hours DECIMAL(10,2),
    Worked_Hours DECIMAL(10,2),
    Overtime_Hours DECIMAL(10,2),
    Status VARCHAR(30)
);

-- 18. MONTHLY TARGETS
CREATE TABLE IF NOT EXISTS monthly_targets (
    Target_ID VARCHAR(20) PRIMARY KEY,
    Month DATE,
    Region_ID VARCHAR(10),
    Department VARCHAR(100),
    Revenue_Target DECIMAL(18,2),
    Profit_Target DECIMAL(18,2),
    Orders_Target INT,
    Collection_Target DECIMAL(18,2),
    Inventory_Target DECIMAL(18,2),
    Management_Reported_Revenue DECIMAL(18,2)
);