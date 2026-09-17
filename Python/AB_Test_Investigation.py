from getpass import getpass
# ============================================================
# PART 11: A/B TEST INVESTIGATION
# Checkout Page - Control vs Treatment
# ============================================================

from pathlib import Path
import warnings
import math

import mysql.connector
import pandas as pd
import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore")

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)
pd.set_option("display.float_format", lambda value: f"{value:,.4f}")


# ============================================================
# 1. DATABASE CONFIGURATION
# ============================================================

MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = getpass("Enter MySQL password: ")
MYSQL_DATABASE = "enterprise_bi"


# ============================================================
# 2. TEST CONFIGURATION
# ============================================================

SIGNIFICANCE_LEVEL = 0.05
CONFIDENCE_LEVEL = 0.95

CONTROL_LABEL = "Control"
TREATMENT_LABEL = "Treatment"


# ============================================================
# 3. OUTPUT LOCATION
# ============================================================

CURRENT_FOLDER = Path(__file__).resolve().parent
PROJECT_FOLDER = CURRENT_FOLDER.parent

OUTPUT_FOLDER = PROJECT_FOLDER / "AB_Test_Analysis"
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

EXCEL_OUTPUT = OUTPUT_FOLDER / "AB_Test_Investigation_Report.xlsx"
CSV_OUTPUT = OUTPUT_FOLDER / "AB_Test_Summary.csv"
CHART_OUTPUT = OUTPUT_FOLDER / "AB_Test_Conversion_Rate.png"

print("=" * 72)
print("A/B TEST INVESTIGATION STARTED")
print("=" * 72)


# ============================================================
# 4. CONNECT TO MYSQL
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
# 5. CHECK EXPERIMENT-GROUP VALUES
# ============================================================

group_check_query = """
SELECT
    Experiment_Group,
    COUNT(*) AS Record_Count

FROM website_activity

GROUP BY Experiment_Group

ORDER BY Record_Count DESC;
"""

group_check_df = pd.read_sql(
    group_check_query,
    connection
)

print("\nAvailable experiment groups:")
print(group_check_df.to_string(index=False))


# ============================================================
# 6. LOAD SESSION-LEVEL A/B TEST DATA
# One session = one experimental observation
# ============================================================

session_query = """
WITH Session_Level_Data AS
(
    SELECT
        Session_ID,

        CASE
            WHEN LOWER(TRIM(Experiment_Group))
                 LIKE 'control%'
                THEN 'Control'

            WHEN LOWER(TRIM(Experiment_Group))
                 LIKE 'treatment%'
                THEN 'Treatment'

            WHEN LOWER(TRIM(Experiment_Group))
                 IN ('a', 'group a', 'variant a')
                THEN 'Control'

            WHEN LOWER(TRIM(Experiment_Group))
                 IN ('b', 'group b', 'variant b')
                THEN 'Treatment'

            ELSE TRIM(Experiment_Group)
        END AS Experiment_Group,

        MAX(
            CASE
                WHEN Converted = 1 THEN 1
                ELSE 0
            END
        ) AS Converted,

        MAX(Customer_ID) AS Customer_ID,
        MAX(Order_ID) AS Order_ID,
        MIN(Event_Time) AS Session_Start_Time,
        MAX(Event_Time) AS Session_End_Time

    FROM website_activity

    WHERE Session_ID IS NOT NULL
      AND TRIM(Session_ID) <> ''
      AND Experiment_Group IS NOT NULL
      AND TRIM(Experiment_Group) <> ''

    GROUP BY
        Session_ID,

        CASE
            WHEN LOWER(TRIM(Experiment_Group))
                 LIKE 'control%'
                THEN 'Control'

            WHEN LOWER(TRIM(Experiment_Group))
                 LIKE 'treatment%'
                THEN 'Treatment'

            WHEN LOWER(TRIM(Experiment_Group))
                 IN ('a', 'group a', 'variant a')
                THEN 'Control'

            WHEN LOWER(TRIM(Experiment_Group))
                 IN ('b', 'group b', 'variant b')
                THEN 'Treatment'

            ELSE TRIM(Experiment_Group)
        END
)

SELECT
    Session_ID,
    Experiment_Group,
    Converted,
    Customer_ID,
    Order_ID,
    Session_Start_Time,
    Session_End_Time

FROM Session_Level_Data

WHERE Experiment_Group IN ('Control', 'Treatment');
"""

