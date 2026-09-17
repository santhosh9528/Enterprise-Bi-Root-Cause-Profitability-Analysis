USE enterprise_bi;

/* =====================================================
   CREATE COMMON PROFITABILITY VIEW
   ===================================================== */

CREATE OR REPLACE VIEW vw_sales_profitability AS

SELECT
    s.Sale_ID,
    s.Order_ID,
    s.Order_Item_ID,
    s.Sale_Date,
    DATE_FORMAT(s.Sale_Date, '%Y-%m-01') AS Sales_Month,

    s.Customer_ID,
    c.Customer_Name,
    c.Customer_Type,

    s.Product_ID,
    p.Product_Name,
    p.Category,
    p.Subcategory,

    s.Employee_ID,
    e.Employee_Name,

    s.Region_ID,
    r.Region_Name,

    s.Quantity,
    s.Gross_Sales,
    s.Discount,
    s.Net_Sales AS Revenue,

    COALESCE(rt.Refund_Amount, 0) AS Refunds,

    s.Product_Cost,
    s.Shipping_Cost,
    s.Payment_Fee,

    s.Net_Sales * mr.Marketing_Rate
        AS Allocated_Marketing_Cost,

    s.Net_Sales
    - COALESCE(rt.Refund_Amount, 0)
    - s.Product_Cost
    - s.Shipping_Cost
    - s.Payment_Fee
    - (s.Net_Sales * mr.Marketing_Rate)
        AS Net_Profit

FROM sales s

JOIN customer_master c
    ON s.Customer_ID = c.Customer_ID

JOIN product_master p
    ON s.Product_ID = p.Product_ID

JOIN employee_master e
    ON s.Employee_ID = e.Employee_ID

JOIN region_master r
    ON s.Region_ID = r.Region_ID

LEFT JOIN (
    SELECT
        Order_Item_ID,

        SUM(
            CASE
                WHEN Status = 'Refunded'
                THEN Refund_Amount
                ELSE 0
            END
        ) AS Refund_Amount

    FROM returns
    GROUP BY Order_Item_ID
) rt
    ON s.Order_Item_ID = rt.Order_Item_ID

CROSS JOIN (
    SELECT
        SUM(Spend) /
        NULLIF(
            (SELECT SUM(Net_Sales) FROM sales),
            0
        ) AS Marketing_Rate
    FROM marketing_campaigns
) mr;


/* =====================================================
   RESULT 1 — OVERALL PROFITABILITY
   ===================================================== */

SELECT
    ROUND(SUM(Revenue), 2) AS Revenue,
    ROUND(SUM(Discount), 2) AS Discounts,
    ROUND(SUM(Refunds), 2) AS Refunds,
    ROUND(SUM(Product_Cost), 2) AS Product_Cost,
    ROUND(SUM(Shipping_Cost), 2) AS Shipping_Cost,
    ROUND(SUM(Payment_Fee), 2) AS Payment_Fees,

    ROUND(
        SUM(Allocated_Marketing_Cost),
        2
    ) AS Marketing_Cost,

    ROUND(SUM(Net_Profit), 2) AS Net_Profit,

    ROUND(
        SUM(Net_Profit) /
        NULLIF(SUM(Revenue), 0) * 100,
        2
    ) AS Profit_Margin_Percentage

FROM vw_sales_profitability;


/* =====================================================
   RESULT 2 — PRODUCT PROFITABILITY
   ===================================================== */

SELECT
    Product_ID,
    Product_Name,
    Category,

    SUM(Quantity) AS Units_Sold,

    ROUND(SUM(Revenue), 2) AS Revenue,
    ROUND(SUM(Discount), 2) AS Discounts,
    ROUND(SUM(Refunds), 2) AS Refunds,
    ROUND(SUM(Product_Cost), 2) AS Product_Cost,
    ROUND(SUM(Shipping_Cost), 2) AS Shipping_Cost,
    ROUND(SUM(Payment_Fee), 2) AS Payment_Fees,

    ROUND(
        SUM(Allocated_Marketing_Cost),
        2
    ) AS Marketing_Cost,

    ROUND(SUM(Net_Profit), 2) AS Net_Profit,

    ROUND(
        SUM(Net_Profit) /
        NULLIF(SUM(Revenue), 0) * 100,
        2
    ) AS Profit_Margin_Percentage,

    RANK() OVER (
        ORDER BY SUM(Revenue) DESC
    ) AS Revenue_Rank,

    RANK() OVER (
        ORDER BY SUM(Net_Profit) DESC
    ) AS Profit_Rank

FROM vw_sales_profitability

