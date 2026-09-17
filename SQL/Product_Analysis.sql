USE enterprise_bi;

-- ============================================================
-- PART 9: COMPLETE PRODUCT ANALYSIS
-- MySQL 8.0+
-- ============================================================

DROP TEMPORARY TABLE IF EXISTS product_performance;
DROP TEMPORARY TABLE IF EXISTS product_classification;


-- ============================================================
-- STEP 1: CREATE PRODUCT PERFORMANCE TABLE
-- ============================================================

CREATE TEMPORARY TABLE product_performance AS

WITH Product_Sales AS
(
    SELECT
        Product_ID,
        Product_Name,
        Category,
        Subcategory,

        SUM(Quantity) AS Units_Sold,
        SUM(Revenue) AS Revenue,
        SUM(Discount) AS Discounts,
        SUM(Refunds) AS Refunds,
        SUM(Product_Cost) AS Product_Cost,
        SUM(Shipping_Cost) AS Shipping_Cost,
        SUM(Payment_Fee) AS Payment_Fees,
        SUM(Allocated_Marketing_Cost) AS Marketing_Cost,
        SUM(Net_Profit) AS Net_Profit

    FROM vw_sales_profitability

    GROUP BY
        Product_ID,
        Product_Name,
        Category,
        Subcategory
),

Product_Returns AS
(
    SELECT
        Product_ID,
        SUM(Return_Quantity) AS Returned_Units

    FROM returns

    WHERE Product_ID IS NOT NULL

    GROUP BY Product_ID
),

Daily_Inventory AS
(
    SELECT
        Product_ID,
        Snapshot_Date,
        SUM(Stock_Value) AS Daily_Stock_Value

    FROM inventory

    WHERE Product_ID IS NOT NULL

    GROUP BY
        Product_ID,
        Snapshot_Date
),

Average_Inventory AS
(
    SELECT
        Product_ID,
        AVG(Daily_Stock_Value) AS Average_Inventory_Value

    FROM Daily_Inventory

    GROUP BY Product_ID
),

Latest_Inventory_Rows AS
(
    SELECT
        Product_ID,
        Warehouse_ID,
        Closing_Stock,
        Stock_Value,

        ROW_NUMBER() OVER
        (
            PARTITION BY
                Product_ID,
                Warehouse_ID

            ORDER BY
                Snapshot_Date DESC
        ) AS rn

    FROM inventory

    WHERE Product_ID IS NOT NULL
),

Current_Inventory AS
(
    SELECT
        Product_ID,

        SUM(Closing_Stock) AS Current_Inventory_Units,
        SUM(Stock_Value) AS Current_Inventory_Value

    FROM Latest_Inventory_Rows

    WHERE rn = 1

    GROUP BY Product_ID
)

SELECT
    ps.Product_ID,
    ps.Product_Name,
    ps.Category,
    ps.Subcategory,

    ps.Units_Sold,

    COALESCE(pr.Returned_Units, 0) AS Returned_Units,

    ps.Revenue,
    ps.Discounts,
    ps.Refunds,
    ps.Product_Cost,
    ps.Shipping_Cost,
    ps.Payment_Fees,
    ps.Marketing_Cost,
    ps.Net_Profit,

    ROUND(
        ps.Net_Profit /
        NULLIF(ps.Revenue, 0) * 100,
        2
    ) AS Profit_Margin_Percentage,

    ROUND(
        COALESCE(pr.Returned_Units, 0) /
        NULLIF(ps.Units_Sold, 0) * 100,
        2
    ) AS Return_Rate_Percentage,

    COALESCE(
        ci.Current_Inventory_Units,
        0
    ) AS Current_Inventory_Units,

    COALESCE(
        ci.Current_Inventory_Value,
        0
    ) AS Current_Inventory_Value,

    COALESCE(
        ai.Average_Inventory_Value,
        0
    ) AS Average_Inventory_Value,

    ROUND(
        ps.Product_Cost /
        NULLIF(ai.Average_Inventory_Value, 0),
        2
    ) AS Stock_Turnover

FROM Product_Sales ps

LEFT JOIN Product_Returns pr
    ON ps.Product_ID = pr.Product_ID

LEFT JOIN Average_Inventory ai
    ON ps.Product_ID = ai.Product_ID

LEFT JOIN Current_Inventory ci
    ON ps.Product_ID = ci.Product_ID;