session_df = pd.read_sql(
    session_query,
    connection
)

connection.close()

print("\nMySQL connection closed.")
print(f"\nValid A/B test sessions loaded: {len(session_df):,}")


# ============================================================
# 7. VALIDATE DATA
# ============================================================

if session_df.empty:
    raise ValueError(
        "Control/Treatment session data available illa. "
        "Experiment_Group values-a check pannanum."
    )

required_groups = {
    CONTROL_LABEL,
    TREATMENT_LABEL
}

available_groups = set(
    session_df["Experiment_Group"].unique()
)

missing_groups = required_groups - available_groups

if missing_groups:
    raise ValueError(
        f"Required experiment groups missing: {missing_groups}"
    )

session_df["Converted"] = pd.to_numeric(
    session_df["Converted"],
    errors="coerce"
).fillna(0).astype(int)

session_df["Converted"] = session_df["Converted"].clip(
    lower=0,
    upper=1
)

duplicate_sessions = session_df.duplicated(
    subset=["Session_ID"],
    keep=False
).sum()

missing_conversion_values = session_df[
    "Converted"
].isna().sum()

invalid_conversion_values = (
    ~session_df["Converted"].isin([0, 1])
).sum()


# ============================================================
# 8. CREATE GROUP SUMMARY
# ============================================================

group_summary = (
    session_df
    .groupby("Experiment_Group")
    .agg(
        Total_Sessions=("Session_ID", "nunique"),
        Conversions=("Converted", "sum"),
        Unique_Customers=("Customer_ID", "nunique"),
        Orders=("Order_ID", "nunique")
    )
    .reset_index()
)

group_summary["Non_Conversions"] = (
    group_summary["Total_Sessions"]
    - group_summary["Conversions"]
)

group_summary["Conversion_Rate"] = (
    group_summary["Conversions"]
    / group_summary["Total_Sessions"]
)

group_summary["Conversion_Rate_Percentage"] = (
    group_summary["Conversion_Rate"] * 100
)


# ============================================================
# 9. EXTRACT CONTROL AND TREATMENT VALUES
# ============================================================

control_row = group_summary[
    group_summary["Experiment_Group"] == CONTROL_LABEL
].iloc[0]

treatment_row = group_summary[
    group_summary["Experiment_Group"] == TREATMENT_LABEL
].iloc[0]

control_sessions = int(
    control_row["Total_Sessions"]
)

control_conversions = int(
    control_row["Conversions"]
)

control_rate = float(
    control_row["Conversion_Rate"]
)

treatment_sessions = int(
    treatment_row["Total_Sessions"]
)

treatment_conversions = int(
    treatment_row["Conversions"]
)

treatment_rate = float(
    treatment_row["Conversion_Rate"]
)


# ============================================================
# 10. FORMULATE HYPOTHESES
# ============================================================

null_hypothesis = (
    "H0: Treatment checkout conversion rate is equal to "
    "the Control checkout conversion rate."
)

alternative_hypothesis = (
    "H1: Treatment checkout conversion rate is different from "
    "the Control checkout conversion rate."
)


# ============================================================
# 11. TWO-PROPORTION Z-TEST
# ============================================================

pooled_conversion_rate = (
    control_conversions + treatment_conversions
) / (
    control_sessions + treatment_sessions
)

pooled_standard_error = math.sqrt(
    pooled_conversion_rate
    * (1 - pooled_conversion_rate)
    * (
        (1 / control_sessions)
        + (1 / treatment_sessions)
    )
)

if pooled_standard_error == 0:
    z_statistic = 0
    p_value = 1
else:
    z_statistic = (
        treatment_rate - control_rate
    ) / pooled_standard_error

    p_value = 2 * (
        1 - norm.cdf(abs(z_statistic))
    )


