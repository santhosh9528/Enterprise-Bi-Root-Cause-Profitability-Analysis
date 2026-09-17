USE enterprise_bi;

LOAD DATA LOCAL INFILE
'C:/Users/Hooooo/Documents/Excel/Enterprise_BI_Root_Cause_Profitability_Dataset/Final_Data_Analyst_Project/Cleaned_Data/region_master.csv'
INTO TABLE region_master
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE
'C:/Users/Hooooo/Documents/Excel/Enterprise_BI_Root_Cause_Profitability_Dataset/Final_Data_Analyst_Project/Cleaned_Data/customer_master.csv'
INTO TABLE customer_master
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE
'C:/Users/Hooooo/Documents/Excel/Enterprise_BI_Root_Cause_Profitability_Dataset/Final_Data_Analyst_Project/Cleaned_Data/employee_master.csv'
INTO TABLE employee_master
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE
'C:/Users/Hooooo/Documents/Excel/Enterprise_BI_Root_Cause_Profitability_Dataset/Final_Data_Analyst_Project/Cleaned_Data/suppliers.csv'
INTO TABLE suppliers
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE
'C:/Users/Hooooo/Documents/Excel/Enterprise_BI_Root_Cause_Profitability_Dataset/Final_Data_Analyst_Project/Cleaned_Data/product_master.csv'
INTO TABLE product_master
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE
'C:/Users/Hooooo/Documents/Excel/Enterprise_BI_Root_Cause_Profitability_Dataset/Final_Data_Analyst_Project/Cleaned_Data/orders.csv'
INTO TABLE orders
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE
'C:/Users/Hooooo/Documents/Excel/Enterprise_BI_Root_Cause_Profitability_Dataset/Final_Data_Analyst_Project/Cleaned_Data/order_items.csv'
INTO TABLE order_items
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE
'C:/Users/Hooooo/Documents/Excel/Enterprise_BI_Root_Cause_Profitability_Dataset/Final_Data_Analyst_Project/Cleaned_Data/sales.csv'
INTO TABLE sales
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE
'C:/Users/Hooooo/Documents/Excel/Enterprise_BI_Root_Cause_Profitability_Dataset/Final_Data_Analyst_Project/Cleaned_Data/returns.csv'
INTO TABLE returns
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE
'C:/Users/Hooooo/Documents/Excel/Enterprise_BI_Root_Cause_Profitability_Dataset/Final_Data_Analyst_Project/Cleaned_Data/invoices.csv'
INTO TABLE invoices
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE
'C:/Users/Hooooo/Documents/Excel/Enterprise_BI_Root_Cause_Profitability_Dataset/Final_Data_Analyst_Project/Cleaned_Data/payments.csv'
INTO TABLE payments
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE
'C:/Users/Hooooo/Documents/Excel/Enterprise_BI_Root_Cause_Profitability_Dataset/Final_Data_Analyst_Project/Cleaned_Data/purchases.csv'
INTO TABLE purchases
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE
'C:/Users/Hooooo/Documents/Excel/Enterprise_BI_Root_Cause_Profitability_Dataset/Final_Data_Analyst_Project/Cleaned_Data/inventory.csv'
INTO TABLE inventory
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE
'C:/Users/Hooooo/Documents/Excel/Enterprise_BI_Root_Cause_Profitability_Dataset/Final_Data_Analyst_Project/Cleaned_Data/marketing_campaigns.csv'
INTO TABLE marketing_campaigns
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE
'C:/Users/Hooooo/Documents/Excel/Enterprise_BI_Root_Cause_Profitability_Dataset/Final_Data_Analyst_Project/Cleaned_Data/website_activity.csv'
INTO TABLE website_activity
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE
'C:/Users/Hooooo/Documents/Excel/Enterprise_BI_Root_Cause_Profitability_Dataset/Final_Data_Analyst_Project/Cleaned_Data/customer_complaints.csv'
INTO TABLE customer_complaints
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE
'C:/Users/Hooooo/Documents/Excel/Enterprise_BI_Root_Cause_Profitability_Dataset/Final_Data_Analyst_Project/Cleaned_Data/employee_attendance.csv'
INTO TABLE employee_attendance
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE
'C:/Users/Hooooo/Documents/Excel/Enterprise_BI_Root_Cause_Profitability_Dataset/Final_Data_Analyst_Project/Cleaned_Data/monthly_targets.csv'
INTO TABLE monthly_targets
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;