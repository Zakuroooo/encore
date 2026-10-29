# Data

## Source
| | |
|---|---|
| Name | Sparkify mini event log (`mini_sparkify_event_data.json`) |
| Publisher | Udacity (Data Scientist Nanodegree capstone) |
| Where | `https://udacity-dsnd.s3.amazonaws.com/sparkify/mini_sparkify_event_data.json` (public S3 bucket, no login) |
| Size | 128,477,301 bytes, 286,500 lines (one JSON event per line) |
| Fingerprint | SHA-256 `94620a8c00036956d43f619f85bdded3bf8cc8996a152a9df61f8c3d6e154f97` (S3 Last-Modified 2019-02-02) |
| What it is | **Simulated** listening events for a made-up music app, "Sparkify". Not real people. |

`scripts/download.py` downloads it and refuses to continue if the size or SHA-256 differs.

## Licence: what we found, and what we do
- We found **no licence or terms of use** attached to the file: none on the S3 object, and none on any Udacity
  page we could find (checked 2026-10-29). Community write-ups say the logs come from an event simulator
  (eventsim) and that the file is given to Nanodegree students.
- No licence means no permission to redistribute. So:
  - the raw file is **never committed** (`data/` is in `.gitignore`); anyone re-running downloads it from Udacity;
  - only **aggregate tables** (counts, rates, model scores per group) are published in `outputs/`;
    a test (`tests/test_outputs.py`) fails if any published file has a `user_id` column;
  - first and last names, which look like personal data even though they are simulated, are dropped in the
    clean layer.

## What one row looks like
```
{"ts":1538352117000, "userId":"30", "sessionId":29, "page":"NextSong", "auth":"Logged In",
 "level":"paid", "itemInSession":50, "location":"Bakersfield, CA", "userAgent":"Mozilla/5.0 (Windows ...",
 "registration":1538173362000, "gender":"M", "artist":"Martha Tilston", "song":"Rockpools", "length":277.89, ...}
```
`ts` and `registration` are milliseconds since 1970 (UTC). `page` is what the user did. 19 page types
appear for logged-in users, from `NextSong` (228,108 events) down to `Cancellation Confirmation` (52).

## From raw to clean: every row accounted for
| Step | Rows | Why |
|---|---|---|
| Raw file | 286,500 | as downloaded |
| minus events with no user | −8,346 | 8,249 "Logged Out" + 97 "Guest" events have an empty `userId`, so they cannot be tied to anyone |
| minus events after Nov 30 | −4 | the log really ends on Nov 30. After it there are only 3 songs just after midnight on Dec 1 and 1 song on Dec 3 (nothing on Dec 2). Keeping them would make the last "21-day" window look 3 days longer than the data is |
| minus exact duplicates | −0 | checked, none found |
| **Clean events** | **278,150** | 225 users, 3,175 sessions, 61 days (Oct 1 – Nov 30, 2018) |

`tests/check_quality.py` re-derives this table on every run and **stops the pipeline** if any number changes.

## Known quirks and how they are handled
| Quirk | Size | Handling |
|---|---|---|
| Registration time is *after* the user's first logged-in event | 3 users (by 16–55 hours) | Registration set to the first event for them (`registration_fixed` flag, original kept in `registration_ts_raw`). The check pins the count at 3. |
| Two events with the same timestamp but different plan (the moment of an up/downgrade) | 4 user-moments | A unique `event_seq` decides "first"/"last" event, so every run gives the same answer. |
| The same `sessionId` number is used by different users | common | A session is always `(user_id, session_id)`, never `session_id` alone. |
| Most users registered before the log starts | registrations from Mar 18, 2018 | The funnel's step 1 is "seen on the free plan", not "signed up inside the log" (see METRICS.md). |
| No money anywhere in the data | – | RFM's "M" is songs played; the decision sizing uses a stated, assumed price. |

## Limits of this data (read before trusting any number)
1. **Small.** 225 users, 52 cancellations in total; only 13 cancellations in the test window. Every model and
   segment number has a wide error band.
2. **Simulated.** Behaviour comes from a simulator, so patterns may be cleaner or stranger than a real app's.
3. **Short.** 61 days. Nothing seasonal, no long-term retention.
4. **"Churn" is only the cancel click.** 15 users at the test snapshot went completely silent without
   cancelling: more than the 13 who cancelled (`outputs/snapshot_outcomes.csv`).
