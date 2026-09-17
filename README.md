# Enterprise BI – Root Cause & Profitability Analysis

An end-to-end Business Intelligence project developed to investigate profitability, revenue reconciliation, customer retention, product performance, marketing effectiveness, inventory risk, supplier performance, forecasting, and critical business exceptions.

The solution combines **MySQL, Python, Jupyter Notebook, statistical analysis, machine learning, and Power BI** to convert 18 enterprise datasets into management-ready insights.

---

## Project Objectives

This project answers the following key business questions:

- Why is revenue increasing while profit remains negative?
- Why do management revenue and database revenue not reconcile?
- Which products, customers, regions, and marketing channels generate real profit?
- Is customer retention improving or declining?
- Which products face stockout, excess inventory, or dead-stock risks?
- Which suppliers require renegotiation or critical review?
- Is the new checkout experience statistically better?
- Will the company achieve its next-quarter targets?
- Which business exceptions require immediate management action?

---

## Executive Findings

| Business Metric | Finding |
|---|---:|
| Database Revenue | ₹48.43 Cr |
| Net Profit | **₹3.25 Cr Loss** |
| Profit Margin | **-6.70%** |
| Management Revenue | ₹52.00 Cr |
| Revenue Reconciliation Difference | ₹3.90 Cr |
| Negative-Profit Products | 990 |
| Excess Inventory Value | ₹79.77 Cr |
| Inventory Turnover | 0.12 times |
| Days Inventory | 2,966.72 days |
| Negative Inventory Products | 120 |
| Supplier On-Time Delivery | 11.22% |
| Overdue Receivables Above 180 Days | ₹4.52 Cr |
| Next-Quarter Revenue Forecast | ₹12.31 Cr |
| Forecast Target Achievement | 98.15% |
| A/B Test P-Value | 0.7645 |
| A/B Test Decision | Continue Testing |

---

## Five Largest Business Problems

### 1. Revenue Generated but Company Remains Unprofitable

The company generated approximately **₹48.43 Cr in revenue**, but recorded a **₹3.25 Cr net loss**.

Major contributors include:

- High product cost
- Marketing expenditure
- Shipping cost
- Payment-processing fees
- Discounts and refunds
- Loss-making products and customers

**Recommended action:** Correct loss-making prices, reduce inefficient marketing expenditure, renegotiate product costs, and control discounting.

### 2. Excess Inventory and Extremely Low Turnover

The business holds approximately **₹79.77 Cr of excess inventory**, while inventory turnover is only **0.12 times**.

**Recommended action:** Stop purchasing dead-stock products, liquidate excess inventory, and introduce demand-based reorder points.

### 3. Poor Supplier Delivery Performance

Overall supplier on-time delivery is approximately **11.22%**.

**Recommended action:** Renegotiate supplier SLAs, introduce late-delivery penalties, and shift critical purchasing volume to better-performing suppliers.

### 4. Revenue Reports Do Not Reconcile

Management revenue and database revenue differ by approximately **₹3.90 Cr**.

**Recommended action:** Establish a governed revenue definition and automate reconciliation across orders, sales, returns, invoices, and payments.

### 5. Long-Overdue Customer Receivables

Invoices overdue by more than 180 days represent approximately **₹4.52 Cr**.

**Recommended action:** Implement ageing-based collection workflows, review customer credit limits, and escalate high-value overdue invoices.

---

## Power BI Executive Dashboard

The Power BI report contains seven management pages.

### Page 1 – Executive Overview

![Executive Overview](PowerBI/Dashboards%20Screenshot/Executive%20Overview.png)

Displays company-level KPIs including revenue, profit, margin, growth, orders, customers, retention, returns, collections, and inventory value.

### Page 2 – Revenue & Profit

![Revenue and Profit](PowerBI/Dashboards%20Screenshot/Revenue%20%26%20Profit.png)

Provides monthly revenue and profit trends, category performance, regional profitability, margin analysis, and revenue reconciliation.

### Page 3 – Customer Analytics

![Customer Analytics](PowerBI/Dashboards%20Screenshot/Customer%20Analytics.png)

Includes customer segments, retention, churn, cohort performance, customer lifetime value, and high-revenue/low-profit customer identification.

### Page 4 – Product Analytics

![Product Analytics](PowerBI/Dashboards%20Screenshot/Product%20Analysis.png)

Shows product revenue, profit, margin, returns, inventory, turnover, ranking, and product classifications.

### Page 5 – Marketing Analytics

![Marketing Analytics](PowerBI/Dashboards%20Screenshot/Marketing%20Analytics.png)

Analyzes marketing spend, leads, conversions, CAC, attributed revenue, attributed profit, ROI, and channel performance.

### Page 6 – Operations

![Operations](PowerBI/Dashboards%20Screenshot/Operations.png)

