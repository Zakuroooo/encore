# 6. The churn model

## What we are trying to do
On a given date, give every user a **risk score**: how likely are they to cancel in the next 21 days?
Then the team can act on the riskiest users first.

> **Hinglish:** Churn model aaj tak ka data dekh kar har user ko ek risk score deta hai, ki agle 21 din mein woh cancel karega ya nahi, taaki pehle sabse risky logon par dhyan de sakein.

## Words
- **Label** (the answer we want to predict): 1 if the user confirmed cancellation within 21 days after the date, else 0.
- **Features** (the clues): 21 numbers per user, from events **before** the date only. Examples:
  songs played, sessions, days since last visit, thumbs-down per 100 songs, Help page visits, plan.
- **Snapshot / cutoff**: the date on which we "freeze" what we know.

## The time-based split
We pretend we are standing on a date and cannot see the future.
- **Train**: snapshot Oct 20. Features from before Oct 20; label = cancelled between Oct 20 and Nov 10. 185 users, 18 cancellers.
- **Test**: snapshot Nov 10. Features from before Nov 10; label = cancelled between Nov 10 and Dec 1. 184 users, 13 cancellers.

The model learns on the first, and is judged **once** on the second, a later period it never saw.
This copies real life: you train on the past and use the model on the future.
A random split would mix the same weeks into train and test and look better than reality.

## Two models
1. **Logistic regression**: adds up the features, each with a weight, and squashes the total into 0–1.
   Easy to explain: a positive weight means "more of this = more risk".
2. **Gradient boosting**: many small decision trees ("if Help visits > 2 and thumbs-up rate < 3 then …"),
   each one fixing the mistakes of the ones before. Can find patterns logistic regression misses, but
   overfits easily on small data.

Both use `class_weight="balanced"`: cancellers are only ~10% of users, so each canceller counts more in training.
Side effect: the scores come out too high (average 0.41 when the real rate is 0.07). So we use them to
**rank** users, never as "41% chance".

## Choosing the model without cheating
We choose using **cross-validation on the training users only**: split the training users into 5 parts, train on
4, check on the 5th, repeat. Logistic regression scored PR-AUC 0.186 vs 0.126 for boosting, so it was chosen
*before* we looked at the test set.

## What the model leans on
Measured by scrambling one feature at a time (on held-out training users) and seeing how much the score drops.
Top clues: Help page visits (more = more risk), thumbs-up per 100 songs (more = less risk), being on the paid
plan (more risk: only paid users have something to cancel), Settings visits (more risk), thumbs-down rate (more risk).
Careful: with 18 training cancellers this list changes a lot if the dates move. Treat it as hints, not facts.

## Say it in one line
"I trained on users as of Oct 20, tested once on users as of Nov 10, picked logistic regression on training
cross-validation, and used the scores only as a ranking."
