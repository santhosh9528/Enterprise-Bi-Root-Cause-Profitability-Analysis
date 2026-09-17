from getpass import getpass
# ============================================================
# PART 10: MARKETING ATTRIBUTION ANALYSIS
# ============================================================

from pathlib import Path
import warnings

import mysql.connector
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore")

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)
pd.set_option("display.float_format", lambda value: f"{value:,.2f}")


# ============================================================
# 1. DATABASE CONFIGURATION
# ============================================================

MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = getpass("Enter MySQL password: ")
MYSQL_DATABASE = "enterprise_bi"


# ============================================================
# 2. OUTPUT FOLDER
# ============================================================

CURRENT_FOLDER = Path(__file__).resolve().parent
PROJECT_FOLDER = CURRENT_FOLDER.parent

OUTPUT_FOLDER = PROJECT_FOLDER / "Marketing_Analysis"
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

EXCEL_OUTPUT = OUTPUT_FOLDER / "Marketing_Attribution_Report.xlsx"
CSV_OUTPUT = OUTPUT_FOLDER / "Marketing_Channel_Summary.csv"

print("=" * 70)
print("MARKETING ATTRIBUTION ANALYSIS STARTED")
print("=" * 70)


# ============================================================
# 3. CONNECT TO MYSQL
# ============================================================

try:
    connection = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )

    print("\nMySQL connection successful!")

except mysql.connector.Error as error:
    print("\nMySQL connection failed!")
    print(error)
    raise SystemExit


# ============================================================
# 4. CAMPAIGN PERFORMANCE
# ============================================================

campaign_query = """
SELECT
    TRIM(Channel) AS Channel,

    COUNT(DISTINCT Campaign_ID) AS Campaign_Count,

    SUM(Spend) AS Marketing_Spend,
    SUM(Impressions) AS Impressions,
    SUM(Clicks) AS Clicks,
    SUM(Leads) AS Leads,
    SUM(Conversions) AS Campaign_Conversions,

    SUM(Attributed_Revenue) AS Campaign_Attributed_Revenue,
    SUM(Attributed_Profit) AS Campaign_Attributed_Profit

FROM marketing_campaigns

WHERE Channel IS NOT NULL
  AND TRIM(Channel) <> ''

GROUP BY TRIM(Channel)

ORDER BY Marketing_Spend DESC;
"""

campaign_df = pd.read_sql(campaign_query, connection)

print("\nCampaign performance loaded:")
print(campaign_df)


# ============================================================
# 5. WEBSITE CHANNEL PERFORMANCE
# ============================================================

website_query = """
SELECT
    TRIM(Channel) AS Channel,

    COUNT(*) AS Website_Events,
    COUNT(DISTINCT Session_ID) AS Website_Sessions,
    COUNT(DISTINCT Customer_ID) AS Website_Customers,

    COUNT(
        DISTINCT CASE
            WHEN Converted = 1
            THEN Session_ID
        END
    ) AS Converted_Sessions,

    COUNT(
        DISTINCT CASE
            WHEN Converted = 1
             AND Order_ID IS NOT NULL
            THEN Order_ID
        END
    ) AS Website_Orders

FROM website_activity

WHERE Channel IS NOT NULL
  AND TRIM(Channel) <> ''

GROUP BY TRIM(Channel)

ORDER BY Website_Sessions DESC;
"""

website_df = pd.read_sql(website_query, connection)

print("\nWebsite channel performance loaded:")
print(website_df)


# ============================================================
# 6. FIRST-TOUCH AND LAST-TOUCH ATTRIBUTION
# ============================================================

