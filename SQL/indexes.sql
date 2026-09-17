USE enterprise_bi;

-- Customer and Product indexes
CREATE INDEX idx_customer_region
ON customer_master(Region_ID);

CREATE INDEX idx_product_supplier
ON product_master(Supplier_ID);

CREATE INDEX idx_product_category
ON product_master(Category);

CREATE INDEX idx_employee_region
ON employee_master(Region_ID);

CREATE INDEX idx_supplier_region
ON suppliers(Region_ID);

-- Order indexes
CREATE INDEX idx_orders_customer
ON orders(Customer_ID);

CREATE INDEX idx_orders_date
ON orders(Order_Date);

CREATE INDEX idx_orders_region
ON orders(Region_ID);

CREATE INDEX idx_orders_employee
ON orders(Sales_Employee_ID);

CREATE INDEX idx_order_items_order
ON order_items(Order_ID);

CREATE INDEX idx_order_items_product
ON order_items(Product_ID);

-- Sales indexes
CREATE INDEX idx_sales_order
ON sales(Order_ID);

CREATE INDEX idx_sales_order_item
ON sales(Order_Item_ID);

CREATE INDEX idx_sales_date
ON sales(Sale_Date);

CREATE INDEX idx_sales_customer
ON sales(Customer_ID);

CREATE INDEX idx_sales_product
ON sales(Product_ID);

CREATE INDEX idx_sales_employee
ON sales(Employee_ID);

CREATE INDEX idx_sales_region
ON sales(Region_ID);

-- Return indexes
CREATE INDEX idx_returns_order
ON returns(Order_ID);

CREATE INDEX idx_returns_product
ON returns(Product_ID);

CREATE INDEX idx_returns_customer
ON returns(Customer_ID);

CREATE INDEX idx_returns_date
ON returns(Return_Date);

-- Invoice and Payment indexes
CREATE INDEX idx_invoices_order
ON invoices(Order_ID);

CREATE INDEX idx_invoices_customer
ON invoices(Customer_ID);

CREATE INDEX idx_invoices_date
ON invoices(Invoice_Date);

CREATE INDEX idx_payments_invoice
ON payments(Invoice_ID);

CREATE INDEX idx_payments_customer
ON payments(Customer_ID);

CREATE INDEX idx_payments_date
ON payments(Payment_Date);

-- Inventory and Purchase indexes
CREATE INDEX idx_inventory_product
ON inventory(Product_ID);

CREATE INDEX idx_inventory_warehouse
ON inventory(Warehouse_ID);

CREATE INDEX idx_inventory_date
ON inventory(Snapshot_Date);

CREATE INDEX idx_purchases_supplier
ON purchases(Supplier_ID);

CREATE INDEX idx_purchases_product
ON purchases(Product_ID);

CREATE INDEX idx_purchases_warehouse
ON purchases(Warehouse_ID);

-- Marketing and Website indexes
CREATE INDEX idx_marketing_channel
ON marketing_campaigns(Channel);

CREATE INDEX idx_marketing_date
ON marketing_campaigns(Campaign_Date);

CREATE INDEX idx_website_customer
ON website_activity(Customer_ID);

CREATE INDEX idx_website_order
ON website_activity(Order_ID);

CREATE INDEX idx_website_session
ON website_activity(Session_ID);

CREATE INDEX idx_website_event_time
ON website_activity(Event_Time);

-- Other operational indexes
CREATE INDEX idx_complaints_customer
ON customer_complaints(Customer_ID);

CREATE INDEX idx_complaints_order
ON customer_complaints(Order_ID);

CREATE INDEX idx_attendance_employee
ON employee_attendance(Employee_ID);

CREATE INDEX idx_attendance_date
ON employee_attendance(Attendance_Date);

CREATE INDEX idx_targets_region_month
ON monthly_targets(Region_ID, Month);