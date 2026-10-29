-- ANALYTICS: what happened to users in the 21 days after the test snapshot (test_cutoff, Nov 10).
-- The project's churn label is "clicked Cancellation Confirmation". Some users never cancel:
-- they just stop coming. This table counts both, so the label's blind spot has a size.
--   cancelled   = reached Cancellation Confirmation in the 21 days
--   went_silent = did not cancel AND had zero events in the 21 days
--   stayed      = everyone else (active at least once in the 21 days, did not cancel)
CREATE TABLE analytics.snapshot_outcomes AS
WITH p AS (SELECT test_cutoff::TIMESTAMP AS t0,
                  test_cutoff::TIMESTAMP + INTERVAL (horizon_days) DAY AS t1 FROM raw.params),
eligible AS (
    SELECT u.user_id FROM clean.users u, p
    WHERE u.first_event_ts < p.t0 AND (u.churn_ts IS NULL OR u.churn_ts >= p.t0)
),
tier AS (
    SELECT e.user_id, arg_max(e.level, e.event_seq) AS plan
    FROM clean.events e JOIN eligible USING (user_id), p
    WHERE e.event_ts < p.t0 GROUP BY 1
),
window_activity AS (
    SELECT e.user_id, count(*) AS events_in_window
    FROM clean.events e JOIN eligible USING (user_id), p
    WHERE e.event_ts >= p.t0 AND e.event_ts < p.t1 GROUP BY 1
),
labelled AS (
    SELECT t.plan,
           CASE WHEN u.churn_ts IS NOT NULL AND u.churn_ts < p.t1 THEN 'cancelled'
                WHEN coalesce(w.events_in_window, 0) = 0         THEN 'went_silent'
                ELSE 'stayed' END AS outcome
    FROM eligible JOIN clean.users u USING (user_id) JOIN tier t USING (user_id)
    LEFT JOIN window_activity w USING (user_id), p
)
SELECT coalesce(plan, 'all') AS plan, outcome, count(*) AS users,
       round(count(*) / sum(count(*)) OVER (PARTITION BY coalesce(plan, 'all')), 4) AS share
FROM labelled
GROUP BY GROUPING SETS ((plan, outcome), (outcome))
ORDER BY plan, outcome;
