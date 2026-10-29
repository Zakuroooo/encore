-- ANALYTICS: RFM segments, measured at the test snapshot (Nov 12) using only events before it,
-- then compared with who actually cancelled in the 21 days after. This makes RFM a forward-looking
-- test, not a look back at people who already left.
-- R = days since last event, F = sessions, M = songs played. There is no money in this data,
-- so M is listening volume (a stand-in for value), not revenue.
-- Each of R, F, M gets a score 1-3 by tertile (3 = best: recent, frequent, heavy).
CREATE TABLE analytics.rfm_users AS
WITH p AS (SELECT * FROM raw.params),
eligible AS (
    -- users seen before the snapshot who had not cancelled before it
    SELECT u.user_id FROM clean.users u, p
    WHERE u.first_event_ts < p.test_cutoff
      AND (u.churn_ts IS NULL OR u.churn_ts >= p.test_cutoff)
),
base AS (
    SELECT e.user_id,
           date_diff('day', max(e.event_ts), any_value(p.test_cutoff)::TIMESTAMP) AS recency_days,
           count(DISTINCT e.session_id)                                       AS frequency_sessions,
           count(*) FILTER (WHERE e.page = 'NextSong')                        AS monetary_songs,
           arg_max(e.level, e.event_ts)                                       AS tier_at_snapshot
    FROM clean.events e JOIN eligible USING (user_id), p
    WHERE e.event_ts < p.test_cutoff
    GROUP BY e.user_id
),
scored AS (
    SELECT *,
           4 - ntile(3) OVER (ORDER BY recency_days)       AS r_score,  -- fewest days = 3
           ntile(3) OVER (ORDER BY frequency_sessions)     AS f_score,
           ntile(3) OVER (ORDER BY monetary_songs)         AS m_score
    FROM base
)
SELECT s.*,
       CASE
           WHEN r_score = 3 AND f_score + m_score >= 5 THEN 'Champions'
           WHEN r_score >= 2 AND f_score + m_score >= 4 THEN 'Loyal'
           WHEN r_score = 1 AND f_score + m_score >= 4 THEN 'At risk (was strong, gone quiet)'
           WHEN r_score >= 2                           THEN 'Casual'
           ELSE                                             'Hibernating'
       END AS segment,
       -- outcome: cancelled in the 21 days after the snapshot
       (u.churn_ts IS NOT NULL
        AND u.churn_ts < (SELECT test_cutoff + INTERVAL (horizon_days) DAY FROM raw.params)) AS churned_next_21d
FROM scored s JOIN clean.users u USING (user_id);

CREATE TABLE analytics.rfm_segments AS
SELECT segment,
       count(*)                                   AS users,
       count(*) FILTER (WHERE tier_at_snapshot = 'paid') AS paid_users,
       round(median(recency_days), 1)             AS median_recency_days,
       round(median(frequency_sessions), 1)       AS median_sessions,
       round(median(monetary_songs), 0)           AS median_songs,
       count(*) FILTER (WHERE churned_next_21d)   AS churned_next_21d,
       round(avg(churned_next_21d::INT), 4)       AS churn_rate_next_21d
FROM analytics.rfm_users
GROUP BY segment
ORDER BY churn_rate_next_21d DESC;
