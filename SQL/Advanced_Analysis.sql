USE enterprise_bi;

WITH Sales_Summary AS (
    SELECT
        SUM(Quantity) AS Units_Sold,
        SUM(Product_Cost) AS Cost_Of_Goods_Sold
    FROM sales
),

Return_Summary AS (
    SELECT
        SUM(Return_Quantity) AS Returned_Units,
        SUM(
            CASE
                WHEN Status = 'Refunded'
                THEN Refund_Amount
                ELSE 0
            END
        ) AS Refunded_Amount
    FROM returns
),

Invoice_Summary AS (
    SELECT
        SUM(Invoice_Amount) AS Total_Invoiced
    FROM invoices
),

Payment_Summary AS (
    SELECT
        SUM(
            CASE
                WHEN Payment_Status = 'Successful'
                THEN Payment_Amount
                ELSE 0
            END
        ) AS Successful_Collections,

        SUM(
            CASE
                WHEN Payment_Status = 'Failed'
                THEN Payment_Amount
                ELSE 0
            END
        ) AS Failed_Payments
    FROM payments
),

Daily_Inventory AS (
    SELECT
        Snapshot_Date,
        SUM(Stock_Value) AS Daily_Inventory_Value
    FROM inventory
    GROUP BY Snapshot_Date
),

Inventory_Summary AS (
    SELECT
        AVG(Daily_Inventory_Value)
            AS Average_Inventory_Value
    FROM Daily_Inventory
)

SELECT
    s.Units_Sold,
    r.Returned_Units,

    ROUND(
        r.Returned_Units /
        NULLIF(s.Units_Sold, 0) * 100,
        2
    ) AS Return_Rate_Percentage,

    ROUND(r.Refunded_Amount, 2)
        AS Refunded_Amount,

    ROUND(i.Total_Invoiced, 2)
        AS Total_Invoiced,

    ROUND(p.Successful_Collections, 2)
        AS Successful_Collections,

    ROUND(p.Failed_Payments, 2)
        AS Failed_Payments,

    ROUND(
        p.Successful_Collections /
        NULLIF(i.Total_Invoiced, 0) * 100,
        2
    ) AS Collection_Rate_Percentage,

    ROUND(inv.Average_Inventory_Value, 2)
        AS Average_Inventory_Value,

    ROUND(
        s.Cost_Of_Goods_Sold /
        NULLIF(inv.Average_Inventory_Value, 0),
        2
    ) AS Inventory_Turnover,

    ROUND(
        365 /
        NULLIF(
            s.Cost_Of_Goods_Sold /
            NULLIF(inv.Average_Inventory_Value, 0),
            0
        ),
        2
    ) AS Days_Inventory

FROM Sales_Summary s
CROSS JOIN Return_Summary r
CROSS JOIN Invoice_Summary i
CROSS JOIN Payment_Summary p
CROSS JOIN Inventory_Summary inv;


WITH Payment_By_Invoice AS (
    SELECT
        Invoice_ID,

        SUM(
            CASE
                WHEN Payment_Status = 'Successful'
                THEN Payment_Amount
                ELSE 0
            END
        ) AS Paid_Amount,

        COUNT(
            CASE
                WHEN Payment_Status = 'Successful'
                THEN Payment_ID
            END
        ) AS Successful_Payment_Count

    FROM payments
    GROUP BY Invoice_ID
),

Invoice_Reconciliation AS (
    SELECT
        i.Invoice_ID,
        i.Customer_ID,
        i.Invoice_Amount,

        COALESCE(p.Paid_Amount, 0)
            AS Paid_Amount,

        COALESCE(p.Successful_Payment_Count, 0)
            AS Successful_Payment_Count,

        LEAST(
            COALESCE(p.Paid_Amount, 0),
            i.Invoice_Amount
        ) AS Recognized_Collection,

        GREATEST(
            COALESCE(p.Paid_Amount, 0)
            - i.Invoice_Amount,
            0
        ) AS Overpayment,

        GREATEST(
            i.Invoice_Amount
            - COALESCE(p.Paid_Amount, 0),
            0
        ) AS Outstanding_Amount

    FROM invoices i

    LEFT JOIN Payment_By_Invoice p
        ON i.Invoice_ID = p.Invoice_ID
)