first_last_query = """
WITH Purchase_Events AS
(
    SELECT
        Session_ID,
        Order_ID,
        MAX(Customer_ID) AS Customer_ID

    FROM website_activity

    WHERE Converted = 1
      AND Order_ID IS NOT NULL
      AND TRIM(Order_ID) <> ''

    GROUP BY
        Session_ID,
        Order_ID
),

Session_Touch_Ranking AS
(
    SELECT
        wa.Session_ID,
        TRIM(wa.Channel) AS Channel,
        wa.Event_Time,
        wa.Event_ID,

        ROW_NUMBER() OVER
        (
            PARTITION BY wa.Session_ID
            ORDER BY
                wa.Event_Time ASC,
                wa.Event_ID ASC
        ) AS First_Touch_Rank,

        ROW_NUMBER() OVER
        (
            PARTITION BY wa.Session_ID
            ORDER BY
                wa.Event_Time DESC,
                wa.Event_ID DESC
        ) AS Last_Touch_Rank

    FROM website_activity wa

    INNER JOIN
    (
        SELECT DISTINCT Session_ID
        FROM Purchase_Events
    ) pe
        ON wa.Session_ID = pe.Session_ID

    WHERE wa.Channel IS NOT NULL
      AND TRIM(wa.Channel) <> ''
),

Session_First_Last AS
(
    SELECT
        Session_ID,

        MAX(
            CASE
                WHEN First_Touch_Rank = 1
                THEN Channel
            END
        ) AS First_Touch_Channel,

        MAX(
            CASE
                WHEN Last_Touch_Rank = 1
                THEN Channel
            END
        ) AS Last_Touch_Channel

    FROM Session_Touch_Ranking

    GROUP BY Session_ID
),

Order_Profitability AS
(
    SELECT
        Order_ID,
        MAX(Customer_ID) AS Customer_ID,
        SUM(Revenue) AS Revenue,
        SUM(Net_Profit) AS Net_Profit

    FROM vw_sales_profitability

    WHERE Order_ID IS NOT NULL

    GROUP BY Order_ID
),

Purchase_Attribution AS
(
    SELECT
        pe.Session_ID,
        pe.Order_ID,
        pe.Customer_ID,

        sfl.First_Touch_Channel,
        sfl.Last_Touch_Channel,

        COALESCE(op.Revenue, 0) AS Revenue,
        COALESCE(op.Net_Profit, 0) AS Net_Profit

    FROM Purchase_Events pe

    INNER JOIN Session_First_Last sfl
        ON pe.Session_ID = sfl.Session_ID

    LEFT JOIN Order_Profitability op
        ON pe.Order_ID = op.Order_ID
)

SELECT
    'First Touch' AS Attribution_Method,
    First_Touch_Channel AS Channel,

    COUNT(DISTINCT Order_ID) AS Attributed_Orders,
    COUNT(DISTINCT Customer_ID) AS Attributed_Customers,

    SUM(Revenue) AS Attributed_Revenue,
    SUM(Net_Profit) AS Attributed_Profit

FROM Purchase_Attribution

WHERE First_Touch_Channel IS NOT NULL

GROUP BY First_Touch_Channel

UNION ALL

SELECT
    'Last Touch' AS Attribution_Method,
    Last_Touch_Channel AS Channel,

    COUNT(DISTINCT Order_ID) AS Attributed_Orders,
    COUNT(DISTINCT Customer_ID) AS Attributed_Customers,

    SUM(Revenue) AS Attributed_Revenue,
    SUM(Net_Profit) AS Attributed_Profit

FROM Purchase_Attribution

WHERE Last_Touch_Channel IS NOT NULL

GROUP BY Last_Touch_Channel

ORDER BY
    Attribution_Method,
    Attributed_Revenue DESC;
"""

first_last_df = pd.read_sql(first_last_query, connection)

print("\nFirst-touch and last-touch attribution completed:")
print(first_last_df)


# ============================================================
# 7. LINEAR ATTRIBUTION
# ============================================================

