USE enterprise_bi;

/* Old temporary table irundha remove pannum */
DROP TEMPORARY TABLE IF EXISTS cohort_retention_long;


/* =====================================================
   CREATE MONTHLY COHORT RETENTION TABLE
   ===================================================== */

CREATE TEMPORARY TABLE cohort_retention_long AS

WITH Customer_First_Purchase AS (
    SELECT
        Customer_ID,

        DATE_FORMAT(
            MIN(Sale_Date),
            '%Y-%m-01'
        ) AS Cohort_Month

    FROM sales

    GROUP BY Customer_ID
),

Customer_Activity AS (
    SELECT DISTINCT
        Customer_ID,

        DATE_FORMAT(
            Sale_Date,
            '%Y-%m-01'
        ) AS Activity_Month

    FROM sales
),

Cohort_Activity AS (
    SELECT
        fp.Customer_ID,
        fp.Cohort_Month,
        ca.Activity_Month,

        TIMESTAMPDIFF(
            MONTH,
            fp.Cohort_Month,
            ca.Activity_Month
        ) AS Month_Number

    FROM Customer_First_Purchase fp

    JOIN Customer_Activity ca
        ON fp.Customer_ID = ca.Customer_ID

    WHERE ca.Activity_Month >= fp.Cohort_Month
),

Cohort_Size AS (
    SELECT
        Cohort_Month,
        COUNT(DISTINCT Customer_ID)
            AS Cohort_Customers

    FROM Customer_First_Purchase

    GROUP BY Cohort_Month
),

Retained_Customers AS (
    SELECT
        Cohort_Month,
        Month_Number,

        COUNT(DISTINCT Customer_ID)
            AS Retained_Customers

    FROM Cohort_Activity

    GROUP BY
        Cohort_Month,
        Month_Number
)

SELECT
    rc.Cohort_Month,
    rc.Month_Number,
    cs.Cohort_Customers,
    rc.Retained_Customers,

    ROUND(
        rc.Retained_Customers /
        NULLIF(cs.Cohort_Customers, 0) * 100,
        2
    ) AS Retention_Percentage

FROM Retained_Customers rc

JOIN Cohort_Size cs
    ON rc.Cohort_Month = cs.Cohort_Month

WHERE rc.Month_Number BETWEEN 0 AND 12;


/* =====================================================
   RESULT 1 — COHORT RETENTION MATRIX
   ===================================================== */

SELECT
    Cohort_Month,

    MAX(Cohort_Customers)
        AS Cohort_Customers,

    COALESCE(
        MAX(
            CASE
                WHEN Month_Number = 0
                THEN Retention_Percentage
            END
        ),
        0
    ) AS Month_0,

    COALESCE(
        MAX(
            CASE
                WHEN Month_Number = 1
                THEN Retention_Percentage
            END
        ),
        0
    ) AS Month_1,

    COALESCE(
        MAX(
            CASE
                WHEN Month_Number = 2
                THEN Retention_Percentage
            END
        ),
        0
    ) AS Month_2,

    COALESCE(
        MAX(
            CASE
                WHEN Month_Number = 3
                THEN Retention_Percentage
            END
        ),
        0
    ) AS Month_3,

    COALESCE(
        MAX(
            CASE
                WHEN Month_Number = 6
                THEN Retention_Percentage
            END
        ),
        0
    ) AS Month_6,

    COALESCE(
        MAX(
            CASE
                WHEN Month_Number = 12
                THEN Retention_Percentage
            END
        ),
        0
    ) AS Month_12

FROM cohort_retention_long

GROUP BY Cohort_Month

ORDER BY Cohort_Month;


/* =====================================================
   RESULT 2 — AVERAGE RETENTION TREND
   ===================================================== */

SELECT
    Month_Number,

    ROUND(
        AVG(Retention_Percentage),
        2
    ) AS Average_Retention_Percentage,

    SUM(Retained_Customers)
        AS Total_Retained_Customers,

    COUNT(DISTINCT Cohort_Month)
        AS Cohorts_Available

FROM cohort_retention_long

WHERE Month_Number IN (0, 1, 2, 3, 6, 12)

GROUP BY Month_Number

ORDER BY Month_Number;


/* =====================================================
   RESULT 3 — LARGEST COHORT RETENTION DROPS
   ===================================================== */

WITH Retention_Change AS (
    SELECT
        Cohort_Month,
        Month_Number,
        Cohort_Customers,
        Retained_Customers,
        Retention_Percentage,

        LAG(Retention_Percentage) OVER (
            PARTITION BY Cohort_Month
            ORDER BY Month_Number
        ) AS Previous_Month_Retention

    FROM cohort_retention_long
),

Retention_Drop AS (
    SELECT
        Cohort_Month,
        Month_Number,
        Cohort_Customers,
        Previous_Month_Retention,
        Retention_Percentage,

        Previous_Month_Retention
        - Retention_Percentage
            AS Retention_Drop_Percentage

    FROM Retention_Change
)

SELECT
    Cohort_Month,
    Month_Number,
    Cohort_Customers,

    ROUND(
        Previous_Month_Retention,
        2
    ) AS Previous_Month_Retention,

    ROUND(
        Retention_Percentage,
        2
    ) AS Current_Month_Retention,

    ROUND(
        Retention_Drop_Percentage,
        2
    ) AS Retention_Drop_Percentage

FROM Retention_Drop

WHERE Retention_Drop_Percentage > 0

ORDER BY Retention_Drop_Percentage DESC

LIMIT 20;


/* =====================================================
   RESULT 4 — COHORT IMPROVING OR DECLINING
   ===================================================== */

WITH Cohort_Month_One AS (
    SELECT
        Cohort_Month,
        Cohort_Customers,
        Retention_Percentage AS Month_1_Retention,

        LAG(Retention_Percentage) OVER (
            ORDER BY Cohort_Month
        ) AS Previous_Cohort_Retention

    FROM cohort_retention_long

    WHERE Month_Number = 1
)

SELECT
    Cohort_Month,
    Cohort_Customers,
    Month_1_Retention,
    Previous_Cohort_Retention,

    ROUND(
        Month_1_Retention
        - Previous_Cohort_Retention,
        2
    ) AS Retention_Change,

    CASE
        WHEN Previous_Cohort_Retention IS NULL
            THEN 'First Cohort'

        WHEN Month_1_Retention >
             Previous_Cohort_Retention
            THEN 'Improving'

        WHEN Month_1_Retention <
             Previous_Cohort_Retention
            THEN 'Declining'

        ELSE 'No Change'
    END AS Retention_Trend

FROM Cohort_Month_One

ORDER BY Cohort_Month;