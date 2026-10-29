# Memo: put the save offer where people actually cancel

**To:** Head of Product, Retention · **From:** Pranay Sarkar · **Data:** Sparkify sample log, 225 users,
Oct 1 – Nov 30 2018 (simulated app; method demo) · **Full detail:** README, dashboard, `outputs/`

## Recommendation
Add a one-time save offer (50% off next month) to the **Cancel page** for paid users, and launch it as an
A/B test (269 users per group, 4 weeks, decision rule fixed in advance: docs/AB_TEST.md).
**Do not** spend discounts on e-mails to users a churn model flags.

## Why
1. **The cancel flow has no brakes.** All 52 users who opened the Cancel page confirmed, a median of
   **25.5 seconds** later. Those people are certainly leaving, so an offer shown there wastes almost nothing.
2. **The churn model is weak.** On the test period it found **5 of 13** cancellers in its top 20% (random:
   2.6 on average), PR-AUC **0.215** vs 0.071 for random. That is not reliably better than luck (p = 0.095), and
   it reached p < 0.05 on only 2 of 7 test dates. With 13 cancellers, no model here can prove itself.
3. **E-mail offers lose money even under hopeful assumptions.** Per 10,000 paid users per month, e-mailing the
   model's top 20% loses \$1,725–\$4,114 in our three scenarios; it would need to save **46%** of flagged
   cancellers to break even. The Cancel-page offer gains \$860–\$8,027 (save rate 5–20%, 1–3 extra months kept).
4. **Classic RFM points the wrong way.** "Loyal" and "Champions" users cancelled most (12.0% and 10.5% in 21 days);
   "At risk (gone quiet)" users cancelled **none** (0 of 19). Heavy users who are unhappy click Cancel.

## What I am not sure about
- **Assumed, not measured:** price \$9.99, discount \$5, save rate 5/10/20%, months kept 1/2/3. The A/B test exists to measure the save rate.
- **The label misses silent leavers.** At the test snapshot, 15 users stopped coming without cancelling, more than
  the 13 who cancelled. A Cancel-page offer cannot reach them.
- **Simulated, small data.** The method transfers; the exact numbers will not.

## Next steps
1. Build the offer screen behind a flag; run the A/B test as written (owner: product + CRM).
2. Add "inactive 14+ days" as a second outcome to track. For it, "days since last event" already ranks users
   better than chance (PR-AUC 0.227 vs 0.152) and costs nothing to compute: try a free re-engagement nudge.
3. Re-train the churn model on the full user base (thousands of cancellers) before using it for anything that costs money.