linear_query = """
WITH Purchase_Events AS
(
    SELECT
        Session_ID,
        Order_ID,
        MAX(Customer_ID) AS Customer_ID

    FROM website_activity

    WHERE Converted = 1
      AND Order_ID IS NOT NULL
      AND TRIM(Order_ID) <> ''

    GROUP BY
        Session_ID,
        Order_ID
),

Session_Channels AS
(
    SELECT DISTINCT
        wa.Session_ID,
        TRIM(wa.Channel) AS Channel

    FROM website_activity wa

    INNER JOIN
    (
        SELECT DISTINCT Session_ID
        FROM Purchase_Events
    ) pe
        ON wa.Session_ID = pe.Session_ID

    WHERE wa.Channel IS NOT NULL
      AND TRIM(wa.Channel) <> ''
),

Session_Channel_Count AS
(
    SELECT
        Session_ID,
        COUNT(*) AS Channel_Count

    FROM Session_Channels

    GROUP BY Session_ID
),

Order_Profitability AS
(
    SELECT
        Order_ID,
        MAX(Customer_ID) AS Customer_ID,
        SUM(Revenue) AS Revenue,
        SUM(Net_Profit) AS Net_Profit

    FROM vw_sales_profitability

    WHERE Order_ID IS NOT NULL

    GROUP BY Order_ID
),

Linear_Allocation AS
(
    SELECT
        pe.Session_ID,
        pe.Order_ID,
        pe.Customer_ID,
        sc.Channel,

        1.0 /
        NULLIF(scc.Channel_Count, 0)
            AS Attribution_Weight,

        COALESCE(op.Revenue, 0) /
        NULLIF(scc.Channel_Count, 0)
            AS Allocated_Revenue,

        COALESCE(op.Net_Profit, 0) /
        NULLIF(scc.Channel_Count, 0)
            AS Allocated_Profit

    FROM Purchase_Events pe

    INNER JOIN Session_Channels sc
        ON pe.Session_ID = sc.Session_ID

    INNER JOIN Session_Channel_Count scc
        ON pe.Session_ID = scc.Session_ID

    LEFT JOIN Order_Profitability op
        ON pe.Order_ID = op.Order_ID
)

SELECT
    'Linear' AS Attribution_Method,
    Channel,

    COUNT(DISTINCT Order_ID) AS Influenced_Orders,
    COUNT(DISTINCT Customer_ID) AS Influenced_Customers,

    SUM(Attribution_Weight) AS Attributed_Order_Equivalent,
    SUM(Allocated_Revenue) AS Attributed_Revenue,
    SUM(Allocated_Profit) AS Attributed_Profit

FROM Linear_Allocation

GROUP BY Channel

ORDER BY Attributed_Revenue DESC;
"""

linear_df = pd.read_sql(linear_query, connection)

print("\nLinear attribution completed:")
print(linear_df)


# ============================================================
# 8. CLOSE DATABASE CONNECTION
# ============================================================

connection.close()

print("\nMySQL connection closed.")


# ============================================================
# 9. CLEAN CHANNEL NAMES
# ============================================================

def clean_channel_name(channel):
    if pd.isna(channel):
        return "Unknown"

    channel = str(channel).strip()

    channel_mapping = {
        "google": "Google Ads",
        "google ads": "Google Ads",
        "instagram": "Instagram",
        "email": "Email",
        "referral": "Referral",
        "organic": "Organic Search",
        "organic search": "Organic Search"
    }

    return channel_mapping.get(channel.lower(), channel.title())


for dataframe in [
    campaign_df,
    website_df,
    first_last_df,
    linear_df
]:
    dataframe["Channel"] = dataframe["Channel"].apply(clean_channel_name)


# ============================================================
# 10. CALCULATE CAMPAIGN KPIs
# ============================================================

campaign_df["Click_Through_Rate_Percentage"] = np.where(
    campaign_df["Impressions"] > 0,
    campaign_df["Clicks"] / campaign_df["Impressions"] * 100,
    0
)

campaign_df["Lead_Conversion_Rate_Percentage"] = np.where(
    campaign_df["Leads"] > 0,
    campaign_df["Campaign_Conversions"] / campaign_df["Leads"] * 100,
    0
)

campaign_df["Cost_Per_Click"] = np.where(
    campaign_df["Clicks"] > 0,
    campaign_df["Marketing_Spend"] / campaign_df["Clicks"],
    0
)

campaign_df["Cost_Per_Lead"] = np.where(
    campaign_df["Leads"] > 0,
    campaign_df["Marketing_Spend"] / campaign_df["Leads"],
    0
)

campaign_df["Campaign_CAC"] = np.where(
    campaign_df["Campaign_Conversions"] > 0,
    campaign_df["Marketing_Spend"] /
    campaign_df["Campaign_Conversions"],
    0
)

campaign_df["Campaign_ROI_Percentage"] = np.where(
    campaign_df["Marketing_Spend"] > 0,
    campaign_df["Campaign_Attributed_Profit"] /
    campaign_df["Marketing_Spend"] * 100,
    0
)

campaign_df["Campaign_ROAS"] = np.where(
    campaign_df["Marketing_Spend"] > 0,
    campaign_df["Campaign_Attributed_Revenue"] /
    campaign_df["Marketing_Spend"],
    0
)


# ============================================================
# 11. WEBSITE CONVERSION RATE
# ============================================================

