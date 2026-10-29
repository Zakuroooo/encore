# 1. The data

## What an event log is
An app writes one line every time a user does something: plays a song, presses thumbs-up, opens Settings.
Each line is an **event**. A list of all events in time order is an **event log**. Our log has 286,500 events.

One event looks like this (simplified):
```
time: 2018-10-01 00:01:57   user: 30   session: 29   page: NextSong   level: paid   song: "Rockpools"
```
- **user** (`userId`): who did it.
- **page**: what they did. `NextSong` = a song played. Other pages: `Thumbs Up`, `Add Friend`, `Roll Advert`
  (an ad played), `Upgrade`, `Downgrade`, `Cancel`, `Cancellation Confirmation`, and more (19 in total).
- **level**: the user's plan at that moment, `free` or `paid`.
- **session**: one sitting of using the app. Session 29 of user 30 is everything user 30 did in one go.
- **ts** (time) is stored as milliseconds since 1 Jan 1970, a common way computers store time. We convert it.

## Where it comes from
Udacity made a fake music app called **Sparkify** and a program that simulates users. We use the "mini"
file (128 MB). It is **simulated**: no real people. Always say this in an interview.

## Users, sessions, days
After cleaning: **225 users**, **3,175 sessions**, **278,150 events**, **61 days** (Oct 1 – Nov 30, 2018).

## What "churn" means here
**Churn** = a user leaves. In this project, churn has one exact meaning: the user reached the page
**Cancellation Confirmation** (the last step of cancelling). 52 of 225 users did that.

Important: some users stop coming without ever cancelling. Our churn label does not count them.
We measured it: at our test date, 13 users cancelled, and 15 more just went silent.

## Why we clean the data
- 8,346 events had no user (people not logged in). We cannot tie them to anyone, so we drop them.
- The log really ends on Nov 30. There were 4 stray events after that. We drop them, so time windows are honest.
- 3 users had a sign-up time *after* their first song. Impossible, so we fix it to their first event.
- We drop first and last names. We never need them.

Every one of these is counted and checked by `tests/check_quality.py`. If a number changes, the pipeline stops.

## Say it in one line
"It is a simulated event log of a music app: 278 thousand clean events from 225 users over 61 days, and churn means
the user confirmed cancellation."
