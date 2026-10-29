# 10. 25 likely interview questions, with answers

Answer in this shape: **the point first, then one number, then the limit.**

### About the project
**1. Walk me through the project in one minute.**
A simulated music app's event log, 225 users over 61 days. I built a DuckDB SQL pipeline with quality checks,
measured engagement, a free-to-paid funnel, weekly cohort retention and RFM, then built a churn model with a
time-based split. The model was weak (5 of 13 cancellers found vs 2.6 by chance, not significant). The strongest
finding was that 100% of people who opened the Cancel page cancelled within about 25 seconds, so I recommended an
A/B-tested save offer there and sized it.

**2. Why this dataset?**
It is a public event log in the streaming domain with real product events (songs, ads, upgrades, cancels).
That lets me do product analytics end to end. Limit: it is simulated and small, which I say up front.

**3. What was the hardest part?**
Being honest about a weak model. Moving the dates by 2 days changed which model won, so instead of picking the
best-looking run I published a 7-date robustness table.

**4. What would you do with more time or data?**
Run on the full Sparkify log (thousands of cancellers) so the model can be tested properly; add "inactive for
14 days" as a second outcome; run the A/B test.

### SQL and data
**5. Why raw / clean / analytics layers?**
So every number can be traced back. If an analytics number looks wrong, I check clean, then raw. Raw is never edited.

**6. How do your quality checks "fail loudly"?**
18 checks print PASS/FAIL with the real number, and any FAIL exits with an error, which stops the pipeline and
CI. Example: clean rows must equal raw rows minus the no-user rows, the 4 stray tail rows, and duplicates.

**7. Tell me about a data problem you found.**
The log seemed to end on Dec 3, but daily volume showed it really ends on Nov 30, with only 4 stray events after.
My test window was 3 days shorter than it looked. I cut the data at Nov 30, moved both cutoffs, and added a check
that fails if any day inside the window is nearly empty.

**8. How do you get the "first plan" of a user in SQL?**
`arg_min(level, event_seq)`: the level on the user's earliest event. I use a unique `event_seq` rather than the
timestamp, because some events share a timestamp and the answer must be the same every run.

**9. Difference between `WHERE` and `FILTER` in your queries?**
`WHERE` removes rows before grouping. `FILTER` inside an aggregate counts only matching rows but keeps the others
for other columns, e.g. songs and thumbs-up counted in the same `GROUP BY`.

### Product metrics
**10. What is stickiness and what was yours?**
DAU divided by 28-day MAU: the share of this month's users who came today. Median 24.8%, so an average monthly
user comes about 1 day in 4.

**11. Why 28 days for MAU instead of a calendar month?**
28 days = 4 full weeks, so every window has the same weekdays and weekends; calendar months have 28–31 days.

**12. What does your funnel show?**
Of 177 users first seen on the free plan, 40.1% became paid. The biggest drop is the last step: 53.4% of those
who added a friend went on to pay. It is ordered, and users already paying on day one are left out.

### Cohorts and RFM
**13. Explain cohort retention.**
Group users by the week they first appeared, then for each later week count what share came back. The Oct 1 cohort
keeps 58.6% by week 7; paid users 72.7% vs free 55.0%.

**14. What traps are there in a cohort table?**
A partial last week looks like a drop (I removed it); the first cohort holds everyone already using the app; tiny
cohorts swing a lot from one person.

**15. How did you make RFM forward-looking, and what did it show?**
I scored users on events before Nov 10 only and checked who cancelled in the next 21 days. The "at risk"
segment had 0 of 19 cancels while "Loyal" had 12%. Classic RFM did not find cancellers here.

### Churn model
**16. How did you split train and test, and why not randomly?**
By time: train on users as of Oct 20 (label: cancels by Nov 10), test on users as of Nov 10 (cancels by Dec 1).
A random split would let the model see the same weeks it is tested on, which is not how it would be used.

**17. What is data leakage and how did you rule it out?**
Information the model would not have at prediction time, usually from the future. My test deletes every event
after the cutoff and checks all 21 features stay identical. It caught a real bug: session length depended on
whether a session ended after the cutoff.

**18. Why logistic regression and gradient boosting?**
Logistic regression is a simple, explainable baseline; gradient boosting can catch interactions. I chose between them
with 5-fold cross-validation on training users only; logistic regression won, 0.186 vs 0.126 PR-AUC.

**19. Why PR-AUC and not accuracy?**
Only 7% cancel, so "nobody cancels" is 93% accurate and useless. PR-AUC measures how well cancellers rise to the
top. A random ranking scores the churn rate, 0.071; mine scored 0.215.

**20. Is your model good?**
Not yet. It found 5 of 13 cancellers in its top 20% vs 2.6 by chance; 9.5% of random shuffles do as well
(p = 0.095), and the PR-AUC range is 0.07–0.44. On 7 dates it beat random on average every time but was significant
on only 2. I would not spend money on it.

**21. What drives churn in your model?**
Help page visits and Settings visits (more = more risk), thumbs-up per 100 songs (more = less risk), thumbs-down rate
(more risk). Measured by how much the score drops when each feature is scrambled. With 18 training cancellers
this ranking is not stable, so I present it as hints.

**22. You used class weights. Any side effects?**
Yes. They make the model pay attention to the rare cancellers but inflate the probabilities: average predicted
0.41 against a real rate of 0.07. I use the scores only to rank.

### Decision and experiment
**23. Which users would you save, and how?**
Paid users who open the Cancel page: all 52 openers cancelled, so an offer there reaches only real leavers and
wastes no discounts. E-mailing the model's top 20% would need a 46% save rate to break even, because most of
those users were never leaving.

**24. How did you size it without revenue data?**
I took the cancel rates from the data and labelled everything else as assumptions: \$9.99 price, \$5 discount,
5/10/20% save rate, 1/2/3 extra months. Per 10,000 paid users per month the Cancel-page offer nets +\$860 to
+\$8,027; the e-mail option loses \$1,725 to \$4,114 in every scenario.

**25. Design the A/B test.**
Paid users opening Cancel, randomised 50/50 by user. Primary metric: still paying at day 30. Guardrails: Cancel-page
visits per 1,000 users (discount farming), revenue at day 60, complaints. 269 users per group for a 5-point lift at
α 0.05 and 80% power; run 4 weeks. Decision rule fixed before launch: ship only if the 95% interval is above zero
and no guardrail fails; no peeking.
