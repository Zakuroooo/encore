-- Fixed dates used across the project, in one place so SQL and Python agree.
-- train_cutoff: the model learns from events before this date, label = cancels in the next 21 days.
-- test_cutoff:  the model is scored on events before this date, label = cancels in the next 21 days.
-- The training label window (Oct 22 to Nov 12) ends exactly where test features begin: no overlap.
CREATE TABLE raw.params AS
SELECT DATE '2018-10-22' AS train_cutoff,
       DATE '2018-11-12' AS test_cutoff,
       21                AS horizon_days;
