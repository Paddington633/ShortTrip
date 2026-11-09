# ShortTrip

Modified ChinaTravel / LLMNeSy travel planning with structured constraint
translation, database retrieval, DFS, hard-constraint pruning, four-category soft
scoring, and selection from up to 20 feasible itinerary candidates.

## Current changes

- Flexible C-group meal ordering explores sightseeing before meals and meals
  before sightseeing, with real-route meal feasibility checks.
- Translation validates source evidence, database names, metadata and generated
  checks. Standard constraints use deterministic Python templates.
- Pruning filters incompatible tickets and checks irreversible prefix violations,
  cost lower bounds and optimistic meal feasibility.
- Transport checks try all permitted modes before rejecting access as too late.
- Selection records pruning counts and bounded examples.

See [ARCHITECTURE.md](ARCHITECTURE.md), [translation details](docs/translation-alignment.md),
[meal ordering](docs/flexible-meals.md), and [pruning](docs/pruning.md).

## Setup

Use Python 3.12 or newer from the repository root.

```sh
python -m venv .venv
# Activate .venv for your operating system.
python -m pip install -r requirements.txt
python scripts/bootstrap_data.py --lang both
```

## Local-model C experiment

The checked-in experiment uses a separately deployed, OpenAI-compatible local
Qwen3.5-4B Q8 server at `http://127.0.0.1:18080/v1`, exposing model alias
`qwen3.5-4b-q8`. The tested deployment used a 16K context with thinking disabled.
Start the model server before launching the driver.

```sh
python experiments/c_only/prepare.py
python experiments/c_only/driver.py
```

Preparation writes ignored configuration and source hashes without model calls.
The driver runs the original five easy and five human inputs once each,
sequentially, with a 30-minute case limit and target of 20 candidates. Existing
case artifacts are preserved. Request timeout is 600 seconds with no HTTP retry.

Results are written to `experiments/c_only/itineraries.html`, `summary.json`,
`all_results.json` and per-case JSON directories. Rendering saved results uses
`python experiments/c_only/report.py`.

The original configurable API entry points remain in `reproduction/` and the
original source tree. The C experiment above explicitly targets loopback inference.

## Offline tests

Download the pinned data first. No model server is needed for these tests.

```sh
python -m unittest discover -s tests -p "test_*.py"
python -m unittest discover -s experiments/c_only -p "test_*.py"
```

On Windows, run the process-tree timeout test in an execution environment that
can terminate its own child processes. Verification details are recorded in
[VERIFICATION.md](VERIFICATION.md).

Original documentation and credits are in `README.upstream.md`,
`README.upstream.zh-CN.md` and `LICENSE`.