website_df["Website_Conversion_Rate_Percentage"] = np.where(
    website_df["Website_Sessions"] > 0,
    website_df["Converted_Sessions"] /
    website_df["Website_Sessions"] * 100,
    0
)


# ============================================================
# 12. PREPARE ATTRIBUTION TABLES
# ============================================================

first_touch_df = first_last_df[
    first_last_df["Attribution_Method"] == "First Touch"
].copy()

last_touch_df = first_last_df[
    first_last_df["Attribution_Method"] == "Last Touch"
].copy()

first_touch_df = first_touch_df.rename(
    columns={
        "Attributed_Orders": "First_Touch_Orders",
        "Attributed_Customers": "First_Touch_Customers",
        "Attributed_Revenue": "First_Touch_Revenue",
        "Attributed_Profit": "First_Touch_Profit"
    }
)

last_touch_df = last_touch_df.rename(
    columns={
        "Attributed_Orders": "Last_Touch_Orders",
        "Attributed_Customers": "Last_Touch_Customers",
        "Attributed_Revenue": "Last_Touch_Revenue",
        "Attributed_Profit": "Last_Touch_Profit"
    }
)

first_touch_df = first_touch_df.drop(
    columns=["Attribution_Method"]
)

last_touch_df = last_touch_df.drop(
    columns=["Attribution_Method"]
)

linear_df = linear_df.rename(
    columns={
        "Influenced_Orders": "Linear_Influenced_Orders",
        "Influenced_Customers": "Linear_Influenced_Customers",
        "Attributed_Order_Equivalent": "Linear_Order_Equivalent",
        "Attributed_Revenue": "Linear_Attributed_Revenue",
        "Attributed_Profit": "Linear_Attributed_Profit"
    }
)

linear_df = linear_df.drop(
    columns=["Attribution_Method"]
)


# ============================================================
# 13. CREATE FINAL CHANNEL SUMMARY
# ============================================================

channel_summary = campaign_df.merge(
    website_df,
    on="Channel",
    how="outer"
)

channel_summary = channel_summary.merge(
    first_touch_df,
    on="Channel",
    how="outer"
)

channel_summary = channel_summary.merge(
    last_touch_df,
    on="Channel",
    how="outer"
)

channel_summary = channel_summary.merge(
    linear_df,
    on="Channel",
    how="outer"
)

numeric_columns = channel_summary.select_dtypes(
    include=[np.number]
).columns

channel_summary[numeric_columns] = (
    channel_summary[numeric_columns]
    .fillna(0)
)


# ============================================================
# 14. ATTRIBUTION CAC, ROI AND PROFITABILITY
# ============================================================

channel_summary["First_Touch_CAC"] = np.where(
    channel_summary["First_Touch_Customers"] > 0,
    channel_summary["Marketing_Spend"] /
    channel_summary["First_Touch_Customers"],
    0
)

channel_summary["Last_Touch_CAC"] = np.where(
    channel_summary["Last_Touch_Customers"] > 0,
    channel_summary["Marketing_Spend"] /
    channel_summary["Last_Touch_Customers"],
    0
)

channel_summary["Linear_CAC"] = np.where(
    channel_summary["Linear_Influenced_Customers"] > 0,
    channel_summary["Marketing_Spend"] /
    channel_summary["Linear_Influenced_Customers"],
    0
)

channel_summary["First_Touch_Profit_ROI_Percentage"] = np.where(
    channel_summary["Marketing_Spend"] > 0,
    channel_summary["First_Touch_Profit"] /
    channel_summary["Marketing_Spend"] * 100,
    0
)

channel_summary["Last_Touch_Profit_ROI_Percentage"] = np.where(
    channel_summary["Marketing_Spend"] > 0,
    channel_summary["Last_Touch_Profit"] /
    channel_summary["Marketing_Spend"] * 100,
    0
)

channel_summary["Linear_Profit_ROI_Percentage"] = np.where(
    channel_summary["Marketing_Spend"] > 0,
    channel_summary["Linear_Attributed_Profit"] /
    channel_summary["Marketing_Spend"] * 100,
    0
)

channel_summary["Linear_Profit_Per_Customer"] = np.where(
    channel_summary["Linear_Influenced_Customers"] > 0,
    channel_summary["Linear_Attributed_Profit"] /
    channel_summary["Linear_Influenced_Customers"],
    0
)