# ============================================================
# 12. CONFIDENCE INTERVAL FOR CONVERSION DIFFERENCE
# Treatment rate - Control rate
# ============================================================

conversion_difference = (
    treatment_rate - control_rate
)

unpooled_standard_error = math.sqrt(
    (
        treatment_rate
        * (1 - treatment_rate)
        / treatment_sessions
    )
    +
    (
        control_rate
        * (1 - control_rate)
        / control_sessions
    )
)

critical_z = norm.ppf(
    1 - SIGNIFICANCE_LEVEL / 2
)

confidence_interval_lower = (
    conversion_difference
    - critical_z * unpooled_standard_error
)

confidence_interval_upper = (
    conversion_difference
    + critical_z * unpooled_standard_error
)


# ============================================================
# 13. ABSOLUTE AND RELATIVE EFFECT
# ============================================================

absolute_lift_percentage_points = (
    conversion_difference * 100
)

if control_rate != 0:
    relative_lift_percentage = (
        conversion_difference
        / control_rate
        * 100
    )
else:
    relative_lift_percentage = np.nan


# ============================================================
# 14. COHEN'S H EFFECT SIZE
# ============================================================

cohens_h = (
    2 * math.asin(math.sqrt(treatment_rate))
    - 2 * math.asin(math.sqrt(control_rate))
)

absolute_cohens_h = abs(cohens_h)

if absolute_cohens_h < 0.20:
    effect_size_interpretation = "Negligible / Very Small"
elif absolute_cohens_h < 0.50:
    effect_size_interpretation = "Small"
elif absolute_cohens_h < 0.80:
    effect_size_interpretation = "Medium"
else:
    effect_size_interpretation = "Large"


# ============================================================
# 15. STATISTICAL SIGNIFICANCE
# ============================================================

if p_value < SIGNIFICANCE_LEVEL:
    statistical_result = (
        "Statistically Significant"
    )
else:
    statistical_result = (
        "Not Statistically Significant"
    )


# ============================================================
# 16. MANAGEMENT DECISION
# ============================================================

if (
    p_value < SIGNIFICANCE_LEVEL
    and conversion_difference > 0
    and confidence_interval_lower > 0
):
    management_decision = (
        "Implement Treatment Permanently"
    )

    management_reason = (
        "Treatment conversion rate Control-a vida statistically "
        "significant-ah higher. 95% confidence interval full-ah "
        "positive range-la irukku."
    )

elif (
    p_value < SIGNIFICANCE_LEVEL
    and conversion_difference < 0
    and confidence_interval_upper < 0
):
    management_decision = (
        "Reject Treatment"
    )

    management_reason = (
        "Treatment conversion rate statistically significant-ah "
        "Control-a vida lower. Existing checkout-a retain pannanum."
    )

elif (
    p_value >= SIGNIFICANCE_LEVEL
    and conversion_difference > 0
):
    management_decision = (
        "Do Not Implement Yet - Continue Testing"
    )

    management_reason = (
        "Treatment conversion konjam improve aagirukku; aana "
        "statistical evidence sufficient illa. More sample size "
        "and longer test period required."
    )

else:
    management_decision = (
        "Do Not Implement Treatment"
    )

    management_reason = (
        "Treatment measurable improvement show pannala and result "
        "statistically significant illa."
    )


# ============================================================
# 17. ADD CONFIDENCE INTERVAL FOR EACH GROUP
# ============================================================

def proportion_confidence_interval(
    conversions,
    sessions,
    z_value=1.96
):
    rate = conversions / sessions

    standard_error = math.sqrt(
        rate * (1 - rate) / sessions
    )

    lower_limit = max(
        0,
        rate - z_value * standard_error
    )

    upper_limit = min(
        1,
        rate + z_value * standard_error
    )

    return lower_limit, upper_limit


control_ci_lower, control_ci_upper = (
    proportion_confidence_interval(
        control_conversions,
        control_sessions,
        critical_z
    )
)

