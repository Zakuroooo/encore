# A/B test design: a save offer on the Cancel page

Written **before** any result exists. The decision rule below is fixed now and is not changed after the data
comes in. Numbers marked *(data)* come from `outputs/`; numbers marked *(assumed)* are choices we made.

## Why this test
- 52 of 52 users who opened the Cancel page confirmed, median 25.5 seconds later *(data)*. There is no save step.
- Everyone who reaches that page is about to leave, so an offer there wastes almost no discounts
  (unlike an e-mail to model-flagged users, which needs a 46% save rate to break even *(data + assumed)*).

## Hypothesis
Showing paid users a one-time offer (50% off next month) on the Cancel page increases the share who are
**still paying 30 days later**, by at least 5 percentage points.

## Design
| Item | Choice |
|---|---|
| Who | **paid** users who open the Cancel page for the first time in the test period |
| Unit of randomisation | user (by a hash of `user_id`), 50/50, at the moment they open the page |
| Control | today's flow: Cancel → Confirm |
| Treatment | Cancel → offer screen ("Stay for $4.99 next month") → accept, or continue to Confirm |
| Limit | one offer per user per 12 months, so nobody can farm discounts by clicking Cancel |
| Primary metric | **still paid at day 30** after first opening the Cancel page (yes/no per user) |
| Secondary | confirmed cancellation within 7 days; songs played in the 30 days |
| Guardrails | (1) Cancel-page openings per 1,000 paid users must not rise by more than 20% vs the 4 weeks before (a sign of gaming); (2) net revenue per user who opened the page at day 60, treatment ≥ control; (3) support complaints/refund requests not up |

## Sample size *(computed in `analysis/decision.py`, `outputs/decision.json`)*
- Control "still paid at day 30" assumed at **2%** *(assumed: in this log 0 of 52 came back, but a small
  allowance avoids a 0% baseline that would make the maths unrealistic)*.
- Smallest effect worth detecting: **+5 points** (2% → 7%), the "low" save-rate scenario.
- Two-sided α = 0.05, power = 0.80 → **269 users per group, 538 in total**.
- At 10,000 paid subscribers, about 1,148 open the Cancel page per month *(data: 8.0% of paid users
  cancelled in the 21-day test window, scaled to 30 days)* → about **2 weeks** of traffic. Run for **4 full
  weeks** anyway, so every weekday is covered twice and the day-30 outcome exists for everyone.
- This test **cannot be run on the Sparkify sample** (31 paid cancellers in 61 days). It is a plan for the live app.

## Decision rule (fixed now)
After the planned sample is reached and every user has a full 30 days (no peeking, no early stop):
1. **Ship** if the treatment − control difference in "still paid at day 30" has a 95% interval entirely
   above 0, **and** no guardrail fails, **and** net revenue per user at day 60 is not lower in treatment.
2. **Do not ship** if the interval includes 0 or any guardrail fails. Write up the result anyway.
3. **Re-test** (new offer, not a re-run of the same one) if the effect is positive but smaller than 5 points,
   since the test was not sized to detect that reliably.
The analysis is a two-proportion z-test on the primary metric; secondary metrics are reported, not used to decide.

## Threats, and what we do about them
| Threat | Handling |
|---|---|
| Users see the offer, accept, and cancel next month anyway | Primary metric is day 30, plus revenue at day 60 |
| Offer leaks (users share "click Cancel to get 50% off") | One offer per year per user; guardrail 1 |
| Novelty effect | 4-week run; compare first vs second half as a check (reported, not used to decide) |
| Free users | Not in this test: cancelling a free account loses no subscription. A separate test could offer an ad-free week |
| Silent leavers | Not reached by this test at all (they never click Cancel); see MEMO next steps |
