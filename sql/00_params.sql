-- Fixed dates used across the project, in one place so SQL and Python agree.
-- train_cutoff: the model learns from events before this date, label = cancels in the next 21 days.
-- test_cutoff:  the model is scored on events before this date, label = cancels in the next 21 days.
-- log_end:      the log really covers Oct 1 - Nov 30. After that there are only 4 stray songs
--               (3 just after midnight on Dec 1, 1 on Dec 3, nothing on Dec 2), so the clean layer stops here.
-- The training label window (Oct 20 to Nov 10) ends exactly where test features begin: no overlap.
-- The test label window (Nov 10 to Dec 1) ends exactly at log_end: fully observed.
CREATE TABLE raw.params AS
SELECT DATE '2018-10-20' AS train_cutoff,
       DATE '2018-11-10' AS test_cutoff,
       21                AS horizon_days,
       DATE '2018-12-01' AS log_end;
