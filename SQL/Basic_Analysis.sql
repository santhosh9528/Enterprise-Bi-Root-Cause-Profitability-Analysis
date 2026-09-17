USE enterprise_bi;

WITH Sales_KPI AS (
    SELECT
        SUM(Gross_Sales) AS Gross_Revenue,
        SUM(Discount) AS Total_Discount,
        SUM(Net_Sales) AS Database_Revenue,
        SUM(Product_Cost) AS Product_Cost,
        SUM(Shipping_Cost) AS Shipping_Cost,
        SUM(Payment_Fee) AS Payment_Fees,
        COUNT(DISTINCT Order_ID) AS Total_Orders,
        COUNT(DISTINCT Customer_ID) AS Total_Customers
    FROM sales
),

Return_KPI AS (
    SELECT
        SUM(
            CASE
                WHEN Status = 'Refunded'
                THEN Refund_Amount
                ELSE 0
            END
        ) AS Total_Refunds
    FROM returns
),

Marketing_KPI AS (
    SELECT
        SUM(Spend) AS Marketing_Cost
    FROM marketing_campaigns
)

SELECT
    ROUND(s.Gross_Revenue, 2) AS Gross_Revenue,
    ROUND(s.Total_Discount, 2) AS Total_Discount,
    ROUND(s.Database_Revenue, 2) AS Database_Revenue,
    ROUND(r.Total_Refunds, 2) AS Total_Refunds,
    ROUND(s.Product_Cost, 2) AS Product_Cost,
    ROUND(s.Shipping_Cost, 2) AS Shipping_Cost,
    ROUND(s.Payment_Fees, 2) AS Payment_Fees,
    ROUND(m.Marketing_Cost, 2) AS Marketing_Cost,

    ROUND(
        s.Database_Revenue
        - r.Total_Refunds
        - s.Product_Cost
        - s.Shipping_Cost
        - s.Payment_Fees
        - m.Marketing_Cost,
        2
    ) AS Net_Profit,

    ROUND(
        (
            s.Database_Revenue
            - r.Total_Refunds
            - s.Product_Cost
            - s.Shipping_Cost
            - s.Payment_Fees
            - m.Marketing_Cost
        ) / NULLIF(s.Database_Revenue, 0) * 100,
        2
    ) AS Profit_Margin_Percentage,

    s.Total_Orders,
    s.Total_Customers,

    ROUND(
        s.Database_Revenue /
        NULLIF(s.Total_Orders, 0),
        2
    ) AS Average_Order_Value

FROM Sales_KPI s
CROSS JOIN Return_KPI r
CROSS JOIN Marketing_KPI m;

WITH Monthly_Sales AS (
    SELECT
        DATE_FORMAT(Sale_Date, '%Y-%m-01') AS Sales_Month,
        SUM(Net_Sales) AS Revenue,
        SUM(Product_Cost) AS Product_Cost,
        SUM(Shipping_Cost) AS Shipping_Cost,
        SUM(Payment_Fee) AS Payment_Fees,
        COUNT(DISTINCT Order_ID) AS Total_Orders
    FROM sales
    GROUP BY DATE_FORMAT(Sale_Date, '%Y-%m-01')
),

Monthly_Returns AS (
    SELECT
        DATE_FORMAT(Return_Date, '%Y-%m-01') AS Return_Month,
        SUM(
            CASE
                WHEN Status = 'Refunded'
                THEN Refund_Amount
                ELSE 0
            END
        ) AS Refunds
    FROM returns
    GROUP BY DATE_FORMAT(Return_Date, '%Y-%m-01')
),

Monthly_Marketing AS (
    SELECT
        DATE_FORMAT(Campaign_Date, '%Y-%m-01') AS Campaign_Month,
        SUM(Spend) AS Marketing_Cost
    FROM marketing_campaigns
    GROUP BY DATE_FORMAT(Campaign_Date, '%Y-%m-01')
),

Monthly_Result AS (
    SELECT
        s.Sales_Month,
        s.Revenue,
        COALESCE(r.Refunds, 0) AS Refunds,
        s.Product_Cost,
        s.Shipping_Cost,
        s.Payment_Fees,
        COALESCE(m.Marketing_Cost, 0) AS Marketing_Cost,
        s.Total_Orders,

        s.Revenue
        - COALESCE(r.Refunds, 0)
        - s.Product_Cost
        - s.Shipping_Cost
        - s.Payment_Fees
        - COALESCE(m.Marketing_Cost, 0)
        AS Net_Profit

    FROM Monthly_Sales s

    LEFT JOIN Monthly_Returns r
        ON s.Sales_Month = r.Return_Month

    LEFT JOIN Monthly_Marketing m
        ON s.Sales_Month = m.Campaign_Month
),

Growth_Result AS (
    SELECT
        *,
        LAG(Revenue) OVER (
            ORDER BY Sales_Month
        ) AS Previous_Month_Revenue
    FROM Monthly_Result
)

SELECT
    Sales_Month,
    ROUND(Revenue, 2) AS Revenue,
    ROUND(Net_Profit, 2) AS Net_Profit,

    ROUND(
        Net_Profit /
        NULLIF(Revenue, 0) * 100,
        2
    ) AS Profit_Margin_Percentage,

    Total_Orders,
    ROUND(Previous_Month_Revenue, 2)
        AS Previous_Month_Revenue,

    ROUND(
        (
            Revenue - Previous_Month_Revenue
        ) / NULLIF(Previous_Month_Revenue, 0) * 100,
        2
    ) AS Revenue_Growth_Percentage

FROM Growth_Result
ORDER BY Sales_Month;



WITH Daily_Revenue AS (
    SELECT
        Sale_Date,
        SUM(Net_Sales) AS Daily_Revenue,
        COUNT(DISTINCT Order_ID) AS Daily_Orders
    FROM sales
    GROUP BY Sale_Date
),

Daily_Calculation AS (
    SELECT
        Sale_Date,
        Daily_Revenue,
        Daily_Orders,

        SUM(Daily_Revenue) OVER (
            PARTITION BY
                YEAR(Sale_Date),
                MONTH(Sale_Date)
            ORDER BY Sale_Date
        ) AS MTD_Revenue,

        SUM(Daily_Revenue) OVER (
            PARTITION BY YEAR(Sale_Date)
            ORDER BY Sale_Date
        ) AS YTD_Revenue,

        SUM(Daily_Revenue) OVER (
            ORDER BY Sale_Date
        ) AS Running_Total_Revenue,

        AVG(Daily_Revenue) OVER (
            ORDER BY Sale_Date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS Seven_Day_Rolling_Average,

        LAG(Daily_Revenue) OVER (
            ORDER BY Sale_Date
        ) AS Previous_Day_Revenue,

        LEAD(Daily_Revenue) OVER (
            ORDER BY Sale_Date
        ) AS Next_Day_Revenue

    FROM Daily_Revenue
)

SELECT
    Sale_Date,
    ROUND(Daily_Revenue, 2) AS Daily_Revenue,
    Daily_Orders,
    ROUND(MTD_Revenue, 2) AS MTD_Revenue,
    ROUND(YTD_Revenue, 2) AS YTD_Revenue,
    ROUND(Running_Total_Revenue, 2)
        AS Running_Total_Revenue,
    ROUND(Seven_Day_Rolling_Average, 2)
        AS Seven_Day_Rolling_Average,
    ROUND(Previous_Day_Revenue, 2)
        AS Previous_Day_Revenue,
    ROUND(Next_Day_Revenue, 2)
        AS Next_Day_Revenue
FROM Daily_Calculation
ORDER BY Sale_Date;