GROUP BY
    Product_ID,
    Product_Name,
    Category

ORDER BY Net_Profit ASC;


/* =====================================================
   RESULT 3 — CATEGORY PROFITABILITY
   ===================================================== */

SELECT
    Category,

    SUM(Quantity) AS Units_Sold,

    ROUND(SUM(Revenue), 2) AS Revenue,
    ROUND(SUM(Discount), 2) AS Discounts,
    ROUND(SUM(Refunds), 2) AS Refunds,
    ROUND(SUM(Product_Cost), 2) AS Product_Cost,
    ROUND(SUM(Shipping_Cost), 2) AS Shipping_Cost,
    ROUND(SUM(Payment_Fee), 2) AS Payment_Fees,

    ROUND(
        SUM(Allocated_Marketing_Cost),
        2
    ) AS Marketing_Cost,

    ROUND(SUM(Net_Profit), 2) AS Net_Profit,

    ROUND(
        SUM(Net_Profit) /
        NULLIF(SUM(Revenue), 0) * 100,
        2
    ) AS Profit_Margin_Percentage,

    RANK() OVER (
        ORDER BY SUM(Net_Profit) DESC
    ) AS Profit_Rank

FROM vw_sales_profitability

GROUP BY Category

ORDER BY Net_Profit DESC;


/* =====================================================
   RESULT 4 — REGIONAL PROFITABILITY
   ===================================================== */

SELECT
    Region_ID,
    Region_Name,

    COUNT(DISTINCT Order_ID) AS Total_Orders,
    COUNT(DISTINCT Customer_ID) AS Customers,

    ROUND(SUM(Revenue), 2) AS Revenue,
    ROUND(SUM(Discount), 2) AS Discounts,
    ROUND(SUM(Refunds), 2) AS Refunds,
    ROUND(SUM(Product_Cost), 2) AS Product_Cost,

    ROUND(
        SUM(Allocated_Marketing_Cost),
        2
    ) AS Marketing_Cost,

    ROUND(SUM(Net_Profit), 2) AS Net_Profit,

    ROUND(
        SUM(Net_Profit) /
        NULLIF(SUM(Revenue), 0) * 100,
        2
    ) AS Profit_Margin_Percentage,

    RANK() OVER (
        ORDER BY SUM(Revenue) DESC
    ) AS Revenue_Rank,

    RANK() OVER (
        ORDER BY SUM(Net_Profit) DESC
    ) AS Profit_Rank

FROM vw_sales_profitability

GROUP BY
    Region_ID,
    Region_Name

ORDER BY Net_Profit DESC;


/* =====================================================
   RESULT 5 — CUSTOMER PROFITABILITY
   ===================================================== */

WITH Customer_Profit AS (
    SELECT
        Customer_ID,
        Customer_Name,
        Customer_Type,

        COUNT(DISTINCT Order_ID)
            AS Total_Orders,

        SUM(Revenue) AS Revenue,
        SUM(Discount) AS Discounts,
        SUM(Refunds) AS Refunds,
        SUM(Product_Cost) AS Product_Cost,
        SUM(Allocated_Marketing_Cost)
            AS Marketing_Cost,

        SUM(Net_Profit) AS Net_Profit

    FROM vw_sales_profitability

    GROUP BY
        Customer_ID,
        Customer_Name,
        Customer_Type
),

Customer_Benchmark AS (
    SELECT
        *,

        AVG(Revenue) OVER ()
            AS Average_Customer_Revenue,

        AVG(
            Net_Profit /
            NULLIF(Revenue, 0) * 100
        ) OVER () AS Average_Customer_Margin

    FROM Customer_Profit
)

SELECT
    Customer_ID,
    Customer_Name,
    Customer_Type,
    Total_Orders,

    ROUND(Revenue, 2) AS Revenue,
    ROUND(Discounts, 2) AS Discounts,
    ROUND(Refunds, 2) AS Refunds,
    ROUND(Product_Cost, 2) AS Product_Cost,
    ROUND(Marketing_Cost, 2) AS Marketing_Cost,
    ROUND(Net_Profit, 2) AS Net_Profit,

    ROUND(
        Net_Profit /
        NULLIF(Revenue, 0) * 100,
        2
    ) AS Profit_Margin_Percentage,

    CASE
        WHEN Revenue >= Average_Customer_Revenue
             AND Net_Profit < 0
            THEN 'High Revenue + Low Profit'

        WHEN Revenue < Average_Customer_Revenue
             AND Net_Profit > 0
             AND (
                 Net_Profit /
                 NULLIF(Revenue, 0) * 100
             ) >= Average_Customer_Margin
            THEN 'Low Revenue + High Margin'

        WHEN Revenue >= Average_Customer_Revenue
             AND Net_Profit >= 0
            THEN 'High Revenue + High Profit'

        WHEN Net_Profit < 0
            THEN 'Low Revenue + Negative Profit'

        ELSE 'Regular'
    END AS Customer_Profitability_Group,

    RANK() OVER (
        ORDER BY Revenue DESC
    ) AS Revenue_Rank,

    RANK() OVER (
        ORDER BY Net_Profit DESC
    ) AS Profit_Rank