-- ============================================================
-- STEP 2: CREATE PRODUCT CLASSIFICATION TABLE
-- Star / Cash Generator / Problem Product / Dead Product
-- ============================================================

CREATE TEMPORARY TABLE product_classification AS

WITH Product_Benchmarks AS
(
    SELECT
        pp.*,

        AVG(Revenue) OVER () AS Average_Revenue,

        AVG(Profit_Margin_Percentage) OVER ()
            AS Average_Profit_Margin,

        AVG(Return_Rate_Percentage) OVER ()
            AS Average_Return_Rate,

        AVG(Stock_Turnover) OVER ()
            AS Average_Stock_Turnover,

        AVG(Current_Inventory_Value) OVER ()
            AS Average_Current_Inventory_Value

    FROM product_performance pp
)

SELECT
    Product_ID,
    Product_Name,
    Category,
    Subcategory,

    Units_Sold,
    Returned_Units,

    ROUND(Revenue, 2) AS Revenue,
    ROUND(Discounts, 2) AS Discounts,
    ROUND(Refunds, 2) AS Refunds,
    ROUND(Product_Cost, 2) AS Product_Cost,
    ROUND(Shipping_Cost, 2) AS Shipping_Cost,
    ROUND(Payment_Fees, 2) AS Payment_Fees,
    ROUND(Marketing_Cost, 2) AS Marketing_Cost,
    ROUND(Net_Profit, 2) AS Net_Profit,

    ROUND(
        Profit_Margin_Percentage,
        2
    ) AS Profit_Margin_Percentage,

    ROUND(
        Return_Rate_Percentage,
        2
    ) AS Return_Rate_Percentage,

    Current_Inventory_Units,

    ROUND(
        Current_Inventory_Value,
        2
    ) AS Current_Inventory_Value,

    ROUND(
        Average_Inventory_Value,
        2
    ) AS Average_Inventory_Value,

    ROUND(
        Stock_Turnover,
        2
    ) AS Stock_Turnover,

    CASE
        WHEN Current_Inventory_Units < 0
          OR Current_Inventory_Value < 0
            THEN 'Inventory Data Issue'

        WHEN Net_Profit > 0
         AND Revenue >= Average_Revenue
         AND Profit_Margin_Percentage >= Average_Profit_Margin
         AND Return_Rate_Percentage <= Average_Return_Rate
            THEN 'Star'

        WHEN Net_Profit > 0
         AND Revenue < Average_Revenue
         AND Profit_Margin_Percentage >= Average_Profit_Margin
         AND Stock_Turnover >= Average_Stock_Turnover
            THEN 'Cash Generator'

        WHEN Net_Profit < 0
         AND Revenue >= Average_Revenue
            THEN 'Problem Product'

        WHEN Revenue < Average_Revenue
         AND Current_Inventory_Value > Average_Current_Inventory_Value
         AND Stock_Turnover < Average_Stock_Turnover
            THEN 'Dead Product'

        ELSE 'Monitor'
    END AS Product_Classification

FROM Product_Benchmarks;


-- ============================================================
-- RESULT 1: COMPLETE PRODUCT PERFORMANCE
-- ============================================================

SELECT
    Product_ID,
    Product_Name,
    Category,
    Subcategory,

    Units_Sold,
    Returned_Units,

    Revenue,
    Discounts,
    Refunds,
    Product_Cost,
    Shipping_Cost,
    Payment_Fees,
    Marketing_Cost,
    Net_Profit,

    Profit_Margin_Percentage,
    Return_Rate_Percentage,

    Current_Inventory_Units,
    Current_Inventory_Value,
    Average_Inventory_Value,
    Stock_Turnover,

    Product_Classification,

    DENSE_RANK() OVER
    (
        ORDER BY Revenue DESC
    ) AS Revenue_Rank,

    DENSE_RANK() OVER
    (
        ORDER BY Net_Profit DESC
    ) AS Profit_Rank

FROM product_classification

ORDER BY Revenue DESC;


-- ============================================================
-- RESULT 2: PRODUCT CLASSIFICATION SUMMARY
-- ============================================================