channel_summary["Linear_Revenue_Per_Customer"] = np.where(
    channel_summary["Linear_Influenced_Customers"] > 0,
    channel_summary["Linear_Attributed_Revenue"] /
    channel_summary["Linear_Influenced_Customers"],
    0
)

channel_summary["Linear_Profit_Margin_Percentage"] = np.where(
    channel_summary["Linear_Attributed_Revenue"] > 0,
    channel_summary["Linear_Attributed_Profit"] /
    channel_summary["Linear_Attributed_Revenue"] * 100,
    0
)


# ============================================================
# 15. CHANNEL RANKING
# ============================================================

channel_summary["Revenue_Rank"] = (
    channel_summary["Linear_Attributed_Revenue"]
    .rank(method="dense", ascending=False)
    .astype(int)
)

channel_summary["Profit_Rank"] = (
    channel_summary["Linear_Attributed_Profit"]
    .rank(method="dense", ascending=False)
    .astype(int)
)

channel_summary["ROI_Rank"] = (
    channel_summary["Linear_Profit_ROI_Percentage"]
    .rank(method="dense", ascending=False)
    .astype(int)
)

channel_summary["Customer_Profitability_Rank"] = (
    channel_summary["Linear_Profit_Per_Customer"]
    .rank(method="dense", ascending=False)
    .astype(int)
)


# ============================================================
# 16. CHANNEL STATUS
# ============================================================

average_conversion_rate = channel_summary[
    "Website_Conversion_Rate_Percentage"
].mean()

average_profit_per_customer = channel_summary[
    "Linear_Profit_Per_Customer"
].mean()

average_roi = channel_summary[
    "Linear_Profit_ROI_Percentage"
].mean()


def classify_channel(row):
    if (
        row["Linear_Attributed_Profit"] > 0
        and row["Linear_Profit_ROI_Percentage"] >= average_roi
        and row["Linear_Profit_Per_Customer"] >= average_profit_per_customer
    ):
        return "Most Profitable Channel"

    if (
        row["Linear_Attributed_Revenue"] > 0
        and row["Linear_Attributed_Profit"] <= 0
    ):
        return "High Revenue - Low Profit"

    if (
        row["Website_Conversion_Rate_Percentage"]
        >= average_conversion_rate
        and row["Linear_Attributed_Profit"] <= 0
    ):
        return "Good Conversion - Unprofitable"

    if (
        row["Website_Conversion_Rate_Percentage"]
        < average_conversion_rate
    ):
        return "Low Conversion"

    return "Monitor"


channel_summary["Channel_Status"] = channel_summary.apply(
    classify_channel,
    axis=1
)

channel_summary = channel_summary.sort_values(
    by=[
        "Profit_Rank",
        "Revenue_Rank"
    ]
).reset_index(drop=True)


# ============================================================
# 17. MANAGEMENT RECOMMENDATION
# ============================================================

def create_recommendation(row):
    if row["Linear_Attributed_Profit"] > 0:
        return (
            "Increase or maintain budget; channel creates "
            "profitable customers."
        )

    if (
        row["Website_Conversion_Rate_Percentage"]
        >= average_conversion_rate
        and row["Linear_Attributed_Profit"] < 0
    ):
        return (
            "Conversion is acceptable but profit is negative; "
            "reduce CAC and review discounts and product mix."
        )

    if (
        row["Linear_Attributed_Revenue"] > 0
        and row["Linear_Attributed_Profit"] < 0
    ):
        return (
            "Do not rank using revenue alone; optimize targeting, "
            "campaign cost and low-margin customer acquisition."
        )

    return (
        "Review channel tracking and improve traffic quality "
        "before increasing budget."
    )


channel_summary["Recommended_Action"] = channel_summary.apply(
    create_recommendation,
    axis=1
)


# ============================================================
# 18. ROUND NUMERIC VALUES
# ============================================================

decimal_columns = channel_summary.select_dtypes(
    include=[np.number]
).columns

channel_summary[decimal_columns] = (
    channel_summary[decimal_columns]
    .round(2)
)


# ============================================================
# 19. EXECUTIVE SUMMARY
# ============================================================

best_profit_channel = channel_summary.sort_values(
    "Linear_Attributed_Profit",
    ascending=False
).iloc[0]

