-- User-level features for the churn model, computed ONLY from events before :cutoff.
-- Label = the user reached Cancellation Confirmation in the :horizon days after :cutoff.
-- Who is scored: users seen before the cutoff who had not cancelled before it.
-- Leakage guards: no event at or after the cutoff is used for any feature, and the Cancel /
-- Cancellation Confirmation pages are never used as features. tests/test_leakage.py proves it:
-- it deletes every event after the cutoff, rebuilds, and checks every feature is unchanged.
WITH params AS (
    SELECT CAST(? AS TIMESTAMP) AS cutoff, CAST(? AS INTEGER) AS horizon
),
eligible AS (
    SELECT u.user_id, u.gender, u.registration_ts, u.churn_ts
    FROM clean.users u, params p
    WHERE u.first_event_ts < p.cutoff
      AND (u.churn_ts IS NULL OR u.churn_ts >= p.cutoff)
),
past AS (
    SELECT e.* FROM clean.events e JOIN eligible USING (user_id), params p
    WHERE e.event_ts < p.cutoff
),
agg AS (
    SELECT user_id,
           count(*) FILTER (WHERE page = 'NextSong')                                AS songs,
           count(DISTINCT session_id)                                               AS sessions,
           count(DISTINCT event_date)                                               AS active_days,
           -- last 14 days vs the 14 days before that: is listening going up or down?
           count(*) FILTER (WHERE page = 'NextSong'
                            AND event_ts >= (SELECT cutoff FROM params) - INTERVAL 14 DAY)  AS songs_last14,
           count(*) FILTER (WHERE page = 'NextSong'
                            AND event_ts <  (SELECT cutoff FROM params) - INTERVAL 14 DAY
                            AND event_ts >= (SELECT cutoff FROM params) - INTERVAL 28 DAY)  AS songs_prev14,
           count(*) FILTER (WHERE page = 'Thumbs Up')                               AS thumbs_up,
           count(*) FILTER (WHERE page = 'Thumbs Down')                             AS thumbs_down,
           count(*) FILTER (WHERE page = 'Add Friend')                              AS friends,
           count(*) FILTER (WHERE page = 'Add to Playlist')                         AS playlist_adds,
           count(*) FILTER (WHERE page = 'Roll Advert')                             AS ads,
           count(*) FILTER (WHERE page = 'Error')                                   AS errors,
           count(*) FILTER (WHERE page = 'Help')                                    AS help_visits,
           count(*) FILTER (WHERE page = 'Downgrade')                               AS downgrade_page_visits,
           count(*) FILTER (WHERE page = 'Submit Downgrade')                        AS downgrades,
           count(*) FILTER (WHERE page = 'Settings')                                AS settings_visits,
           arg_max(level, event_seq) = 'paid'                                        AS is_paid_now,
           max(event_ts)                                                            AS last_ts,
           arg_max(device, event_seq)                                                AS device
    FROM past GROUP BY user_id
),
sess AS (
    -- sessions are rebuilt from past events only: a session still running at the cutoff counts
    -- with the part played so far. (Using clean.sessions and dropping sessions that END after the
    -- cutoff would let the future decide which sessions are kept - a small leak.)
    SELECT user_id, avg(minutes) AS avg_session_minutes
    FROM (SELECT user_id, session_id,
                 date_diff('second', min(event_ts), max(event_ts)) / 60.0 AS minutes
          FROM past GROUP BY 1, 2)
    GROUP BY 1
)
SELECT
    a.user_id,
    date_diff('day', e.registration_ts, p.cutoff)               AS tenure_days,
    date_diff('hour', a.last_ts, p.cutoff) / 24.0               AS days_since_last_event,
    a.active_days,
    a.sessions,
    a.songs,
    a.songs_last14,
    -- ratio > 1 means listening grew; +1 on both sides so new users do not divide by zero
    (a.songs_last14 + 1.0) / (a.songs_prev14 + 1.0)             AS listening_trend,
    coalesce(s.avg_session_minutes, 0)                          AS avg_session_minutes,
    100.0 * a.thumbs_up   / greatest(a.songs, 1)                AS thumbs_up_per_100,
    100.0 * a.thumbs_down / greatest(a.songs, 1)                AS thumbs_down_per_100,
    100.0 * a.friends     / greatest(a.songs, 1)                AS friends_per_100,
    100.0 * a.playlist_adds / greatest(a.songs, 1)              AS playlist_adds_per_100,
    100.0 * a.ads         / greatest(a.songs, 1)                AS ads_per_100,
    a.errors,
    a.help_visits,
    a.downgrade_page_visits,
    a.downgrades,
    a.settings_visits,
    a.is_paid_now::INT                                          AS is_paid_now,
    (e.gender = 'M')::INT                                       AS is_male,
    (a.device IN ('Mac', 'iOS'))::INT                           AS is_apple_device,
    -- the label
    (e.churn_ts IS NOT NULL
     AND e.churn_ts < p.cutoff + INTERVAL (p.horizon) DAY)::INT AS churned
FROM agg a
JOIN eligible e USING (user_id)
LEFT JOIN sess s USING (user_id),
params p
ORDER BY a.user_id
