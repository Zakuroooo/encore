-- CLEAN layer, continued: one row per session and one row per user.

-- A session is identified by (user_id, session_id): the same session_id number can belong to two users.
CREATE TABLE clean.sessions AS
SELECT
    user_id,
    session_id,
    min(event_ts)                                             AS start_ts,
    max(event_ts)                                             AS end_ts,
    -- session length = first event to last event. A one-event session counts as 0 minutes.
    date_diff('second', min(event_ts), max(event_ts)) / 60.0  AS minutes,
    count(*)                                                  AS n_events,
    count(*) FILTER (WHERE page = 'NextSong')                 AS n_songs,
    -- level at the start of the session (free or paid)
    arg_min(level, event_seq)                                  AS level
FROM clean.events
GROUP BY user_id, session_id;

-- One row per user with the facts every metric needs.
CREATE TABLE clean.users AS
WITH song_rank AS (
    -- number each user's songs in time order, so we can find the 10th song
    SELECT user_id, event_ts,
           row_number() OVER (PARTITION BY user_id ORDER BY event_ts, session_id, item_in_session) AS song_no
    FROM clean.events
    WHERE page = 'NextSong'
),
tenth AS (
    SELECT user_id, event_ts AS tenth_song_ts FROM song_rank WHERE song_no = 10
)
SELECT
    e.user_id,
    any_value(e.gender)                                                    AS gender,
    -- Source quirk: 3 users have a registration time AFTER their first logged-in event (by 16-55 hours).
    -- A user cannot listen before signing up, so registration is set to the first event for them,
    -- and the original value is kept in registration_ts_raw. The quality checks pin this count at 3.
    least(min(e.registration_ts), min(e.event_ts))                         AS registration_ts,
    min(e.registration_ts)                                                 AS registration_ts_raw,
    min(e.registration_ts) > min(e.event_ts)                               AS registration_fixed,
    min(e.event_ts)                                                        AS first_event_ts,
    max(e.event_ts)                                                        AS last_event_ts,
    arg_min(e.level, e.event_seq)                                           AS first_level,
    arg_max(e.level, e.event_seq)                                           AS last_level,
    mode(e.device)                                                         AS device,
    mode(e.state)                                                          AS state,
    count(*)                                                               AS n_events,
    count(*) FILTER (WHERE e.page = 'NextSong')                            AS n_songs,
    count(DISTINCT e.session_id)                                           AS n_sessions,
    count(DISTINCT e.event_date)                                           AS n_active_days,
    -- funnel milestones (NULL = never reached)
    min(e.event_ts) FILTER (WHERE e.page = 'NextSong')                     AS first_song_ts,
    any_value(t.tenth_song_ts)                                             AS tenth_song_ts,
    min(e.event_ts) FILTER (WHERE e.page = 'Add Friend')                   AS first_friend_ts,
    min(e.event_ts) FILTER (WHERE e.level = 'paid')                        AS first_paid_ts,
    -- churn = the user reached the Cancellation Confirmation page
    min(e.event_ts) FILTER (WHERE e.page = 'Cancellation Confirmation')    AS churn_ts,
    count(*) FILTER (WHERE e.page = 'Cancellation Confirmation') > 0       AS churned,
    count(*) FILTER (WHERE e.page = 'Submit Downgrade') > 0                AS downgraded,
    count(*) FILTER (WHERE e.page = 'Submit Upgrade') > 0                  AS upgraded,
    count(*) FILTER (WHERE e.level = 'paid') > 0                           AS ever_paid
FROM clean.events e
LEFT JOIN tenth t ON t.user_id = e.user_id
GROUP BY e.user_id;
