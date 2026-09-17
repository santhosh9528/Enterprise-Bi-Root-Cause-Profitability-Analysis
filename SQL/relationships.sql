USE enterprise_bi;

-- Master table relationships
ALTER TABLE customer_master
ADD CONSTRAINT fk_customer_region
FOREIGN KEY (Region_ID)
REFERENCES region_master(Region_ID);

ALTER TABLE employee_master
ADD CONSTRAINT fk_employee_region
FOREIGN KEY (Region_ID)
REFERENCES region_master(Region_ID);

ALTER TABLE product_master
ADD CONSTRAINT fk_product_supplier
FOREIGN KEY (Supplier_ID)
REFERENCES suppliers(Supplier_ID);

-- Order relationships
ALTER TABLE orders
ADD CONSTRAINT fk_orders_customer
FOREIGN KEY (Customer_ID)
REFERENCES customer_master(Customer_ID),

ADD CONSTRAINT fk_orders_region
FOREIGN KEY (Region_ID)
REFERENCES region_master(Region_ID),

ADD CONSTRAINT fk_orders_employee
FOREIGN KEY (Sales_Employee_ID)
REFERENCES employee_master(Employee_ID);

-- Order-item relationships
ALTER TABLE order_items
ADD CONSTRAINT fk_order_items_order
FOREIGN KEY (Order_ID)
REFERENCES orders(Order_ID),

ADD CONSTRAINT fk_order_items_product
FOREIGN KEY (Product_ID)
REFERENCES product_master(Product_ID);

-- Sales relationships
ALTER TABLE sales
ADD CONSTRAINT fk_sales_order
FOREIGN KEY (Order_ID)
REFERENCES orders(Order_ID),

ADD CONSTRAINT fk_sales_order_item
FOREIGN KEY (Order_Item_ID)
REFERENCES order_items(Order_Item_ID),

ADD CONSTRAINT fk_sales_customer
FOREIGN KEY (Customer_ID)
REFERENCES customer_master(Customer_ID),

ADD CONSTRAINT fk_sales_product
FOREIGN KEY (Product_ID)
REFERENCES product_master(Product_ID),

ADD CONSTRAINT fk_sales_employee
FOREIGN KEY (Employee_ID)
REFERENCES employee_master(Employee_ID),

ADD CONSTRAINT fk_sales_region
FOREIGN KEY (Region_ID)
REFERENCES region_master(Region_ID);

-- Invoice relationships
ALTER TABLE invoices
ADD CONSTRAINT fk_invoices_order
FOREIGN KEY (Order_ID)
REFERENCES orders(Order_ID),

ADD CONSTRAINT fk_invoices_customer
FOREIGN KEY (Customer_ID)
REFERENCES customer_master(Customer_ID);

-- Payment relationships
ALTER TABLE payments
ADD CONSTRAINT fk_payments_invoice
FOREIGN KEY (Invoice_ID)
REFERENCES invoices(Invoice_ID),

ADD CONSTRAINT fk_payments_customer
FOREIGN KEY (Customer_ID)
REFERENCES customer_master(Customer_ID);


--------------------------------------------------------------

USE enterprise_bi;

-- Optional blank foreign keys-ai NULL-ah standardize pannuvom
SET SQL_SAFE_UPDATES = 0;

UPDATE website_activity
SET Customer_ID = NULL
WHERE Customer_ID = '';

UPDATE website_activity
SET Order_ID = NULL
WHERE Order_ID = '';

UPDATE employee_master
SET Manager_ID = NULL
WHERE Manager_ID = '';

SET SQL_SAFE_UPDATES = 1;

-- Employee self relationship
ALTER TABLE employee_master
ADD CONSTRAINT fk_employee_manager
FOREIGN KEY (Manager_ID)
REFERENCES employee_master(Employee_ID);

-- Supplier relationship
ALTER TABLE suppliers
ADD CONSTRAINT fk_supplier_region
FOREIGN KEY (Region_ID)
REFERENCES region_master(Region_ID);

-- Returns relationships
ALTER TABLE returns
ADD CONSTRAINT fk_returns_order
FOREIGN KEY (Order_ID)
REFERENCES orders(Order_ID),

ADD CONSTRAINT fk_returns_order_item
FOREIGN KEY (Order_Item_ID)
REFERENCES order_items(Order_Item_ID),

ADD CONSTRAINT fk_returns_customer
FOREIGN KEY (Customer_ID)
REFERENCES customer_master(Customer_ID),

ADD CONSTRAINT fk_returns_product
FOREIGN KEY (Product_ID)
REFERENCES product_master(Product_ID);

-- Purchase relationships
ALTER TABLE purchases
ADD CONSTRAINT fk_purchases_supplier
FOREIGN KEY (Supplier_ID)
REFERENCES suppliers(Supplier_ID),

ADD CONSTRAINT fk_purchases_product
FOREIGN KEY (Product_ID)
REFERENCES product_master(Product_ID),

ADD CONSTRAINT fk_purchases_warehouse
FOREIGN KEY (Warehouse_ID)
REFERENCES region_master(Warehouse_ID);

-- Inventory relationships
ALTER TABLE inventory
ADD CONSTRAINT fk_inventory_product
FOREIGN KEY (Product_ID)
REFERENCES product_master(Product_ID),

ADD CONSTRAINT fk_inventory_warehouse
FOREIGN KEY (Warehouse_ID)
REFERENCES region_master(Warehouse_ID);

-- Website relationships
ALTER TABLE website_activity
ADD CONSTRAINT fk_website_customer
FOREIGN KEY (Customer_ID)
REFERENCES customer_master(Customer_ID),

ADD CONSTRAINT fk_website_order
FOREIGN KEY (Order_ID)
REFERENCES orders(Order_ID);

-- Complaint relationships
ALTER TABLE customer_complaints
ADD CONSTRAINT fk_complaints_customer
FOREIGN KEY (Customer_ID)
REFERENCES customer_master(Customer_ID),

ADD CONSTRAINT fk_complaints_order
FOREIGN KEY (Order_ID)
REFERENCES orders(Order_ID);

-- Attendance relationship
ALTER TABLE employee_attendance
ADD CONSTRAINT fk_attendance_employee
FOREIGN KEY (Employee_ID)
REFERENCES employee_master(Employee_ID);

-- Monthly target relationship
ALTER TABLE monthly_targets
ADD CONSTRAINT fk_targets_region
FOREIGN KEY (Region_ID)
REFERENCES region_master(Region_ID);