# Current architecture

Natural-language request -> original NL2SL translation -> sandbox retrieval -> intercity/hotel ranking -> original DFS with C-group hooks -> original hard/common validation + new meal/date/daylight validation -> pool of20 unique feasible candidates -> minimum soft-penalty plan -> original independent evaluation -> HTML/JSON report.

Core modules: chinatravel/agent/nesy_agent; chinatravel/environment; chinatravel/symbol_verification; chinatravel/evaluation. Four-category soft scoring and candidate pool: chinatravel/soft_constraints. Latest C-group integration: experiments/c_only/experiment_agent.py, dfs_snapshot.py, rules.py, catalog.py. The original search architecture is preserved.

Meals: breakfast06-09/30min, lunch11-14/60min, dinner17-20/60min; windows constrain start time. Journey begins at outbound departure and ends at return arrival. Intercity traffic can exempt a meal when no full opportunity remains; access/waiting cannot. Absolute dates include midnight access and approximate sandbox Duration rollover.

Sightseeing must be within08:00-21:00 and actual opening hours; gated before insertion and in final audit. Hotel midnight usually resumes06:00, with access/buffer-aware exceptions for early returns. Hotel breakfast requires actual preceding accommodation.

C prioritizes morning outbound and evening return, recomputes delayed meal/return access, and limits attraction opening waits. Each input runs once, at most30min with20-candidate target. No previous outputs are used.

Known unresolved issues: NL2SL may invent room constraints or misuse transport helper signatures; preference reranking can place a hard-incompatible return ahead of feasible ones; several constraints are checked only at completed plans, causing late rejection and excessive local DFS; budget recommendations can leave too little for meals; model activity prompt still describes some original semantics. These issues are preserved and documented, not silently claimed fixed by publication. The daylight sightseeing defect is fixed in this snapshot.
