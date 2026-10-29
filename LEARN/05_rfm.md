# 5. RFM segments

## The idea
RFM is an old marketing method to group customers by three numbers:
- **R, Recency**: how long since they last came? (fewer days = better)
- **F, Frequency**: how often do they come? (here: number of sessions)
- **M, Monetary**: how much value do they bring? There is **no money** in this data, so we use **songs played** instead.

Each user gets a score 1–3 on each letter (3 = best third), then a segment name from the scores:
Champions, Loyal, At risk (was strong, gone quiet), Casual, Hibernating.

> **Hinglish:** RFM mein hum har user ko teen sawaal se naapte hain: kitne din pehle aaya, kitni baar aata hai, aur kitna sunta hai; phir in teeno ke number se usko ek group mein daal dete hain.

## How we made it fair
Most RFM tutorials compute segments using all data, then show "the At-risk group churned most". That is
circular: people who already left look "not recent".
We did it properly: segments use **only events before Nov 10**, and then we check who cancelled in the **next 21 days**.

## What we found
| Segment | Users | Cancelled in next 21 days |
|---|---|---|
| Loyal | 50 | 6 (12.0%) |
| Champions | 38 | 4 (10.5%) |
| Hibernating | 42 | 2 (4.8%) |
| Casual | 35 | 1 (2.9%) |
| At risk (gone quiet) | 19 | **0 (0%)** |

The "best" users cancelled most, and the "at risk" group cancelled least. RFM pointed the wrong way.
Why? To cancel you must open the app and click Cancel. Heavy, unhappy users do that; quiet users just drift
away silently (and our label does not count silent leavers).

Careful: only 13 cancels in total, so each row is a handful of people. The *direction* is the lesson, not the exact %.

## Say it in one line
"I scored users on recency, frequency and listening volume before a cutoff and checked who cancelled after; the
'at risk' group had zero cancels, so classic RFM does not find cancellers in this app."
