# Freeze campaign worker files after the writer exits

The observation backend's full 1145-case run ended1144pass/1failure in the existing
failed-continue campaign restart case. All328 selected inputs stayed unchanged.
The test froze terminal file hashes on the first failed state observation and later
compared them after restart. Its original sampled hashes were not retained, so the
exact original differing file/bytes remain unestablished. The failed report and
JUnit are retained under M3-explicit-lab-observations/full-backend-failed/.

Source inspection finds two saves in the worker error path. A separately labelled
native wrapper injects KeyboardInterrupt at sleep and holds the first failed
atomic write. The worker is still alive with failed state visible; after release,
its second write changes updatedAt and the file digest. This proves the precondition
gap, not the exact old failure schedule. The first diagnostic used an unavailable
host interpreter; its import/setup failure is retained, not a product failure.

The permanent test now observes original writer exit/zombie before freezing files,
checks final PID/birth/owner/state and retains both before/after hashes. Its exact
inverse restores every original source byte; no original assertion, fault source
or threshold changes. All four actual native campaign cases pass on328 unchanged
successor inputs. All three terminal modes confirm process-exit precondition and
equal before/after hashes. Production worker/lifecycle behavior is unchanged.

No fresh single-command full1145 pass is claimed. The observation UI is unfinished;
its two initial native cases fail for the absent control. No successor clean
package, Windows/hardware acceptance or milestone closure follows from this repair.
Counts47/43/10 and zero accepted milestones remain unchanged.
