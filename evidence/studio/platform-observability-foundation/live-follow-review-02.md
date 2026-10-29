# Follow-up controlled-test finding, before repair

The repeated final browser cohort reports4pass/1failure: terminal-stop test expected
capture count3 to remain fixed, but count4 arrived. The test captured the count when
the checkbox was disabled, which occurs immediately at a terminal prop transition;
the final capture effect is scheduled afterwards. A normal poll during stopping can
also finish before the one required final capture. Thus the current assertion does
not distinguish the permitted final read from unwanted later polling.

Before changing product behavior, instrument the controlled HTTP handler to identify
fresh reads actually requested after the UI renders the terminal state. Require
exactly one such final read, wait for it, then advance the clock and prove no further
reads occur. Retain the failed log, JSON report and screenshot. This strengthens
the terminal requirement without pretending the failed cohort passed. Product
code stays unchanged while the actual approved native check is in progress.
