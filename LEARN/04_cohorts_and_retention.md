# 4. Cohorts and retention

## Cohort
A **cohort** is a group of users who started at the same time. Here: the week of their **first event in the log**.
Everyone first seen in the week of Oct 1 is the "Oct 1 cohort" (162 users).

> **Hinglish:** Cohort matlab ek hi hafte mein aaye logon ka group, aur phir hum dekhte hain ki har hafte unmein se kitne wapas aate hain.

Why cohorts? If you only look at "total users this week", new users can hide that old users are leaving.
Cohorts compare like with like.

## Retention
**Week-k retention** = of the cohort, the share who did anything in the k-th week after their start week.
Week 0 is always 100% (by definition everyone was active in their first week).

## The retention table (a "triangle")
Rows = cohorts, columns = weeks since start, cells = retention. It is a triangle because newer cohorts have had
fewer weeks to be measured. The dashboard draws it as a heatmap: darker = more retained.

Oct 1 cohort: 100% → 76.5% (week 1) → … → **58.6%** (week 7).

## The retention curve
Take one cohort's row and draw it as a line: week on the x-axis, % still active on the y-axis.
A good curve **drops and then flattens**: the flat part is your loyal core. A curve that keeps falling to zero
means nobody sticks.

> **Hinglish:** Retention curve pehle girti hai, phir agar seedhi (flat) ho jaaye toh samjho app ke paas pakke users hain; agar girti hi rahe toh sab dheere-dheere chale jaate hain.

Paid vs free (Oct 1 cohort, split by plan on their first event): week 7 paid **72.7%** (of 33) vs free
**55.0%** (of 129). Paid users stay more, as you would expect.

## Traps we avoided
1. **Partial last week.** Nov 26–30 has 5 of 7 days. Fewer days = fewer chances to be active = a fake drop. We leave it out.
2. **The first cohort is special.** Everyone already using the app on Oct 1 lands in it. It is not "new users".
3. **Tiny cohorts.** Some later cohorts have 2–12 users. One person moves a cell by 8–50 points. Treat them as noise.

## Say it in one line
"I grouped users by the week they first appeared and tracked what share came back each week; the first cohort keeps
59% by week 7, and paid users keep 73% against 55% for free."
