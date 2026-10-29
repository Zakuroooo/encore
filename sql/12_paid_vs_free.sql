-- ANALYTICS: how free and paid listeners behave, per 100 songs so tiers of different size compare fairly.
-- Tier = the level on each event, so a user who upgraded counts in free before and paid after.
CREATE TABLE analytics.paid_vs_free AS
WITH per_level AS (
    SELECT level,
           count(DISTINCT user_id)                              AS users,
           count(*) FILTER (WHERE page = 'NextSong')            AS songs,
           count(*) FILTER (WHERE page = 'Thumbs Up')           AS thumbs_up,
           count(*) FILTER (WHERE page = 'Thumbs Down')         AS thumbs_down,
           count(*) FILTER (WHERE page = 'Roll Advert')         AS ads,
           count(*) FILTER (WHERE page = 'Add Friend')          AS friends,
           count(*) FILTER (WHERE page = 'Add to Playlist')     AS playlist_adds,
           count(*) FILTER (WHERE page = 'Error')               AS errors
    FROM clean.events
    GROUP BY level
),
sess AS (
    SELECT level, median(minutes) AS median_session_minutes, avg(n_songs) AS songs_per_session
    FROM clean.sessions GROUP BY level
)
SELECT p.level, p.users, p.songs,
       round(100.0 * thumbs_up / songs, 2)      AS thumbs_up_per_100_songs,
       round(100.0 * thumbs_down / songs, 2)    AS thumbs_down_per_100_songs,
       round(100.0 * ads / songs, 2)            AS ads_per_100_songs,
       round(100.0 * friends / songs, 2)        AS friends_per_100_songs,
       round(100.0 * playlist_adds / songs, 2)  AS playlist_adds_per_100_songs,
       round(s.median_session_minutes, 1)       AS median_session_minutes,
       round(s.songs_per_session, 1)            AS songs_per_session
FROM per_level p JOIN sess s USING (level)
ORDER BY p.level;

-- ANALYTICS: downgrades and cancellations.
-- Tier at cancel = the level on the Cancellation Confirmation event.
CREATE TABLE analytics.churn_summary AS
WITH cancels AS (
    SELECT user_id, level AS tier_at_cancel FROM clean.events WHERE page = 'Cancellation Confirmation'
),
ever AS (
    SELECT user_id,
           bool_or(level = 'paid') AS ever_paid,
           bool_or(level = 'free') AS ever_free
    FROM clean.events GROUP BY 1
)
SELECT
    (SELECT count(*) FROM clean.users)                                         AS users,
    (SELECT count(*) FROM clean.users WHERE churned)                           AS churned_users,
    round((SELECT avg(churned::INT) FROM clean.users), 4)                      AS churn_rate,
    (SELECT count(*) FROM cancels WHERE tier_at_cancel = 'paid')               AS churned_while_paid,
    (SELECT count(*) FROM cancels WHERE tier_at_cancel = 'free')               AS churned_while_free,
    (SELECT count(*) FROM ever WHERE ever_paid)                                AS ever_paid_users,
    (SELECT count(*) FROM clean.users WHERE upgraded)                          AS upgraded_users,
    (SELECT count(*) FROM clean.users WHERE downgraded)                        AS downgraded_users,
    -- of users who were ever paid, how many submitted a downgrade
    round((SELECT count(*) FROM clean.users WHERE downgraded) /
          (SELECT count(*) FROM ever WHERE ever_paid), 4)                       AS downgrade_rate_of_ever_paid,
    -- churn rate among users who ever submitted a downgrade vs those who did not
    round((SELECT avg(churned::INT) FROM clean.users WHERE downgraded), 4)     AS churn_rate_if_downgraded,
    round((SELECT avg(churned::INT) FROM clean.users WHERE NOT downgraded), 4) AS churn_rate_if_not_downgraded;

-- Weekly cancellations, to see if churn is steady or bunched.
CREATE TABLE analytics.weekly_cancels AS
SELECT date_trunc('week', event_date)::DATE AS week,
       count(*)                              AS cancellations,
       count(*) FILTER (WHERE level = 'paid') AS paid_cancellations
FROM clean.events WHERE page = 'Cancellation Confirmation'
GROUP BY 1 ORDER BY 1;