SELECT
    ROUND(SUM(Invoice_Amount), 2)
        AS Total_Invoiced,

    ROUND(SUM(Paid_Amount), 2)
        AS Raw_Payment_Amount,

    ROUND(SUM(Recognized_Collection), 2)
        AS Recognized_Collection,

    ROUND(SUM(Overpayment), 2)
        AS Overpayment,

    ROUND(SUM(Outstanding_Amount), 2)
        AS Outstanding_Amount,

    ROUND(
        SUM(Recognized_Collection) /
        NULLIF(SUM(Invoice_Amount), 0) * 100,
        2
    ) AS Corrected_Collection_Rate,

    SUM(
        CASE
            WHEN Paid_Amount > Invoice_Amount
            THEN 1
            ELSE 0
        END
    ) AS Overpaid_Invoices,

    SUM(
        CASE
            WHEN Successful_Payment_Count > 1
            THEN 1
            ELSE 0
        END
    ) AS Invoices_With_Multiple_Payments

FROM Invoice_Reconciliation;


WITH Regional_Sales AS (
    SELECT
        s.Region_ID,
        r.Region_Name,
        SUM(s.Net_Sales) AS Revenue,
        SUM(s.Product_Cost) AS Product_Cost,
        SUM(s.Shipping_Cost) AS Shipping_Cost,
        SUM(s.Payment_Fee) AS Payment_Fees,
        COUNT(DISTINCT s.Order_ID) AS Total_Orders,
        COUNT(DISTINCT s.Customer_ID) AS Customers
    FROM sales s
    JOIN region_master r
        ON s.Region_ID = r.Region_ID
    GROUP BY
        s.Region_ID,
        r.Region_Name
),

Regional_Returns AS (
    SELECT
        o.Region_ID,

        SUM(
            CASE
                WHEN rt.Status = 'Refunded'
                THEN rt.Refund_Amount
                ELSE 0
            END
        ) AS Refunds

    FROM returns rt
    JOIN orders o
        ON rt.Order_ID = o.Order_ID
    GROUP BY o.Region_ID
),

Marketing_Total AS (
    SELECT
        SUM(Spend) AS Marketing_Cost
    FROM marketing_campaigns
),

Regional_Result AS (
    SELECT
        rs.*,
        COALESCE(rr.Refunds, 0) AS Refunds,

        mt.Marketing_Cost
        * rs.Revenue
        / SUM(rs.Revenue) OVER ()
            AS Allocated_Marketing_Cost

    FROM Regional_Sales rs

    LEFT JOIN Regional_Returns rr
        ON rs.Region_ID = rr.Region_ID

    CROSS JOIN Marketing_Total mt
)

SELECT
    Region_ID,
    Region_Name,
    Total_Orders,
    Customers,

    ROUND(Revenue, 2) AS Revenue,
    ROUND(Refunds, 2) AS Refunds,

    ROUND(
        Revenue
        - Refunds
        - Product_Cost
        - Shipping_Cost
        - Payment_Fees
        - Allocated_Marketing_Cost,
        2
    ) AS Net_Profit,

    ROUND(
        (
            Revenue
            - Refunds
            - Product_Cost
            - Shipping_Cost
            - Payment_Fees
            - Allocated_Marketing_Cost
        ) / NULLIF(Revenue, 0) * 100,
        2
    ) AS Profit_Margin_Percentage,

    RANK() OVER (
        ORDER BY
            Revenue
            - Refunds
            - Product_Cost
            - Shipping_Cost
            - Payment_Fees
            - Allocated_Marketing_Cost
            DESC
    ) AS Profit_Rank

FROM Regional_Result
ORDER BY Net_Profit DESC;