USE enterprise_bi;

/* =====================================================
   CREATE CUSTOMER ANALYTICS VIEW
   ===================================================== */

CREATE OR REPLACE VIEW vw_customer_analytics AS

SELECT
    cp.Customer_ID,
    cp.Customer_Name,
    cp.Customer_Type,
    cp.First_Purchase_Date,
    cp.Last_Purchase_Date,

    DATEDIFF(
        cp.Analysis_Date,
        cp.Last_Purchase_Date
    ) AS Recency_Days,

    cp.Total_Orders AS Frequency,
    cp.Revenue AS Monetary_Value,

    cp.Revenue /
    NULLIF(cp.Total_Orders, 0)
        AS Average_Order_Value,

    cp.Total_Orders / 12
        AS Monthly_Purchase_Frequency,

    cp.Revenue * 3
        AS Estimated_Three_Year_LTV,

    cp.Net_Profit,

    cp.Net_Profit /
    NULLIF(cp.Revenue, 0) * 100
        AS Profit_Margin_Percentage,

    NTILE(5) OVER (
        ORDER BY
            DATEDIFF(
                cp.Analysis_Date,
                cp.Last_Purchase_Date
            ) DESC
    ) AS Recency_Score,

    NTILE(5) OVER (
        ORDER BY cp.Total_Orders ASC
    ) AS Frequency_Score,

    NTILE(5) OVER (
        ORDER BY cp.Revenue ASC
    ) AS Monetary_Score

FROM (
    SELECT
        Customer_ID,
        Customer_Name,
        Customer_Type,

        MIN(Sale_Date)
            AS First_Purchase_Date,

        MAX(Sale_Date)
            AS Last_Purchase_Date,

        DATE_ADD(
            (SELECT MAX(Sale_Date) FROM sales),
            INTERVAL 1 DAY
        ) AS Analysis_Date,

        COUNT(DISTINCT Order_ID)
            AS Total_Orders,

        SUM(Revenue) AS Revenue,
        SUM(Net_Profit) AS Net_Profit

    FROM vw_sales_profitability

    GROUP BY
        Customer_ID,
        Customer_Name,
        Customer_Type
) cp;


/* =====================================================
   RESULT 1 — RFM, LTV AND CUSTOMER SEGMENTS
   ===================================================== */

SELECT
    Customer_ID,
    Customer_Name,
    Customer_Type,

    First_Purchase_Date,
    Last_Purchase_Date,

    Recency_Days,
    Frequency,

    ROUND(Monetary_Value, 2)
        AS Monetary_Value,

    ROUND(Average_Order_Value, 2)
        AS Average_Order_Value,

    ROUND(Monthly_Purchase_Frequency, 2)
        AS Monthly_Purchase_Frequency,

    ROUND(Estimated_Three_Year_LTV, 2)
        AS Estimated_Three_Year_LTV,

    ROUND(Net_Profit, 2)
        AS Net_Profit,

    ROUND(Profit_Margin_Percentage, 2)
        AS Profit_Margin_Percentage,

    Recency_Score,
    Frequency_Score,
    Monetary_Score,

    CASE
        WHEN Recency_Score >= 4
             AND Frequency_Score >= 4
             AND Monetary_Score >= 4
            THEN 'VIP'

        WHEN Recency_Score >= 3
             AND Frequency_Score >= 4
            THEN 'High Value'

        WHEN Recency_Score >= 3
             AND Frequency_Score >= 2
            THEN 'Regular'

        WHEN Recency_Score <= 2
             AND Frequency_Score >= 3
            THEN 'At Risk'

        WHEN Recency_Score = 1
            THEN 'Churned'

        ELSE 'Low Value'
    END AS Customer_Segment

FROM vw_customer_analytics

ORDER BY
    Monetary_Value DESC;


/* =====================================================
   RESULT 2 — CUSTOMER SEGMENT SUMMARY
   ===================================================== */

WITH Customer_Segments AS (
    SELECT
        *,

        CASE
            WHEN Recency_Score >= 4
                 AND Frequency_Score >= 4
                 AND Monetary_Score >= 4
                THEN 'VIP'

            WHEN Recency_Score >= 3
                 AND Frequency_Score >= 4
                THEN 'High Value'

            WHEN Recency_Score >= 3
                 AND Frequency_Score >= 2
                THEN 'Regular'

            WHEN Recency_Score <= 2
                 AND Frequency_Score >= 3
                THEN 'At Risk'

            WHEN Recency_Score = 1
                THEN 'Churned'

            ELSE 'Low Value'
        END AS Customer_Segment

    FROM vw_customer_analytics
)