treatment_ci_lower, treatment_ci_upper = (
    proportion_confidence_interval(
        treatment_conversions,
        treatment_sessions,
        critical_z
    )
)

group_summary["CI_Lower_Percentage"] = np.where(
    group_summary["Experiment_Group"] == CONTROL_LABEL,
    control_ci_lower * 100,
    treatment_ci_lower * 100
)

group_summary["CI_Upper_Percentage"] = np.where(
    group_summary["Experiment_Group"] == CONTROL_LABEL,
    control_ci_upper * 100,
    treatment_ci_upper * 100
)


# ============================================================
# 18. CREATE STATISTICAL TEST SUMMARY
# ============================================================

statistical_summary = pd.DataFrame(
    {
        "Metric": [
            "Test Name",
            "Unit of Analysis",
            "Significance Level",
            "Confidence Level",
            "Control Sessions",
            "Control Conversions",
            "Control Conversion Rate (%)",
            "Treatment Sessions",
            "Treatment Conversions",
            "Treatment Conversion Rate (%)",
            "Absolute Lift (Percentage Points)",
            "Relative Lift (%)",
            "Z Statistic",
            "P Value",
            "Difference CI Lower (%)",
            "Difference CI Upper (%)",
            "Cohen's H",
            "Effect Size",
            "Statistical Result",
            "Management Decision"
        ],

        "Value": [
            "Two-Proportion Z-Test",
            "Unique Website Session",
            SIGNIFICANCE_LEVEL,
            CONFIDENCE_LEVEL,
            control_sessions,
            control_conversions,
            control_rate * 100,
            treatment_sessions,
            treatment_conversions,
            treatment_rate * 100,
            absolute_lift_percentage_points,
            relative_lift_percentage,
            z_statistic,
            p_value,
            confidence_interval_lower * 100,
            confidence_interval_upper * 100,
            cohens_h,
            effect_size_interpretation,
            statistical_result,
            management_decision
        ]
    }
)


# ============================================================
# 19. CREATE HYPOTHESIS SUMMARY
# ============================================================

hypothesis_summary = pd.DataFrame(
    {
        "Section": [
            "Business Question",
            "Null Hypothesis",
            "Alternative Hypothesis",
            "Statistical Test",
            "Significance Level",
            "P-Value Rule",
            "Test Result",
            "Management Decision",
            "Decision Reason"
        ],

        "Explanation": [
            (
                "Did the new checkout design significantly "
                "increase conversion?"
            ),
            null_hypothesis,
            alternative_hypothesis,
            (
                "Two-Proportion Z-Test because conversion is "
                "binary and two independent groups are compared."
            ),
            f"{SIGNIFICANCE_LEVEL:.2f}",
            (
                "Reject H0 when p-value is less than 0.05."
            ),
            statistical_result,
            management_decision,
            management_reason
        ]
    }
)


# ============================================================
# 20. DATA QUALITY SUMMARY
# ============================================================

data_quality_summary = pd.DataFrame(
    {
        "Check": [
            "Total Session Records",
            "Duplicate Session Records",
            "Missing Conversion Values",
            "Invalid Conversion Values",
            "Control Sessions",
            "Treatment Sessions"
        ],

        "Value": [
            len(session_df),
            duplicate_sessions,
            missing_conversion_values,
            invalid_conversion_values,
            control_sessions,
            treatment_sessions
        ]
    }
)


# ============================================================
# 21. ROUND VALUES
# ============================================================

group_summary = group_summary.round(4)

statistical_summary["Value"] = statistical_summary[
    "Value"
].apply(
    lambda value: (
        round(value, 6)
        if isinstance(value, (float, np.floating))
        else value
    )
)


# ============================================================
# 22. SAVE CSV
# ============================================================

group_summary.to_csv(
    CSV_OUTPUT,
    index=False
)


# ============================================================
# 23. SAVE EXCEL REPORT
# ============================================================