FROM Customer_Benchmark

ORDER BY Net_Profit ASC;


/* =====================================================
   RESULT 6 — MONTHLY PROFITABILITY
   ===================================================== */

WITH Monthly_Profit AS (
    SELECT
        Sales_Month,

        COUNT(DISTINCT Order_ID)
            AS Total_Orders,

        SUM(Revenue) AS Revenue,
        SUM(Discount) AS Discounts,
        SUM(Refunds) AS Refunds,
        SUM(Product_Cost) AS Product_Cost,
        SUM(Shipping_Cost) AS Shipping_Cost,
        SUM(Payment_Fee) AS Payment_Fees,

        SUM(Allocated_Marketing_Cost)
            AS Marketing_Cost,

        SUM(Net_Profit) AS Net_Profit

    FROM vw_sales_profitability

    GROUP BY Sales_Month
),

Monthly_Growth AS (
    SELECT
        *,

        LAG(Revenue) OVER (
            ORDER BY Sales_Month
        ) AS Previous_Month_Revenue,

        LAG(Net_Profit) OVER (
            ORDER BY Sales_Month
        ) AS Previous_Month_Profit

    FROM Monthly_Profit
)

SELECT
    Sales_Month,
    Total_Orders,

    ROUND(Revenue, 2) AS Revenue,
    ROUND(Discounts, 2) AS Discounts,
    ROUND(Refunds, 2) AS Refunds,
    ROUND(Product_Cost, 2) AS Product_Cost,
    ROUND(Shipping_Cost, 2) AS Shipping_Cost,
    ROUND(Payment_Fees, 2) AS Payment_Fees,
    ROUND(Marketing_Cost, 2) AS Marketing_Cost,
    ROUND(Net_Profit, 2) AS Net_Profit,

    ROUND(
        Net_Profit /
        NULLIF(Revenue, 0) * 100,
        2
    ) AS Profit_Margin_Percentage,

    ROUND(
        (
            Revenue - Previous_Month_Revenue
        ) /
        NULLIF(Previous_Month_Revenue, 0) * 100,
        2
    ) AS Revenue_Growth_Percentage,

    ROUND(
        Net_Profit - Previous_Month_Profit,
        2
    ) AS Profit_Change

FROM Monthly_Growth

ORDER BY Sales_Month;


/* =====================================================
   RESULT 7 — EMPLOYEE PROFITABILITY
   ===================================================== */

SELECT
    Employee_ID,
    Employee_Name,
    Region_ID,

    COUNT(DISTINCT Order_ID)
        AS Total_Orders,

    COUNT(DISTINCT Customer_ID)
        AS Customers,

    ROUND(SUM(Revenue), 2) AS Revenue,
    ROUND(SUM(Discount), 2) AS Discounts,
    ROUND(SUM(Refunds), 2) AS Refunds,
    ROUND(SUM(Product_Cost), 2) AS Product_Cost,

    ROUND(
        SUM(Allocated_Marketing_Cost),
        2
    ) AS Marketing_Cost,

    ROUND(SUM(Net_Profit), 2) AS Net_Profit,

    ROUND(
        SUM(Net_Profit) /
        NULLIF(SUM(Revenue), 0) * 100,
        2
    ) AS Profit_Margin_Percentage,

    RANK() OVER (
        ORDER BY SUM(Revenue) DESC
    ) AS Revenue_Rank,

    RANK() OVER (
        ORDER BY SUM(Net_Profit) DESC
    ) AS Profit_Rank,

    CASE
        WHEN SUM(Net_Profit) >= 0
            THEN 'Profitable Employee'

        WHEN SUM(Revenue) >=
             AVG(SUM(Revenue)) OVER ()
             AND SUM(Net_Profit) < 0
            THEN 'High Revenue + Low Profit'

        ELSE 'Performance Review'
    END AS Employee_Performance_Group

FROM vw_sales_profitability

GROUP BY
    Employee_ID,
    Employee_Name,
    Region_ID

ORDER BY Net_Profit DESC;