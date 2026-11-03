# Source snapshot verification

- Latest C extension:36offline tests passed after relocating all current experiment modules to experiments/c_only with repository-relative paths.
- Original inherited suite:61of62 tests passed. The known Windows-only test_translation_api_config_expands_user_directory patchesHOME but pathlib.expanduser usesUSERPROFILE; the source behavior has not been silently altered for publication.
- Python syntax checked for all copied sources. C prepare/report run without API calls and produce10pending cases; those generated files are Git-ignored and not part of the published source.
- Exact configured API credentials and private-key material scanned before staging. No .env.local, logs, response traces, candidate pools, experiment output JSON/HTML, database or virtual environment are tracked.
- Local sandbox directories were temporarily linked only for offline verification and are removed after testing. Clone setup downloads pinned official datasets separately using scripts/bootstrap_data.py.
- This is the current architecture snapshot. Known NL2SL/constraint-ordering/late-pruning defects remain documented in ARCHITECTURE.md; no claim is made that all travel cases succeed.