with pd.ExcelWriter(
    EXCEL_OUTPUT,
    engine="openpyxl"
) as writer:

    hypothesis_summary.to_excel(
        writer,
        sheet_name="Conclusion",
        index=False
    )

    statistical_summary.to_excel(
        writer,
        sheet_name="Statistical_Test",
        index=False
    )

    group_summary.to_excel(
        writer,
        sheet_name="Group_Summary",
        index=False
    )

    data_quality_summary.to_excel(
        writer,
        sheet_name="Data_Quality",
        index=False
    )

    session_df.to_excel(
        writer,
        sheet_name="Session_Data",
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
            ].width = min(
                maximum_length + 2,
                60
            )


# ============================================================
# 24. CREATE CONVERSION-RATE CHART
# ============================================================

sns.set_theme(style="whitegrid")

chart_df = group_summary.copy()

chart_colors = {
    "Control": "#4C78A8",
    "Treatment": "#F58518"
}

plt.figure(figsize=(9, 6))

bars = plt.bar(
    chart_df["Experiment_Group"],
    chart_df["Conversion_Rate_Percentage"],
    color=[
        chart_colors.get(group, "#808080")
        for group in chart_df["Experiment_Group"]
    ],
    width=0.55
)

for bar, conversion_rate in zip(
    bars,
    chart_df["Conversion_Rate_Percentage"]
):
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.05,
        f"{conversion_rate:.2f}%",
        ha="center",
        va="bottom",
        fontweight="bold"
    )

plt.title(
    "Checkout A/B Test Conversion Rate",
    fontsize=15,
    fontweight="bold"
)

plt.xlabel("Experiment Group")
plt.ylabel("Conversion Rate (%)")

maximum_rate = chart_df[
    "Conversion_Rate_Percentage"
].max()

plt.ylim(
    0,
    maximum_rate * 1.25
)

plt.tight_layout()

plt.savefig(
    CHART_OUTPUT,
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 25. PRINT FINAL OUTPUT
# ============================================================

print("\n" + "=" * 72)
print("A/B TEST GROUP SUMMARY")
print("=" * 72)

print(
    group_summary[
        [
            "Experiment_Group",
            "Total_Sessions",
            "Conversions",
            "Non_Conversions",
            "Conversion_Rate_Percentage",
            "CI_Lower_Percentage",
            "CI_Upper_Percentage"
        ]
    ].to_string(index=False)
)

print("\n" + "=" * 72)
print("STATISTICAL TEST RESULT")
print("=" * 72)

print(f"\nNull Hypothesis:")
print(null_hypothesis)

print(f"\nAlternative Hypothesis:")
print(alternative_hypothesis)

print(
    f"\nSignificance Level: "
    f"{SIGNIFICANCE_LEVEL:.2f}"
)

print(
    f"Control Conversion Rate: "
    f"{control_rate * 100:.4f}%"
)

print(
    f"Treatment Conversion Rate: "
    f"{treatment_rate * 100:.4f}%"
)

print(
    f"Absolute Lift: "
    f"{absolute_lift_percentage_points:.4f} "
    f"percentage points"
)

print(
    f"Relative Lift: "
    f"{relative_lift_percentage:.4f}%"
)

print(
    f"Z Statistic: "
    f"{z_statistic:.6f}"
)

print(
    f"P-Value: "
    f"{p_value:.6f}"
)

print(
    f"95% Confidence Interval for Difference: "
    f"[{confidence_interval_lower * 100:.4f}%, "
    f"{confidence_interval_upper * 100:.4f}%]"
)

print(
    f"Cohen's H: "
    f"{cohens_h:.6f}"
)

print(
    f"Effect Size: "
    f"{effect_size_interpretation}"
)

print(
    f"\nStatistical Result: "
    f"{statistical_result}"
)

print(
    f"\nManagement Decision: "
    f"{management_decision}"
)

print(
    f"\nReason: "
    f"{management_reason}"
)

print("\n" + "=" * 72)
print("A/B TEST INVESTIGATION COMPLETED SUCCESSFULLY")
print("=" * 72)

print(f"\nExcel report saved in:\n{EXCEL_OUTPUT}")
print(f"\nCSV summary saved in:\n{CSV_OUTPUT}")
print(f"\nChart saved in:\n{CHART_OUTPUT}")