SELECT
    Product_Classification,

    COUNT(*) AS Product_Count,

    ROUND(
        COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (),
        2
    ) AS Product_Percentage,

    SUM(Units_Sold) AS Units_Sold,

    ROUND(
        SUM(Revenue),
        2
    ) AS Revenue,

    ROUND(
        SUM(Net_Profit),
        2
    ) AS Net_Profit,

    ROUND(
        SUM(Net_Profit) /
        NULLIF(SUM(Revenue), 0) * 100,
        2
    ) AS Profit_Margin_Percentage,

    ROUND(
        SUM(Returned_Units) /
        NULLIF(SUM(Units_Sold), 0) * 100,
        2
    ) AS Return_Rate_Percentage,

    ROUND(
        SUM(Current_Inventory_Value),
        2
    ) AS Current_Inventory_Value

FROM product_classification

GROUP BY Product_Classification

ORDER BY
    CASE Product_Classification
        WHEN 'Inventory Data Issue' THEN 1
        WHEN 'Problem Product' THEN 2
        WHEN 'Dead Product' THEN 3
        WHEN 'Star' THEN 4
        WHEN 'Cash Generator' THEN 5
        WHEN 'Monitor' THEN 6
        ELSE 7
    END;


-- ============================================================
-- RESULT 3: CATEGORY PRODUCT PERFORMANCE
-- ============================================================

SELECT
    Category,

    COUNT(DISTINCT Product_ID) AS Product_Count,

    SUM(Units_Sold) AS Units_Sold,

    ROUND(
        SUM(Revenue),
        2
    ) AS Revenue,

    ROUND(
        SUM(Discounts),
        2
    ) AS Discounts,

    ROUND(
        SUM(Refunds),
        2
    ) AS Refunds,

    ROUND(
        SUM(Product_Cost),
        2
    ) AS Product_Cost,

    ROUND(
        SUM(Net_Profit),
        2
    ) AS Net_Profit,

    ROUND(
        SUM(Net_Profit) /
        NULLIF(SUM(Revenue), 0) * 100,
        2
    ) AS Profit_Margin_Percentage,

    ROUND(
        SUM(Returned_Units) /
        NULLIF(SUM(Units_Sold), 0) * 100,
        2
    ) AS Return_Rate_Percentage,

    ROUND(
        SUM(Current_Inventory_Value),
        2
    ) AS Current_Inventory_Value

FROM product_classification

GROUP BY Category

ORDER BY Revenue DESC;


-- ============================================================
-- RESULT 4: TOP 20 LOSS-MAKING PRODUCTS
-- ============================================================

SELECT
    Product_ID,
    Product_Name,
    Category,

    Units_Sold,

    ROUND(
        Revenue,
        2
    ) AS Revenue,

    ROUND(
        Net_Profit,
        2
    ) AS Net_Profit,

    ROUND(
        Profit_Margin_Percentage,
        2
    ) AS Profit_Margin_Percentage,

    ROUND(
        Return_Rate_Percentage,
        2
    ) AS Return_Rate_Percentage,

    ROUND(
        Discounts,
        2
    ) AS Discounts,

    ROUND(
        Refunds,
        2
    ) AS Refunds,

    ROUND(
        Current_Inventory_Value,
        2
    ) AS Current_Inventory_Value,

    Product_Classification

FROM product_classification

WHERE Net_Profit < 0

ORDER BY Net_Profit ASC

LIMIT 20;


-- ============================================================
-- RESULT 5: NEGATIVE INVENTORY DATA-QUALITY ISSUES
-- ============================================================

SELECT
    Product_ID,
    Product_Name,
    Category,

    Current_Inventory_Units,

    ROUND(
        Current_Inventory_Value,
        2
    ) AS Current_Inventory_Value,

    ROUND(
        Average_Inventory_Value,
        2
    ) AS Average_Inventory_Value,

    ROUND(
        Stock_Turnover,
        2
    ) AS Stock_Turnover,

    Product_Classification

FROM product_classification

WHERE Current_Inventory_Units < 0
   OR Current_Inventory_Value < 0

ORDER BY Current_Inventory_Value ASC;


-- ============================================================
-- RESULT 6: MONTHLY PRODUCT TREND
-- SALES INCREASING BUT PROFIT DECREASING
-- ============================================================

WITH Product_Monthly AS
(
    SELECT
        Product_ID,
        Product_Name,
        Category,

        DATE_FORMAT(
            Sale_Date,
            '%Y-%m-01'
        ) AS Sales_Month,

        SUM(Quantity) AS Units_Sold,
        SUM(Revenue) AS Revenue,
        SUM(Net_Profit) AS Net_Profit

    FROM vw_sales_profitability

    GROUP BY
        Product_ID,
        Product_Name,
        Category,
        DATE_FORMAT(
            Sale_Date,
            '%Y-%m-01'
        )
),

