-- ANALYTICS: weekly cohort retention.
-- Cohort = the week (Monday start) of a user's FIRST event in the log.
-- Week k retention = share of the cohort with any event in the k-th week after their cohort week.
-- Caveat: the log starts Oct 1, so the first cohort holds everyone who was already a listener.
-- Later cohorts are users first seen later: mostly new or returning-after-a-break listeners.
CREATE TABLE analytics.cohort_retention AS
WITH firsts AS (
    SELECT user_id, date_trunc('week', min(event_date))::DATE AS cohort_week
    FROM clean.events GROUP BY 1
),
activity AS (
    SELECT DISTINCT user_id, date_trunc('week', event_date)::DATE AS active_week
    FROM clean.events
),
sizes AS (
    SELECT cohort_week, count(*) AS cohort_users FROM firsts GROUP BY 1
),
last_week AS (
    SELECT max(date_trunc('week', event_date))::DATE AS w FROM clean.events
)
SELECT f.cohort_week,
       s.cohort_users,
       date_diff('week', f.cohort_week, a.active_week) AS week_number,
       count(DISTINCT a.user_id)                       AS active_users,
       round(count(DISTINCT a.user_id) / s.cohort_users, 4) AS retention
FROM firsts f
JOIN activity a USING (user_id)
JOIN sizes s USING (cohort_week)
-- the last log week is partial (Dec 3 only), so it is left out to avoid a fake drop
WHERE a.active_week < (SELECT w FROM last_week)
GROUP BY 1, 2, 3
ORDER BY 1, 3;

-- Retention curve for paid vs free: the first cohort only (Oct 1 week), split by tier at first event.
-- This is the biggest, cleanest group: everyone was observed from the same start date.
CREATE TABLE analytics.retention_by_tier AS
WITH first_cohort AS (
    SELECT user_id, first_level AS tier
    FROM clean.users
    WHERE date_trunc('week', first_event_ts) = (SELECT date_trunc('week', min(first_event_ts)) FROM clean.users)
),
sizes AS (
    SELECT tier, count(*) AS cohort_users FROM first_cohort GROUP BY 1
),
activity AS (
    SELECT DISTINCT user_id, date_trunc('week', event_date)::DATE AS active_week FROM clean.events
),
start_week AS (SELECT min(active_week) AS w0, max(active_week) AS w_last FROM activity)
SELECT f.tier, s.cohort_users,
       date_diff('week', (SELECT w0 FROM start_week), a.active_week) AS week_number,
       count(DISTINCT f.user_id)                                     AS active_users,
       round(count(DISTINCT f.user_id) / s.cohort_users, 4)          AS retention
FROM first_cohort f
JOIN activity a USING (user_id)
JOIN sizes s USING (tier)
WHERE a.active_week < (SELECT w_last FROM start_week)
GROUP BY 1, 2, 3
ORDER BY 1, 3;
