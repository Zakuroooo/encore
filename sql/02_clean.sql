-- CLEAN layer: one row per real user event, typed, with no names.

-- Step 1: keep only events that belong to a user. Logged-out and guest events have an empty userId,
-- so they cannot be tied to anyone and are dropped (their count is reported by the quality checks).
-- First and last names are dropped too: we never need them, and they look like personal data.
CREATE TABLE clean.events AS
WITH user_events AS (
    SELECT *
    FROM raw.events
    WHERE userId IS NOT NULL AND userId <> ''
),
-- Step 2: remove exact duplicate rows (same user, session, item number, time and page).
deduped AS (
    SELECT DISTINCT
        userId, sessionId, itemInSession, ts, page, level, auth, status, method,
        gender, registration, location, userAgent, song, artist, length
    FROM user_events
)
-- Step 3: give columns clear names and proper types. ts and registration are milliseconds since 1970 (UTC).
SELECT
    userId                                   AS user_id,
    sessionId                                AS session_id,
    itemInSession                            AS item_in_session,
    make_timestamp(ts * 1000)                AS event_ts,
    CAST(make_timestamp(ts * 1000) AS DATE)  AS event_date,
    page,
    level,
    auth,
    status,
    gender,
    make_timestamp(registration * 1000)      AS registration_ts,
    -- "Boston-Cambridge-Newton, MA-NH" -> "MA-NH": the part after the last comma
    trim(split_part(location, ',', -1))      AS state,
    CASE
        WHEN userAgent LIKE '%iPhone%' OR userAgent LIKE '%iPad%' THEN 'iOS'
        WHEN userAgent LIKE '%Macintosh%'                         THEN 'Mac'
        WHEN userAgent LIKE '%Windows%'                           THEN 'Windows'
        WHEN userAgent LIKE '%Linux%'                             THEN 'Linux'
        ELSE 'Other'
    END                                      AS device,
    song,
    artist,
    length                                   AS song_seconds
FROM deduped;
