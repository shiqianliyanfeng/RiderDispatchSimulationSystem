# Product Requirements Document (PRD) — Rider Dispatch Simulation System (EN)

## Purpose
Provide a reproducible, extensible simulation platform to evaluate rider dispatch strategies for front-warehouse (dark store) operations. The simulation supports time-windowed orders, rider capacities, rider online/offline behavior, and multiple dispatch algorithms to measure key performance indicators (KPIs) and support operational decision-making.

## Audience
- Product managers evaluating dispatch strategies
- Data scientists running experiments and parameter sweeps
- Engineers extending dispatch algorithms and integrating real maps
- Operations analysts using KPI outputs for planning

## Features
### 1. Event-driven simulation engine
- Minute-level discrete-event simulation.
- Event types: `order_arrival`, `delivery_batch`, `rider_return`, `rider_online`, `rider_offline`.

### 2. Rider model
- Attributes: `id`, `location`, `base_location`, `star`, `capacity`, `state`, `online`, `assigned_orders`.
- States: `OFFLINE`, `ONLINE`, `IDLE`, `ASSIGNED`, `DELIVERING`, `RETURNING`.
- APIs: `go_online()`, `go_offline()`, `can_take()`.

### 3. Order model
- Attributes: `id`, `pickup`, `dropoff`, `request_time`, `window_start`, `window_end`, `status`, `assigned_rider`, `delivery_time`.
- Statuses: `CREATED`, `ARRIVED`, `PENDING`, `ASSIGNED`, `DELIVERING`, `DELIVERED`, `COMPLETED`, `CANCELLED`.

### 4. Scheduling & dispatch
- Global CVRPTW via OR-Tools (if available): supports time windows and vehicle capacities.
- Greedy CVRPTW-inspired fallback heuristic: insertion + 2-opt.
- Dispatch considers only `online` and `IDLE` riders, respects rider capacity.
- Batch assignment: riders can be assigned multiple orders (up to capacity) and deliver sequentially.

### 5. Path planning
- Travel time and distance estimation.
- Simple heuristics for routing and 2-opt improvement.

### 6. Metrics and logging
- KPI outputs: on-time rate, early/late deliveries, average delivery time, rider utilization, average distance.
- Detailed event logging to `simulation.log`.

## Non-functional requirements
- Reproducible runs via deterministic RNG seeds (optional extension).
- Modular structure and clear interfaces for algorithms and planners.
- Unit tests for core engine and scheduler.

## Usage
1. Install dependencies

```bash
pip install -r requirements.txt
```

2. Run demo

```bash
python dispatch_sim/cli.py
```

3. Run tests

```bash
python3 -m unittest tests/test_engine.py
python3 -m unittest tests/test_scheduler.py
```

## Extension roadmap
- Add realistic map integration (OSRM, GraphHopper) for travel times.
- Add multi-warehouse / multi-depot dispatch.
- Implement stochastic rider behavior models (breaks, cancellations).
- Add an experiment runner and visualization dashboard.

## Success metrics
- Ability to reproduce experiments and compare strategies.
- Coverage of KPIs required by operations (on-time %, utilization, avg delay).
- Extensibility: new algorithms can be plugged in with < 1 day of engineering effort.

## Contacts
Project owner and contributors: check repository metadata and issue tracker.
