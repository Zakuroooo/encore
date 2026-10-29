-- ANALYTICS: daily, weekly and monthly active users, and stickiness.
-- "Active" = the user did any logged-in event that day (a song, a page view, anything).

-- One row per calendar day: DAU, plus the rolling 28-day active users ending that day ("MAU").
-- MAU needs 28 full days of history, so it is NULL for the first 27 days of the log.
CREATE TABLE analytics.daily_active AS
WITH days AS (
    SELECT DISTINCT event_date AS day FROM clean.events
),
user_days AS (
    SELECT DISTINCT user_id, event_date, level FROM clean.events
),
dau AS (
    SELECT event_date AS day,
           count(DISTINCT user_id)                                AS dau,
           count(DISTINCT user_id) FILTER (WHERE level = 'paid')  AS dau_paid,
           count(DISTINCT user_id) FILTER (WHERE level = 'free')  AS dau_free
    FROM user_days GROUP BY 1
),
mau AS (
    SELECT d.day, count(DISTINCT u.user_id) AS mau_28d
    FROM days d
    JOIN user_days u ON u.event_date BETWEEN d.day - INTERVAL 27 DAY AND d.day
    GROUP BY 1
),
songs AS (
    SELECT event_date AS day, count(*) AS songs FROM clean.events WHERE page = 'NextSong' GROUP BY 1
)
SELECT dau.day, dau.dau, dau.dau_paid, dau.dau_free, songs.songs,
       -- the log ends at 01:11 on Dec 3, so the last day is not a full day: charts and medians skip it
       dau.day = (SELECT max(day) FROM days)                                                AS is_partial_day,
       CASE WHEN dau.day >= (SELECT min(day) FROM days) + INTERVAL 27 DAY THEN mau.mau_28d END AS mau_28d,
       CASE WHEN dau.day >= (SELECT min(day) FROM days) + INTERVAL 27 DAY
            THEN round(dau.dau / mau.mau_28d, 4) END                                         AS stickiness
FROM dau JOIN mau USING (day) LEFT JOIN songs USING (day)
ORDER BY dau.day;

-- One row per week (weeks start on Monday): weekly active users and songs.
-- The first and last weeks are partial (the log starts on a Monday, Oct 1, and ends mid-week).
CREATE TABLE analytics.weekly_active AS
SELECT date_trunc('week', event_date)::DATE                        AS week,
       count(DISTINCT event_date)                                   AS days_in_log,
       count(DISTINCT user_id)                                      AS wau,
       count(DISTINCT user_id) FILTER (WHERE level = 'paid')        AS wau_paid,
       count(*) FILTER (WHERE page = 'NextSong')                    AS songs
FROM clean.events
GROUP BY 1 ORDER BY 1;

-- Session length and depth, overall and by tier (tier = level at session start).
CREATE TABLE analytics.session_stats AS
SELECT coalesce(level, 'all')                    AS level,
       count(*)                                   AS sessions,
       round(median(minutes), 1)                  AS median_minutes,
       round(avg(minutes), 1)                     AS mean_minutes,
       round(median(n_songs), 1)                  AS median_songs,
       round(avg(n_songs), 1)                     AS mean_songs
FROM clean.sessions
GROUP BY ROLLUP (level)
ORDER BY level;
