-- Average monthly spend by GLP-1 status and category

SELECT
    c.category_name,
    c.category_type,
    h.is_glp1_user,
    ROUND(AVG(t.spend)::NUMERIC, 2)     AS avg_monthly_spend,
    COUNT(DISTINCT t.household_id)      AS household_count
FROM transactions t 
JOIN households h ON t.household_id = h.household_id
JOIN categories c ON t.category_id = c.category_id
GROUP BY c.category_name, c.category_type, h.is_glp1_user
ORDER BY c.category_type DESC, avg_monthly_spend DESC;

-- Spending tragectory: pre vd post GLP-1 adoption (window function)

WITH monthly_spend AS (
    SELECT
        t.household_id,
        t.month,
        t.months_on_drug,
        c.category_name,
        t.spend, 
        h.income_bracket,
        CASE   
            WHEN t.months_on_drug = 0 THEN 'pre_adoption'
            WHEN t.months_on_drug <= 3 THEN '0_3 months'
            WHEN t.months_on_drug <= 6 THEN '3_6 months'
            ELSE '6_plus_months'
        END AS adoption_stage
    FROM transactions t 
    JOIN households h ON t.household_id = h.household_id
    JOIN categories c ON t.category_id = c.category_id
    WHERE h.is_glp1_user = TRUE
),
baseline AS (
    SELECT household_id, category_name,
            AVG(spend) AS baseline_spend
    FROM monthly_spend
    WHERE adoption_stage = 'pre_adoption'
    GROUP BY household_id, category_name
)
SELECT
    ms.category_name,
    ms.adoption_stage,
    ROUND(AVG(ms.spend)::NUMERIC, 2)                AS avg_spend,
    ROUND(AVG(b.baseline_spend)::NUMERIC, 2)        AS avg_baseline,
    ROUND(
        ((AVG(ms.spend) - AVG(b.baseline_spend))
           / NULLIF(AVG(b.baseline_spend), 0) * 100)::NUMERIC, 1
    )                                               AS pct_change
FROM monthly_spend ms 
JOIN baseline b
  ON ms.household_id = b.household_id
 AND ms.category_name = b.category_name
WHERE ms.adoption_stage != 'pre_adoption'
GROUP BY ms.category_name, ms.adoption_stage
ORDER BY ms.category_name, ms.adoption_stage;

-- Wallet share of remaining snack spend — the key metric for a meat snack company
WITH total_spend AS (
    SELECT household_id, month,
           SUM(spend) AS total_snack_spend
    FROM transactions
    GROUP BY household_id, month
),
category_spend AS (
    SELECT t.household_id, t.month, c.category_name, t.spend
    FROM transactions t
    JOIN categories c ON t.category_id = c.category_id
)
SELECT
    cs.category_name,
    h.is_glp1_user,
    ROUND(AVG(cs.spend / NULLIF(ts.total_snack_spend, 0) * 100)::NUMERIC, 2) AS avg_wallet_share_pct,
    -- Window function: rank categories by wallet share within each GLP-1 group
    RANK() OVER (
        PARTITION BY h.is_glp1_user
        ORDER BY AVG(cs.spend / NULLIF(ts.total_snack_spend, 0)) DESC
    ) AS wallet_share_rank
FROM category_spend cs
JOIN total_spend   ts ON cs.household_id = ts.household_id AND cs.month = ts.month
JOIN households     h ON cs.household_id = h.household_id
GROUP BY cs.category_name, h.is_glp1_user
ORDER BY h.is_glp1_user DESC, avg_wallet_share_pct DESC;