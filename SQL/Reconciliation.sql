USE enterprise_bi;

WITH Management_Data AS (
    SELECT
        SUM(Management_Reported_Revenue)
            AS Management_Revenue
    FROM monthly_targets
),

Sales_Data AS (
    SELECT
        SUM(Gross_Sales) AS Gross_Sales,
        SUM(Discount) AS Discounts,
        SUM(Net_Sales) AS Database_Revenue
    FROM sales
),

Return_Data AS (
    SELECT
        SUM(Refund_Amount) AS Total_Return_Value,

        SUM(
            CASE
                WHEN Status = 'Refunded'
                THEN Refund_Amount
                ELSE 0
            END
        ) AS Actual_Refunds
    FROM returns
),

Orders_Without_Sales AS (
    SELECT
        COUNT(*) AS Unmatched_Order_Count,
        SUM(o.Management_Order_Value)
            AS Unmatched_Order_Value
    FROM orders o
    LEFT JOIN sales s
        ON o.Order_ID = s.Order_ID
    WHERE s.Order_ID IS NULL
)

SELECT
    ROUND(m.Management_Revenue, 2)
        AS Management_Revenue,

    ROUND(s.Gross_Sales, 2)
        AS Database_Gross_Sales,

    ROUND(s.Discounts, 2)
        AS Discounts,

    ROUND(s.Database_Revenue, 2)
        AS Database_Net_Revenue,

    ROUND(r.Total_Return_Value, 2)
        AS Total_Return_Value,

    ROUND(r.Actual_Refunds, 2)
        AS Actual_Refunds,

    u.Unmatched_Order_Count,

    ROUND(
        COALESCE(u.Unmatched_Order_Value, 0),
        2
    ) AS Unmatched_Order_Value,

    ROUND(
        m.Management_Revenue
        - s.Database_Revenue,
        2
    ) AS Revenue_Difference_Before_Refunds,

    ROUND(
        m.Management_Revenue
        - (
            s.Database_Revenue
            - r.Actual_Refunds
        ),
        2
    ) AS Final_Reconciliation_Difference,

    ROUND(
        m.Management_Revenue
        - s.Gross_Sales,
        2
    ) AS Management_Vs_Gross_Source_Difference

FROM Management_Data m
CROSS JOIN Sales_Data s
CROSS JOIN Return_Data r
CROSS JOIN Orders_Without_Sales u;