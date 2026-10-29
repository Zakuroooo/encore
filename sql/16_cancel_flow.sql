-- ANALYTICS: the cancel flow. Page "Cancel" is the "are you sure?" screen; "Cancellation Confirmation"
-- is the final step. If almost everyone who opens Cancel goes on to confirm, and fast, the app has no
-- working "save" step today - and that screen reaches people who are certainly about to leave.
CREATE TABLE analytics.cancel_flow AS
WITH per_user AS (
    SELECT user_id,
           min(event_ts) FILTER (WHERE page = 'Cancel')                     AS cancel_ts,
           min(event_ts) FILTER (WHERE page = 'Cancellation Confirmation')  AS confirm_ts,
           arg_min(level, event_seq) FILTER (WHERE page = 'Cancel')          AS plan_at_cancel
    FROM clean.events
    GROUP BY 1
)
SELECT coalesce(plan_at_cancel, 'all')                                       AS plan,
       count(*)                                                              AS opened_cancel_page,
       count(*) FILTER (WHERE confirm_ts IS NOT NULL)                        AS confirmed,
       round(count(*) FILTER (WHERE confirm_ts IS NOT NULL) / count(*), 4)   AS confirm_rate,
       median(date_diff('second', cancel_ts, confirm_ts))                    AS median_seconds_to_confirm,
       max(date_diff('second', cancel_ts, confirm_ts))                       AS max_seconds_to_confirm
FROM per_user
WHERE cancel_ts IS NOT NULL
GROUP BY ROLLUP (plan_at_cancel)
ORDER BY plan;