best_roi_channel = channel_summary.sort_values(
    "Linear_Profit_ROI_Percentage",
    ascending=False
).iloc[0]

best_conversion_channel = channel_summary.sort_values(
    "Website_Conversion_Rate_Percentage",
    ascending=False
).iloc[0]

best_customer_channel = channel_summary.sort_values(
    "Linear_Profit_Per_Customer",
    ascending=False
).iloc[0]

executive_summary = pd.DataFrame(
    {
        "Metric": [
            "Total Marketing Spend",
            "Total Linear Attributed Revenue",
            "Total Linear Attributed Profit",
            "Highest Profit Channel",
            "Highest ROI Channel",
            "Highest Conversion Channel",
            "Most Profitable Customer Channel"
        ],

        "Value": [
            round(channel_summary["Marketing_Spend"].sum(), 2),
            round(
                channel_summary[
                    "Linear_Attributed_Revenue"
                ].sum(),
                2
            ),
            round(
                channel_summary[
                    "Linear_Attributed_Profit"
                ].sum(),
                2
            ),
            best_profit_channel["Channel"],
            best_roi_channel["Channel"],
            best_conversion_channel["Channel"],
            best_customer_channel["Channel"]
        ],

        "Supporting_Value": [
            "",
            "",
            "",
            round(
                best_profit_channel[
                    "Linear_Attributed_Profit"
                ],
                2
            ),
            round(
                best_roi_channel[
                    "Linear_Profit_ROI_Percentage"
                ],
                2
            ),
            round(
                best_conversion_channel[
                    "Website_Conversion_Rate_Percentage"
                ],
                2
            ),
            round(
                best_customer_channel[
                    "Linear_Profit_Per_Customer"
                ],
                2
            )
        ]
    }
)


# ============================================================
# 20. SAVE CSV
# ============================================================

channel_summary.to_csv(
    CSV_OUTPUT,
    index=False
)


# ============================================================
# 21. SAVE EXCEL REPORT
# ============================================================

with pd.ExcelWriter(
    EXCEL_OUTPUT,
    engine="openpyxl"
) as writer:

    executive_summary.to_excel(
        writer,
        sheet_name="Executive_Summary",
        index=False
    )

    channel_summary.to_excel(
        writer,
        sheet_name="Channel_Summary",
        index=False
    )

    campaign_df.to_excel(
        writer,
        sheet_name="Campaign_Performance",
        index=False
    )

    website_df.to_excel(
        writer,
        sheet_name="Website_Performance",
        index=False
    )

    first_last_df.to_excel(
        writer,
        sheet_name="First_Last_Touch",
        index=False
    )

    linear_df.to_excel(
        writer,
        sheet_name="Linear_Attribution",
        index=False
    )

    workbook = writer.book

    for worksheet in workbook.worksheets:
        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions

        for column_cells in worksheet.columns:
            maximum_length = 0
            column_letter = column_cells[0].column_letter

            for cell in column_cells:
                try:
                    cell_length = len(str(cell.value))

                    if cell_length > maximum_length:
                        maximum_length = cell_length

                except Exception:
                    pass

            worksheet.column_dimensions[
                column_letter
            ].width = min(maximum_length + 2, 45)


# ============================================================
# 22. CREATE CHARTS
# ============================================================

sns.set_theme(style="whitegrid")

chart_data = channel_summary.sort_values(
    "Linear_Attributed_Revenue",
    ascending=False
)


# Chart 1: Linear attributed revenue by channel

plt.figure(figsize=(11, 6))

sns.barplot(
    data=chart_data,
    x="Channel",
    y="Linear_Attributed_Revenue",
    palette="Blues_d"
)

plt.title(
    "Linear Attributed Revenue by Marketing Channel",
    fontsize=14,
    fontweight="bold"
)

plt.xlabel("Marketing Channel")
plt.ylabel("Attributed Revenue")
plt.xticks(rotation=25)
plt.tight_layout()

