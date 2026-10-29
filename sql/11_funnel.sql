-- ANALYTICS: activation funnel.
-- Steps: signed up -> first song -> 10th song -> first friend added -> first paid event.
-- Who is in it: users whose first event in the log is on the FREE tier. Users already paying when the
-- log starts skipped the funnel before we could see it, so they are left out (count in quality notes).
-- "Signed up" = registered (every user has a registration date). Most registered before the log began,
-- so step 1 is "registered and seen on free tier", not "signed up inside the log".
-- Each step must happen at or after the step before it (an ordered funnel).
CREATE TABLE analytics.funnel AS
WITH base AS (
    SELECT * FROM clean.users WHERE first_level = 'free'
),
reached AS (
    SELECT
        count(*)                                                         AS s1_signed_up,
        count(*) FILTER (WHERE first_song_ts IS NOT NULL)                AS s2_first_song,
        count(*) FILTER (WHERE tenth_song_ts IS NOT NULL)                AS s3_ten_songs,
        count(*) FILTER (WHERE tenth_song_ts IS NOT NULL
                           AND first_friend_ts >= tenth_song_ts)         AS s4_friend_added,
        count(*) FILTER (WHERE tenth_song_ts IS NOT NULL
                           AND first_friend_ts >= tenth_song_ts
                           AND first_paid_ts >= first_friend_ts)         AS s5_paid
    FROM base
)
SELECT step_no, step, users,
       round(users / first_value(users) OVER (ORDER BY step_no), 4)      AS pct_of_start,
       round(users / lag(users) OVER (ORDER BY step_no), 4)              AS pct_of_previous
FROM (
    SELECT 1 AS step_no, 'Signed up (free)' AS step, s1_signed_up AS users FROM reached UNION ALL
    SELECT 2, 'First song',        s2_first_song   FROM reached UNION ALL
    SELECT 3, '10 songs',          s3_ten_songs    FROM reached UNION ALL
    SELECT 4, 'Added a friend',    s4_friend_added FROM reached UNION ALL
    SELECT 5, 'Became paid',       s5_paid         FROM reached
)
ORDER BY step_no;
