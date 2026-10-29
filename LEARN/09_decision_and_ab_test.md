# 9. From analysis to a decision, and the A/B test

## The two options we compared
- **A: offer on the Cancel page.** When a paid user opens Cancel, show "Stay for 50% off next month".
  Only people already leaving see it.
- **B: e-mail the model's top 20%.** Send the same discount to paid users the model flags.

## Sizing: facts vs assumptions
Facts (from the data): 8.0% of paid users cancelled in 21 days → about 11.5% a month → per 10,000 paid users,
about **1,148** open the Cancel page each month, and 100% of them confirm today.

Assumptions (not in the data; written down and labelled): price \$9.99/month; discount \$5; **save rate** (share
of would-be leavers who take the offer and stay) 5% / 10% / 20%; extra months kept 1 / 2 / 3; for e-mail,
30% of users who were *not* leaving also grab the discount.

Money per saved user = discounted month (\$4.99) + extra months × \$9.99.
A **wasted discount** = a discount given to someone who would have paid full price anyway.

| Scenario | A: Cancel page, net per month | B: e-mail, net per month |
|---|---|---|
| low (5%, 1 month) | +\$860 | −\$4,114 |
| mid (10%, 2 months) | +\$2,866 | −\$3,445 |
| high (20%, 3 months) | +\$8,027 | −\$1,725 |

Option B loses money every time: most people it e-mails were never leaving, so most discounts are wasted.
**Break-even** (the save rate where gain = cost) for B is 46%, not believable. Option A wastes nothing.

## Why not just ship option A?
Because the save rate is a guess. An **A/B test** measures it.

## A/B test basics
Split users randomly into two groups. **Control** sees today's app; **treatment** sees the change.
Because the split is random, the only systematic difference between groups is the change, so a difference
in outcomes is caused by the change (plus chance, which statistics measures).

Our design (full version: docs/AB_TEST.md):
- **Who**: paid users opening the Cancel page. **Split**: 50/50 by user.
- **Primary metric**: still paying 30 days later.
- **Guardrails** (must not get worse): Cancel-page visits per 1,000 users (people farming the discount), revenue at day 60, complaints.

## Sample size
To detect a change from 2% (assumed) to 7% "still paying", with α = 0.05 (5% false-alarm risk) and power 0.8
(80% chance to detect a real effect): **269 users per group**. At 10,000 paid users that is about 2 weeks of traffic;
we run 4 weeks to cover each weekday twice and let everyone reach day 30.

Smaller effects need many more users: the needed sample grows with 1 ÷ (effect)².

## Decision rule written BEFORE the test
Ship only if the 95% interval of the difference is above zero **and** no guardrail fails **and** revenue per user
at day 60 is not lower. No peeking and no stopping early. Writing the rule first stops us from
"finding" a win afterwards.

## Say it in one line
"The Cancel-page offer wastes no discounts and wins in every scenario, while e-mailing model-flagged users needs a
46% save rate to break even; the save rate is a guess, so I designed a 538-user A/B test with the ship rule fixed in advance."