Product_Trend AS
(
    SELECT
        Product_ID,
        Product_Name,
        Category,
        Sales_Month,
        Units_Sold,
        Revenue,
        Net_Profit,

        LAG(Revenue) OVER
        (
            PARTITION BY Product_ID
            ORDER BY Sales_Month
        ) AS Previous_Month_Revenue,

        LAG(Net_Profit) OVER
        (
            PARTITION BY Product_ID
            ORDER BY Sales_Month
        ) AS Previous_Month_Profit

    FROM Product_Monthly
)

SELECT
    Product_ID,
    Product_Name,
    Category,
    Sales_Month,
    Units_Sold,

    ROUND(
        Revenue,
        2
    ) AS Current_Revenue,

    ROUND(
        Previous_Month_Revenue,
        2
    ) AS Previous_Month_Revenue,

    ROUND(
        Revenue - Previous_Month_Revenue,
        2
    ) AS Revenue_Change,

    ROUND(
        (Revenue - Previous_Month_Revenue) /
        NULLIF(Previous_Month_Revenue, 0) * 100,
        2
    ) AS Revenue_Growth_Percentage,

    ROUND(
        Net_Profit,
        2
    ) AS Current_Profit,

    ROUND(
        Previous_Month_Profit,
        2
    ) AS Previous_Month_Profit,

    ROUND(
        Net_Profit - Previous_Month_Profit,
        2
    ) AS Profit_Change,

    CASE
        WHEN Revenue > Previous_Month_Revenue
         AND Net_Profit < Previous_Month_Profit
            THEN 'Sales Increasing - Profit Decreasing'
        ELSE 'Normal'
    END AS Trend_Status

FROM Product_Trend

WHERE Previous_Month_Revenue IS NOT NULL
  AND Previous_Month_Profit IS NOT NULL
  AND Revenue > Previous_Month_Revenue
  AND Net_Profit < Previous_Month_Profit

ORDER BY
    Profit_Change ASC,
    Revenue_Change DESC;


-- ============================================================
-- RESULT 7: ROOT-CAUSE SUMMARY FOR PROBLEM PRODUCTS
-- ============================================================

SELECT
    Product_ID,
    Product_Name,
    Category,

    ROUND(
        Revenue,
        2
    ) AS Revenue,

    ROUND(
        Net_Profit,
        2
    ) AS Net_Profit,

    ROUND(
        Profit_Margin_Percentage,
        2
    ) AS Profit_Margin_Percentage,

    ROUND(
        Discounts / NULLIF(Revenue, 0) * 100,
        2
    ) AS Discount_Percentage,

    ROUND(
        Refunds / NULLIF(Revenue, 0) * 100,
        2
    ) AS Refund_Percentage,

    ROUND(
        Product_Cost / NULLIF(Revenue, 0) * 100,
        2
    ) AS Product_Cost_Percentage,

    ROUND(
        Shipping_Cost / NULLIF(Revenue, 0) * 100,
        2
    ) AS Shipping_Cost_Percentage,

    ROUND(
        Payment_Fees / NULLIF(Revenue, 0) * 100,
        2
    ) AS Payment_Fee_Percentage,

    ROUND(
        Marketing_Cost / NULLIF(Revenue, 0) * 100,
        2
    ) AS Marketing_Cost_Percentage,

    CASE
        WHEN Product_Cost / NULLIF(Revenue, 0) >= 0.70
            THEN 'High Product Cost'

        WHEN Marketing_Cost / NULLIF(Revenue, 0) >= 0.30
            THEN 'High Marketing Cost'

        WHEN Discounts / NULLIF(Revenue, 0) >= 0.10
            THEN 'High Discount'

        WHEN Refunds / NULLIF(Revenue, 0) >= 0.05
            THEN 'High Refund'

        WHEN Shipping_Cost / NULLIF(Revenue, 0) >= 0.08
            THEN 'High Shipping Cost'

        ELSE 'Combined Cost Pressure'
    END AS Likely_Root_Cause

FROM product_classification

WHERE Net_Profit < 0

ORDER BY Net_Profit ASC

LIMIT 50;