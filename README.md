# Dispatch Simulation System — Usage Guide (English)

## Overview
This repository implements an event-driven rider dispatch simulation platform designed for quick experimentation with dispatch strategies, rider behaviors, and delivery time-window constraints. It can be used to prototype scheduling logic (global VRPTW with OR-Tools and greedy fallbacks), measure KPIs, and analyze the impact of operational decisions.

## Repository layout
- `dispatch_sim/` — main package containing engine, models, scheduler, path planner, metrics and CLI.
- `tests/` — unit tests for engine and scheduler.
- `simulation.log` — runtime log produced by CLI demo.
- `README.md` — Chinese usage guide (also contains development notes).
- `README_EN.md` — this English usage guide.
- `PRD_EN.md` — English product requirement document (detailed PRD).

## Requirements
- Python 3.8+
- Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional: install OR-Tools to enable the global VRPTW solver:

```bash
pip install ortools
```

## Run the demo
Run the CLI demo which simulates order arrivals and rider behavior and writes logs to `simulation.log`.

```bash
python dispatch_sim/cli.py
```

## Run tests
Run the unit tests with unittest:

```bash
python3 -m unittest tests/test_engine.py
python3 -m unittest tests/test_scheduler.py
```

## Key features
- Event-driven simulation loop with minute-level resolution.
- Rider lifecycle and online/offline events.
- Batch assignment of orders with capacity constraints per rider.
- Time-window aware dispatching.
- OR-Tools VRPTW integration (optional) with greedy heuristic fallback.
- Pluggable path planner for travel time and route heuristics.
- KPI and logging outputs for analysis.

## Extending the project
- Add new scheduling algorithms by editing `dispatch_sim/scheduler.py`.
- Integrate real maps or traffic models in `dispatch_sim/path_planner.py`.
- Add scenario drivers or large-scale experiment scripts in `/scripts` (create as needed).

## Contact
For questions or contributions, open an issue or pull request in the repository.