SELECT
    Customer_Segment,

    COUNT(*) AS Customers,

    ROUND(
        COUNT(*) /
        SUM(COUNT(*)) OVER () * 100,
        2
    ) AS Customer_Percentage,

    ROUND(SUM(Monetary_Value), 2)
        AS Revenue,

    ROUND(SUM(Net_Profit), 2)
        AS Net_Profit,

    ROUND(
        SUM(Net_Profit) /
        NULLIF(SUM(Monetary_Value), 0) * 100,
        2
    ) AS Profit_Margin_Percentage,

    ROUND(
        AVG(Average_Order_Value),
        2
    ) AS Average_Order_Value,

    ROUND(
        AVG(Estimated_Three_Year_LTV),
        2
    ) AS Average_Estimated_LTV

FROM Customer_Segments

GROUP BY Customer_Segment

ORDER BY Revenue DESC;


/* =====================================================
   RESULT 3 — RETENTION AND CHURN
   ===================================================== */

WITH Customer_Activity AS (
    SELECT
        Customer_ID,
        MIN(Sale_Date) AS First_Purchase,
        MAX(Sale_Date) AS Last_Purchase
    FROM sales
    GROUP BY Customer_ID
),

Analysis_Date AS (
    SELECT
        DATE_ADD(
            MAX(Sale_Date),
            INTERVAL 1 DAY
        ) AS Report_Date
    FROM sales
),

Retention_Status AS (
    SELECT
        ca.Customer_ID,

        CASE
            WHEN ca.First_Purchase >
                 DATE_SUB(
                     ad.Report_Date,
                     INTERVAL 90 DAY
                 )
                THEN 'New Customer'

            WHEN ca.Last_Purchase >=
                 DATE_SUB(
                     ad.Report_Date,
                     INTERVAL 90 DAY
                 )
                THEN 'Retained Customer'

            ELSE 'Churned Customer'
        END AS Customer_Status

    FROM Customer_Activity ca
    CROSS JOIN Analysis_Date ad
)

SELECT
    Customer_Status,
    COUNT(*) AS Customers,

    ROUND(
        COUNT(*) /
        SUM(COUNT(*)) OVER () * 100,
        2
    ) AS Customer_Percentage

FROM Retention_Status

GROUP BY Customer_Status

ORDER BY Customers DESC;


/* =====================================================
   RESULT 4 — HIGH REVENUE + LOW PROFIT CUSTOMERS
   ===================================================== */

WITH Customer_Benchmark AS (
    SELECT
        *,

        AVG(Monetary_Value) OVER ()
            AS Average_Revenue,

        AVG(Profit_Margin_Percentage) OVER ()
            AS Average_Profit_Margin

    FROM vw_customer_analytics
)

SELECT
    Customer_ID,
    Customer_Name,
    Customer_Type,

    Frequency,

    ROUND(Monetary_Value, 2)
        AS Revenue,

    ROUND(Net_Profit, 2)
        AS Net_Profit,

    ROUND(Profit_Margin_Percentage, 2)
        AS Profit_Margin_Percentage,

    CASE
        WHEN Monetary_Value >= Average_Revenue
             AND Net_Profit < 0
            THEN 'High Revenue + Low Profit'

        WHEN Monetary_Value < Average_Revenue
             AND Profit_Margin_Percentage >
                 Average_Profit_Margin
            THEN 'Low Revenue + High Margin'

        ELSE 'Other'
    END AS Customer_Profitability_Group,

    CASE
        WHEN Monetary_Value >= Average_Revenue
             AND Net_Profit < 0
            THEN 'Review discounts, returns and service cost'

        WHEN Monetary_Value < Average_Revenue
             AND Profit_Margin_Percentage >
                 Average_Profit_Margin
            THEN 'Grow relationship and increase purchase frequency'

        ELSE 'Monitor'
    END AS Recommended_Action

FROM Customer_Benchmark

WHERE
    (
        Monetary_Value >= Average_Revenue
        AND Net_Profit < 0
    )
    OR
    (
        Monetary_Value < Average_Revenue
        AND Profit_Margin_Percentage >
            Average_Profit_Margin
    )

ORDER BY Net_Profit ASC;