Covers inventory status, stockout risk, excess inventory, supplier delivery, supplier quality, and supplier performance.

### Page 7 – Executive Exception

![Executive Exception](PowerBI/Dashboards%20Screenshot/Executive%20Exception.png)

Displays only critical management issues, including anomalies, reconciliation differences, negative inventory, critical products, and critical suppliers.

---

## Data Sources

The analysis uses the following 18 datasets:

1. Customer Master
2. Product Master
3. Employee Master
4. Region Master
5. Orders
6. Order Items
7. Sales
8. Returns
9. Payments
10. Invoices
11. Purchases
12. Inventory
13. Suppliers
14. Marketing Campaigns
15. Website Activity
16. Customer Complaints
17. Employee Attendance
18. Monthly Targets

The datasets contain more than **1.2 million records** in total.

---

## Data Quality Investigation

The data-quality framework checks:

- Duplicate records
- Missing primary keys
- Missing values
- Invalid and future dates
- Negative quantities and values
- Duplicate orders, invoices, and payments
- Invalid customer, product, employee, and region IDs
- Unmatched foreign keys
- Referential-integrity problems
- Cross-table reconciliation issues

A dataset-level quality score is generated using:

- Total Records
- Valid Records
- Invalid Records
- Duplicate Records
- Missing Records
- Quality Percentage

Rejected records are preserved separately to maintain a complete audit trail.

---

## Analytical Data Model

The relational model supports the following business processes:

```text
Customer → Order → Order Item → Product
Customer → Sales → Product
Product → Inventory → Warehouse
Product → Purchases → Supplier
Customer → Website Activity → Conversion
Orders → Invoices → Payments
```

The model contains:

- Fact tables
- Dimension tables
- Primary and foreign keys
- One-to-many relationships
- Analytical views
- Performance indexes

Data-model documentation and diagrams are available in the `Data_Model` directory.

---

## SQL Analysis

The SQL solution includes:

- Daily and monthly revenue
- MTD and YTD revenue
- Revenue growth
- Net profit and profit margin
- Average order value
- Customer lifetime value
- Retention and churn
- Cohort analysis
- Product and regional profitability
- Employee performance
- Return and collection rates
- Inventory turnover
- Revenue reconciliation

Advanced SQL techniques used:

- Complex joins
- Common Table Expressions
- Subqueries
- CASE expressions
- Window functions
- LAG and LEAD
- Ranking
- Running totals
- Rolling averages
- Conditional aggregation
- Views
- Indexes

---

## Python Analytics

The Python solution includes:

- Data-quality auditing
- Automated cleaning
- Exploratory data analysis
- Statistical testing
- A/B test investigation
- Marketing attribution
- Inventory investigation
- Supplier analytics
- Forecasting
- Multi-factor anomaly detection
- Executive exception generation
- Root-cause analysis
- Executive PDF generation

The four required Jupyter notebooks are:

- `Cleaning.ipynb`
- `EDA.ipynb`
- `Statistics.ipynb`
- `Forecasting.ipynb`

All notebooks include saved execution outputs.

---

## Customer and Cohort Analysis

Customers are classified into:

- VIP
- High Value
- Regular
- Low Value
- At Risk
- Churned

The cohort analysis evaluates retention for:

- Month 0
- Month 1
- Month 2
- Month 3
- Month 6
- Month 12

The analysis shows a significant retention decline in several cohorts, with the largest early-period deterioration occurring in the November 2025 cohort.

---

## Product Profitability

Product-level analysis includes:

- Units sold
- Revenue
- Discounts
- Refunds
- Product cost
- Shipping cost
- Payment fees
- Allocated marketing cost
- Net profit
- Profit margin
- Return rate
- Current inventory
- Average inventory
- Stock turnover

Products are classified as:

- Star
- Cash Generator
- Problem Product
- Dead Product

The solution also identifies products where sales are increasing while profitability is deteriorating.

---

## Marketing Attribution

Marketing performance is analyzed using:

- First-touch attribution
- Last-touch attribution
- Linear attribution
- Conversion rate
- Customer acquisition cost
- Attributed revenue
- Attributed profit
- Profit ROI

Although some channels generate high revenue, all analyzed channels produce negative attributed profit. Therefore, management should evaluate channels using profit and customer quality rather than revenue alone.

---

## A/B Test Investigation

A two-proportion statistical test was performed for the checkout-page experiment.

| Metric | Result |
|---|---:|
| Control Conversion Rate | 8.6040% |
| Treatment Conversion Rate | 8.6572% |
| Absolute Lift | 0.0532 percentage points |
| P-Value | 0.764481 |
| Statistical Significance | Not Significant |
| Effect Size | Negligible |
| Recommendation | Continue Testing |

The available evidence does not justify permanent implementation of the treatment design.

---

## Forecasting

The forecasting model predicts the next three months for:

- Revenue
- Orders
- Product demand

