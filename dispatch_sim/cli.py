try:
    # when run as a package module
    from .engine import SimulationEngine, Event
    from .models import Rider, Order
except Exception:
    # when run as a script, add project root to sys.path and import absolute
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from dispatch_sim.engine import SimulationEngine, Event
    from dispatch_sim.models import Rider, Order
import random
import math
import logging
import os

# configure module-level logging to write to simulation.log in project root
logger = logging.getLogger()
if not logger.handlers:
    log_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'simulation.log'))
    fh = logging.FileHandler(log_path)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.setLevel(logging.INFO)


def poisson_arrivals(rate_per_minute: float, duration_minutes: int):
    """Generate arrival times (in minutes) for Poisson process with given rate."""
    t = 0
    arrivals = []
    while t < duration_minutes:
        # exponential inter-arrival
        u = random.random()
        if u == 0:
            break
        inter = -math.log(u) / rate_per_minute
        t += inter
        if t < duration_minutes:
            arrivals.append(int(math.floor(t)))
    return arrivals


def run_demo():
    logger.info("Starting simulation demo")
    sim = SimulationEngine()
    # add riders
    riders = [
        Rider(location=(0.0, 0.0), base_location=(0.0, 0.0), star=4, capacity=4),
        Rider(location=(0.0, 0.0), base_location=(0.0, 0.0), star=3, capacity=3),
        Rider(location=(0.0, 0.0), base_location=(0.0, 0.0), star=4, capacity=4),
        Rider(location=(0.0, 0.0), base_location=(0.0, 0.0), star=4, capacity=4)
    ]
    for r in riders:
        sim.add_rider(r)
    # 骑手上线/下线事件
    # 第1个骑手立即上线
    sim.schedule_event(Event(0, 'rider_online', riders[0]))
    # 第2个骑手第5分钟上线
    sim.schedule_event(Event(5, 'rider_online', riders[1]))
    # 第3个骑手第10分钟上线，第30分钟下线
    sim.schedule_event(Event(10, 'rider_online', riders[2]))
    sim.schedule_event(Event(40, 'rider_offline', riders[2]))
    # 第4个骑手第20分钟上线
    sim.schedule_event(Event(20, 'rider_online', riders[3]))
    # schedule a few poisson immediate orders over 60 minutes
    arrivals = poisson_arrivals(rate_per_minute=2.0, duration_minutes=60)
    for i, at in enumerate(arrivals):
        sim.add_order(Order(pickup=(0.0, 0.0), dropoff=(2.0 + 0.1 * i, 2.0 + 0.1 * i), request_time=at, window_start=at, window_end=at+10, order_type='immediate'))
    # add an appointment order with a window
    appt1 = Order(pickup=(0.0, 0.0), dropoff=(4.0, 4.0), request_time=2, order_type='appointment')
    appt1.window_start = 10
    appt1.window_end = 20
    sim.add_order(appt1)
    appt2 = Order(pickup=(0.0, 0.0), dropoff=(5.0, 9.0), request_time=8, order_type='appointment')
    appt2.window_start = 20
    appt2.window_end = 40
    sim.add_order(appt2)

    # run simulation until minute 30
    sim_time = 60
    metrics = sim.run(until=sim_time)
    summary = metrics.summary(sim_time)
    logger.info("Simulation finished summary=%s", summary)
    print('Metrics summary:')
    for k, v in summary.items():
        print(f'  {k}: {v}')


if __name__ == '__main__':
    run_demo()
