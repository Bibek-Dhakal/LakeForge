# Case study: LakeForge

Back to [README](../README.md).

1. **Problem:** duplicated, late, malformed, schema-drifting sources corrupt tables and erode trust.
2. **Requirements:** _summarise the analyst conversation: questions they ask, freshness needs, access rules_.
3. **Design:** see [architecture](architecture/overview.md); key trade-offs: correctness over throughput, single-node Spark.
4. **Evidence:** idempotency check output, quarantine recall test, schema-change scenarios, [performance report](results/performance_report.md).
5. **Feedback:** _quotes and queries from real users, external review notes_.
6. **Outcome and lessons:** _numbers: pass-rate, freshness attainment, run times, defects found_.