Next-quarter revenue is forecast at approximately **₹12.31 Cr**, representing **98.15% target achievement**.

Management action is required because the forecast remains slightly below the next-quarter revenue target.

Forecast limitations include:

- Only 12 months of historical monthly data
- Limited ability to model seasonality
- Assumption that recent trends continue
- Exposure to unexpected pricing, marketing, supplier, and economic changes

---

## Anomaly Detection

The anomaly engine evaluates:

- Transaction amount
- Transaction frequency
- Customer behavior
- Product behavior
- Discounts
- Refunds
- Time patterns
- Inventory movement
- Stock-value changes
- Isolation Forest machine-learning score

Each suspicious record receives:

- Anomaly score
- Priority
- Explanation
- Recommended action

---

## Executive Exception Engine

Each exception contains:

- Issue ID
- Issue type
- Department
- Entity ID
- Entity name
- Actual value
- Expected value
- Variance
- Priority
- Financial impact
- Root cause
- Recommended action

Exception priorities include:

- Critical
- High
- Medium
- Low

> **Important:** Gross exception exposure may contain overlapping business issues and must not be interpreted as the company’s unique financial loss.

---

## Project Structure

```text
Final_Data_Analyst_Project/
│
├── Raw_Data/
├── Cleaned_Data/
├── Data_Quality/
├── Data_Model/
│   ├── Enterprise_Data_Model.md
│   ├── Enterprise_Data_Model.png
│   └── Enterprise_Data_Model.pdf
│
├── SQL/
│   ├── Basic_Analysis.sql
│   ├── Advanced_Analysis.sql
│   ├── Cohort_Analysis.sql
│   ├── Customer_Analysis.sql
│   ├── Product_Analysis.sql
│   ├── Profitability_Analysis.sql
│   └── Reconciliation.sql
│
├── Python/
│   ├── Cleaning.ipynb
│   ├── EDA.ipynb
│   ├── Statistics.ipynb
│   ├── Forecasting.ipynb
│   └── Supporting Python Scripts
│
├── PowerBI/
│   ├── Executive_Dashboard.pbix
│   └── Dashboards Screenshot/
│
├── Exception_Report/
├── Reconciliation_Report/
├── Supporting evidence/
├── Root_Cause_Analysis/
└── Executive_Report.pdf
```

---

## Technology Stack

- **Database:** MySQL
- **Data Analysis:** Python, Pandas, NumPy
- **Statistical Analysis:** SciPy, Statsmodels
- **Machine Learning:** Scikit-learn
- **Visualization:** Matplotlib, Seaborn
- **Notebooks:** Jupyter Notebook
- **Dashboard:** Microsoft Power BI
- **Reporting:** Excel, CSV, PDF
- **Version Control:** Git and GitHub

---

## Running the Project

### 1. Clone the repository

```bash
git clone https://github.com/santhosh9528/Enterprise-Bi-Root-Cause-Profitability-Analysis.git
cd Enterprise-Bi-Root-Cause-Profitability-Analysis
```

### 2. Install Python dependencies

```bash
pip install pandas numpy matplotlib seaborn scipy statsmodels scikit-learn mysql-connector-python openpyxl reportlab jupyter
```

### 3. Configure MySQL

Create the database and execute the SQL files in the appropriate order:

```text
SQL/database.sql
SQL/load_data.sql
SQL/relationships.sql
SQL/indexes.sql
SQL/Basic_Analysis.sql
SQL/Advanced_Analysis.sql
SQL/Reconciliation.sql
```

Update the MySQL username, host, database, and port in the Python scripts if required.

The scripts request the MySQL password securely during execution. Passwords are not stored in the repository.

### 4. Run Jupyter notebooks

```bash
jupyter notebook
```

Open and run:

```text
Python/Cleaning.ipynb
Python/EDA.ipynb
Python/Statistics.ipynb
Python/Forecasting.ipynb
```

### 5. Open the Power BI dashboard

```text
PowerBI/Executive_Dashboard.pbix
```

Refresh the data-source credentials if the MySQL connection differs from the original environment.

---

## Security

- Database passwords are not hardcoded.
- Python scripts use secure password prompts.
- Environment and credential files are excluded through `.gitignore`.
- Rejected records are retained for audit purposes.
- No individual raw-data records were manually modified.

---

## Final Management Recommendation

Management should prioritize:

1. Correcting negative product and customer profitability
2. Reducing excess and dead inventory
3. Renegotiating poor-performing suppliers
4. Standardizing the revenue definition
5. Accelerating collection of overdue invoices
6. Reallocating marketing spend based on attributed profit
7. Continuing the checkout A/B test before implementation
8. Automating critical exception monitoring

---

## Author

**Santhosh Kumar M**  
Data Analyst Project – Enterprise Business Intelligence, Root Cause & Profitability Analysis
