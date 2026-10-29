# 3. Product metrics

## DAU, WAU, MAU
- **DAU** (daily active users): how many different users did anything on a day. Median here: 52.
- **WAU** (weekly active users): different users in a Monday–Sunday week. Week of Oct 1: 162.
- **MAU** (monthly active users): we use **the last 28 days** (4 full weeks, so every window has the same
  number of weekends). Here MAU is about 180–211.

"Different users" matters: one user playing 100 songs counts once.

## Stickiness = DAU ÷ MAU
"Of the people who used the app this month, what share came today?"
If MAU = 200 and DAU = 50, stickiness = 25%: the average monthly user comes about 1 day in 4.
Here the median is **24.8%**. Higher = a daily habit (messaging apps are very high; most apps are much lower).

## Funnel
A funnel counts how many users pass each step, in order:
signed up (free) → first song → 10 songs → added a friend → became paid.

Here: 177 → 177 → 174 → 133 → 71. So **40.1%** of free starters became paid.
The biggest drop is the last step: only 53.4% of users who added a friend went on to pay.

Two rules we used:
1. **Ordered**: each step must happen after the one before.
2. **Fair start**: only users first seen on the *free* plan. The 48 already paying when the log began skipped the funnel before we could see it.

Limit: most users signed up before the log started, so step 1 is really "seen on the free plan".

## Paid vs free, "per 100 songs"
Paid users play far more songs, so raw counts would always be bigger for paid. We divide by songs:
thumbs-down per 100 songs, ads per 100 songs, and so on. Now groups of different sizes compare fairly.
Free users hear 8.78 ads per 100 songs; paid users 0.13. Median paid session 246 minutes vs 98 for free.

## Downgrade and cancel rates
- 52 of 225 users cancelled (23.1%): 31 while paid, 21 while free.
- 29.7% of users who were ever paid submitted a downgrade.
- Surprise: users who downgraded cancelled *less* (18.4%) than those who did not (24.4%). So a downgrade is not
  an early warning sign here. Maybe a downgrade is the user "staying, but cheaper".

## The cancel flow
All 52 users who opened the Cancel page confirmed, a median of 25.5 seconds later. This one table became the
main recommendation (see file 9).

## Say it in one line
"Median DAU 52 and stickiness about 25%; 40% of free starters reach paid, and the cancel flow converts 100% in
under half a minute."
