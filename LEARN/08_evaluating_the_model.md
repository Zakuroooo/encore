# 8. Evaluating the model honestly

## Why not accuracy
Only 13 of 184 test users cancelled (7.1%). A "model" that says *nobody cancels* is 92.9% accurate and useless.
So we need measures that focus on finding the cancellers.

## Precision and recall
Say we contact the users the model ranks highest.
- **Precision** = of the people we contacted, how many were really going to cancel?
- **Recall** = of all the people who cancelled, how many did we contact?

There is a trade-off: contact more people → recall goes up, precision usually goes down.

## PR-AUC
Draw precision (y) against recall (x) as you contact more and more users from the top of the ranking.
**PR-AUC** is the area under that curve, one number for the whole ranking. 1.0 = perfect.
**The key fact: a random ranking scores about the churn rate** (here 0.071), not 0.5. So always compare with that.

> **Hinglish:** PR-AUC batata hai ki risk ki list mein upar wale log sach mein cancel karne wale hain ya nahi; random list ka PR-AUC churn rate jitna hi hota hai, isliye usse compare karna zaroori hai.

Our result: logistic regression **0.215** vs random 0.071.

Why PR-AUC and not ROC-AUC? ROC-AUC also rewards correctly ranking the many non-cancellers, so it can look good
when cancellers are rare. PR-AUC only cares about how well the cancellers are found. (We report both.)

## Recall@top-k and lift
The team cannot call everyone. Assume they can contact the top **20%** (37 users).
- **Recall@top-20%** = cancellers among those 37 ÷ all 13 cancellers. Ours: 5 of 13 = 38.5%.
- **Lift** = precision in the top 20% ÷ overall churn rate. Ours: 1.91 (almost twice as good as random picking).

## Is 5 better than luck? (permutation p-value)
We shuffle the users into a random order 10,000 times and count cancellers in the top 37 each time.
On average random finds **2.63**. In **9.5%** of shuffles random finds 5 or more. So p = 0.095.
The usual bar is p < 0.05. We do not pass it. **Honest conclusion: a weak signal, not proven.**

## Bootstrap range
Resample the 184 test users with replacement 2,000 times and recompute PR-AUC each time. The middle 95% of
results is the range: **0.07 to 0.44**. The bottom of that range is about random. This width is what 13 cancellers
buys you.

## Robustness across dates
Moving the dates by 2 days changed which model won. So we re-ran the whole procedure for 7 test dates.
The chosen model beat the random average on all 7, but reached p < 0.05 on only 2 of 7.

## The simple rule that failed
"Days since last visit" (no ML) caught **1** canceller, worse than random. Cancellers were active right up to
the moment they clicked Cancel. But for "cancelled **or** went silent" this same rule was the best ranker
(PR-AUC 0.227 vs base rate 0.152). Lesson: the label you choose decides which clues work.

## Calibration
Calibration asks: when the model says 30%, do 30% of those people really leave? Ours does not (it says ~41% on
average; real rate is 7%), because of the class weighting. Fine for ranking, wrong as a probability.

## Say it in one line
"On 13 test cancellers, the model found 5 in its top 20% against 2.6 by chance, PR-AUC 0.215 against 0.071; p was
0.095, so I report it as a weak, unproven signal."
