# LEARN: everything in this project, from zero

These notes explain every idea used in Encore in simple English. Read them in order. Each file ends with
"Say it in one line": practise saying that line out loud until it feels natural.

| # | File | You will be able to explain |
|---|---|---|
| 1 | [01_the_data.md](01_the_data.md) | what an event log is, users, sessions, what "churn" means here |
| 2 | [02_sql_pipeline.md](02_sql_pipeline.md) | raw → clean → analytics layers, DuckDB, data-quality checks, the SQL tricks used |
| 3 | [03_product_metrics.md](03_product_metrics.md) | DAU, WAU, MAU, stickiness, funnels, paid vs free |
| 4 | [04_cohorts_and_retention.md](04_cohorts_and_retention.md) | cohorts, retention tables, retention curves |
| 5 | [05_rfm.md](05_rfm.md) | RFM segments, and why they failed here |
| 6 | [06_churn_model.md](06_churn_model.md) | features, labels, time split, logistic regression, gradient boosting |
| 7 | [07_leakage.md](07_leakage.md) | data leakage, and how the test proves we have none |
| 8 | [08_evaluating_the_model.md](08_evaluating_the_model.md) | precision, recall, PR-AUC, recall@top-k, lift, bootstrap, p-values, calibration |
| 9 | [09_decision_and_ab_test.md](09_decision_and_ab_test.md) | sizing a decision, break-even, A/B tests, sample size |
| 10 | [10_interview_questions.md](10_interview_questions.md) | 25 likely questions, with answers |
| 11 | [11_explain_the_code.md](11_explain_the_code.md) | a file-by-file tour to defend the code live |

**The whole project in 4 sentences.** I took the event log of a (simulated) music app with 225 users.
I measured engagement, a sign-up-to-paid funnel, weekly cohort retention and RFM segments in SQL. I built a
churn model and showed honestly that, with only 13 cancellers to test on, it is not reliably better than chance.
The most useful finding was simpler: everyone who opened the Cancel page cancelled within seconds, so I
recommended a save offer there, sized it with clear assumptions, and wrote the A/B test to check it.
