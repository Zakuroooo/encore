# 7. Data leakage

## What it is
**Leakage** = the model gets information during training that it would not have at prediction time,
usually information from the future, or the answer itself in disguise.
A leaky model looks brilliant in testing and fails in real life.

> **Hinglish:** Leakage matlab model ko exam se pehle hi answer ka hint mil gaya, isliye test mein marks achhe aate hain, par asli zindagi mein woh fail ho jaata hai.

## Common kinds
1. **Future data in features**: counting songs up to today when the snapshot was last week.
2. **The answer as a feature**: using "visited the Cancel page" to predict "cancelled". (It is the same event!)
3. **Overlapping time**: the test period's events used in training.
4. **Choosing on the test set**: trying 20 models and keeping the best test score. The test score is then too optimistic.

## Our guards
| Guard | Where |
|---|---|
| Every feature uses events with time < cutoff | `analysis/features.sql` (`past` table) |
| Cancel and Cancellation Confirmation pages are never features | test `test_cancel_pages_are_not_features` |
| Train label window (Oct 20 – Nov 10) ends where test features start | test `test_label_windows_do_not_overlap` |
| Model chosen on training CV only; test scored once | `analysis/churn_model.py` |
| All tried variants published, not just the best | `outputs/experiment_snapshots.csv`, `robustness_cutoffs.csv` |

## The proof test (and the real bug it found)
`tests/test_leakage.py` does this:
1. Compute features on the full database.
2. Build a second database where **every event after the cutoff is deleted**.
3. Compute features again. If any feature differs, it was using the future → test fails.

The first version **failed this test**. Session length came from a table of whole sessions, and the code kept
only sessions that *ended* before the cutoff. So a session running across the cutoff was dropped, and whether it was
dropped depended on events after the cutoff. It changed one feature for 4.9% of training users.
The fix: rebuild sessions from past events only. Now the test passes.

## Say it in one line
"I proved there is no leakage by deleting every event after the cutoff and checking that all 21 features stay
identical, and that test caught a real bug in my first version."
