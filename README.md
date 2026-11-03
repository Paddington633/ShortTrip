# ShortTrip / ChinaTravel modified architecture

Complete source snapshot of the original ChinaTravel/LLMNeSy architecture plus the four-category soft scorer,20-candidate selection, updated prompts, and the latest C-only meal/date/daylight extension. See [ARCHITECTURE.md](ARCHITECTURE.md) for current behavior and unresolved limitations; original credits and MIT license are retained in README.upstream.md and LICENSE.

No API keys, virtual environments, sandbox archives, run logs, cached model responses, interrupted runs, candidate pools, or generated itineraries are included. The10 fixed easy/human inputs and offline tests are source fixtures. Large official data is downloaded separately with pinned revisions/checksums.

## Setup

Python3.12+. From this repository root:

```sh
python -m venv .venv
# Activate the environment for your operating system.
python -m pip install -r requirements.txt
python scripts/bootstrap_data.py --lang both
# Copy .env.example to .env.local and put your own API key in it.
python experiments/c_only/prepare.py
python experiments/c_only/driver.py
```

Default model:deepseek-flash, official DeepSeek API, thinking disabled, max output4096. Configuring the key alone never starts a paid run. prepare.py makes no model calls; driver.py starts up to10 paid case runs,3 at a time, once each. It will preserve existing run artifacts rather than silently rerun them.

HTML:experiments/c_only/itineraries.html. JSON:all_results.json and summary.json in the same ignored runtime directory. report.py only renders saved results and never calls the model.

```sh
python -m pip install pytest
python -m unittest discover -s experiments/c_only -p "test_*.py"
python -m pytest tests
```

Use the elevated/normal execution environment that can terminate its own process trees on Windows; the timeout test verifies the venv launcher and actual interpreter are both stopped. Windows checkout-specific HOME/USERPROFILE behavior in an inherited test is a known upstream limitation.