plt.savefig(
    OUTPUT_FOLDER / "01_Channel_Revenue.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# Chart 2: Linear attributed profit by channel

profit_colors = [
    "green" if value >= 0 else "red"
    for value in chart_data["Linear_Attributed_Profit"]
]

plt.figure(figsize=(11, 6))

plt.bar(
    chart_data["Channel"],
    chart_data["Linear_Attributed_Profit"],
    color=profit_colors
)

plt.axhline(
    y=0,
    color="black",
    linewidth=1
)

plt.title(
    "Linear Attributed Profit by Marketing Channel",
    fontsize=14,
    fontweight="bold"
)

plt.xlabel("Marketing Channel")
plt.ylabel("Attributed Profit")
plt.xticks(rotation=25)
plt.tight_layout()

plt.savefig(
    OUTPUT_FOLDER / "02_Channel_Profit.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# Chart 3: Conversion rate by channel

conversion_data = channel_summary.sort_values(
    "Website_Conversion_Rate_Percentage",
    ascending=False
)

plt.figure(figsize=(11, 6))

sns.barplot(
    data=conversion_data,
    x="Channel",
    y="Website_Conversion_Rate_Percentage",
    palette="viridis"
)

plt.title(
    "Website Conversion Rate by Channel",
    fontsize=14,
    fontweight="bold"
)

plt.xlabel("Marketing Channel")
plt.ylabel("Conversion Rate (%)")
plt.xticks(rotation=25)
plt.tight_layout()

plt.savefig(
    OUTPUT_FOLDER / "03_Channel_Conversion_Rate.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# Chart 4: ROI by channel

roi_data = channel_summary.sort_values(
    "Linear_Profit_ROI_Percentage",
    ascending=False
)

roi_colors = [
    "green" if value >= 0 else "red"
    for value in roi_data["Linear_Profit_ROI_Percentage"]
]

plt.figure(figsize=(11, 6))

plt.bar(
    roi_data["Channel"],
    roi_data["Linear_Profit_ROI_Percentage"],
    color=roi_colors
)

plt.axhline(
    y=0,
    color="black",
    linewidth=1
)

plt.title(
    "Linear Attribution Profit ROI by Channel",
    fontsize=14,
    fontweight="bold"
)

plt.xlabel("Marketing Channel")
plt.ylabel("Profit ROI (%)")
plt.xticks(rotation=25)
plt.tight_layout()

plt.savefig(
    OUTPUT_FOLDER / "04_Channel_ROI.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 23. PRINT FINAL RESULTS
# ============================================================

display_columns = [
    "Channel",
    "Marketing_Spend",
    "Website_Conversion_Rate_Percentage",
    "Linear_Attributed_Revenue",
    "Linear_Attributed_Profit",
    "Linear_Profit_Margin_Percentage",
    "Linear_CAC",
    "Linear_Profit_ROI_Percentage",
    "Linear_Profit_Per_Customer",
    "Revenue_Rank",
    "Profit_Rank",
    "ROI_Rank",
    "Channel_Status"
]

print("\n" + "=" * 70)
print("FINAL MARKETING CHANNEL SUMMARY")
print("=" * 70)

print(
    channel_summary[
        display_columns
    ].to_string(index=False)
)

print("\n" + "=" * 70)
print("MANAGEMENT CONCLUSION")
print("=" * 70)

print(
    f"\nHighest attributed profit channel: "
    f"{best_profit_channel['Channel']}"
)

print(
    f"Attributed profit: "
    f"{best_profit_channel['Linear_Attributed_Profit']:,.2f}"
)

print(
    f"\nHighest ROI channel: "
    f"{best_roi_channel['Channel']}"
)

print(
    f"Profit ROI: "
    f"{best_roi_channel['Linear_Profit_ROI_Percentage']:,.2f}%"
)

print(
    f"\nHighest conversion channel: "
    f"{best_conversion_channel['Channel']}"
)

print(
    f"Conversion rate: "
    f"{best_conversion_channel['Website_Conversion_Rate_Percentage']:,.2f}%"
)

print(
    f"\nChannel creating the most profitable customers: "
    f"{best_customer_channel['Channel']}"
)

print(
    f"Profit per customer: "
    f"{best_customer_channel['Linear_Profit_Per_Customer']:,.2f}"
)

print("\n" + "=" * 70)
print("MARKETING ATTRIBUTION ANALYSIS COMPLETED SUCCESSFULLY")
print("=" * 70)

print(f"\nExcel report saved in:\n{EXCEL_OUTPUT}")
print(f"\nCSV report saved in:\n{CSV_OUTPUT}")
print(f"\nCharts saved in:\n{OUTPUT_FOLDER}")