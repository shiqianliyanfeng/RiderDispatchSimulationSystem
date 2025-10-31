from typing import List, Any
import heapq
from .models import Rider, Order, RiderState, OrderStatus
from .scheduler import Scheduler
from .path_planner import PathPlanner
from .metrics import Metrics
import logging

logger = logging.getLogger(__name__)


class Event:
    def __init__(self, time: int, kind: str, payload: Any = None):
        self.time = time
        self.kind = kind
        self.payload = payload

    def __lt__(self, other):
        return self.time < other.time


class SimulationEngine:
    """Event-driven simulation engine.

    Events: 'order_arrival', 'pickup', 'delivery', 'rider_return'
    """

    def __init__(self, start_minute=0, end_minute=60 * 24):
        self.time = start_minute
        self.end_minute = end_minute
        self.riders: List[Rider] = []
        self.orders: List[Order] = []
        self.planner = PathPlanner()
        self.scheduler = Scheduler(self.riders, self.planner)
        self.metrics = Metrics()
        self.event_queue: List[Event] = []

    def schedule_event(self, event: Event):
        heapq.heappush(self.event_queue, event)
        logger.debug("Scheduled event %s at %s", event.kind, event.time)

    def add_rider(self, rider: Rider, online: bool = False):
        self.riders.append(rider)
        if online:
            self.schedule_event(Event(self.time, 'rider_online', rider))
        else:
            rider.go_offline()
            
    def handle_rider_online(self, rider: Rider):
        rider.go_online()
        logger.info("Rider %s ONLINE at %s", rider.id, self.time)

    def handle_rider_offline(self, rider: Rider):
        rider.go_offline()
        logger.info("Rider %s OFFLINE at %s", rider.id, self.time)

    def add_order(self, order: Order):
        self.orders.append(order)
        logger.info("Order created %s request_time=%s window=(%s,%s)", order.id, order.request_time, order.window_start, order.window_end)
        # schedule its arrival event
        ev = Event(order.request_time, 'order_arrival', order)
        self.schedule_event(ev)

    def handle_order_arrival(self, order: Order):
        # mark arrival
        order.status = OrderStatus.ARRIVED
        logger.info("Order %s ARRIVED at %s", order.id, self.time)
        # When any order arrives, try dispatching all pending unassigned orders (allow batching)
        for o in self.orders:
            if o.request_time <= self.time and o.status == OrderStatus.ARRIVED:
                o.status = OrderStatus.PENDING
        pending = [o for o in self.orders if o.status == OrderStatus.PENDING and o.request_time <= self.time]
        logger.debug("Order arrival handling at time=%s pending_count=%s", self.time, len(pending))
        # batch assignment: scheduler returns list of (rider, [orders])
        assignments = self.scheduler.dispatch(pending, current_time=self.time)
        # schedule batch delivery for each rider
        for rider, order_batch in assignments:
            if not order_batch:
                continue
            for o in order_batch:
                o.assigned_time = self.time
                o.status = OrderStatus.ASSIGNED
                o.assigned_rider = rider.id
                logger.info("Order %s status->ASSIGNED rider=%s at %s", o.id, rider.id, self.time)
            if rider.busy_since is None:
                rider.busy_since = self.time
            # build route: depot -> dropoff1 -> dropoff2 ...
            route = [rider.location] + [o.dropoff for o in order_batch]
            depart_time = self.time
            delivery_times = []
            current_loc = rider.location
            current_time = depart_time
            for o in order_batch:
                travel = self.planner.travel_time_minutes(current_loc, o.dropoff)
                current_time += int(round(travel))
                delivery_times.append(current_time)
                current_loc = o.dropoff
            # schedule a single batch delivery event with all orders and their delivery times
            self.schedule_event(Event(delivery_times[-1], 'delivery_batch', {
                'rider': rider,
                'orders': order_batch,
                'delivery_times': delivery_times,
                'route': route
            }))

    def handle_delivery_batch(self, data: dict):
        rider = data['rider']
        orders = data['orders']
        delivery_times = data['delivery_times']
        route = data['route']
        # simulate sequential delivery
        for idx, o in enumerate(orders):
            o.status = OrderStatus.DELIVERED
            o.delivery_time = delivery_times[idx]
            distance_km = self.planner.distance_km(route[idx], o.dropoff)
            logger.info("Order %s delivered by rider %s at %s distance_km=%.3f", o.id, rider.id, delivery_times[idx], distance_km)
            self.metrics.record_delivery(o, delivery_times[idx], distance_km)
        # rider now at last dropoff
        rider.location = orders[-1].dropoff
        rider.state = RiderState.RETURNING
        # schedule rider return to base_location
        return_t = self.planner.travel_time_minutes(rider.location, getattr(rider, 'base_location', rider.location))
        return_time = delivery_times[-1] + int(round(return_t))
        logger.debug("Rider %s returning to base, eta=%s", rider.id, return_time)
        self.schedule_event(Event(return_time, 'rider_return', {'rider': rider, 'orders': orders}))

    def handle_rider_return(self, data: dict):
        rider = data['rider']
        rider.state = RiderState.IDLE
        rider.assigned_orders.clear()
        rider.location = getattr(rider, 'base_location', rider.location)
        logger.info("Rider %s returned to base at %s and is now IDLE", rider.id, self.time)
        # mark busy period end for utilization
        if rider.busy_since is not None:
            busy = self.time - rider.busy_since
            self.metrics.record_rider_idle_period(rider, self.time)
            rider.busy_since = None
            logger.debug("Rider %s busy period ended length=%.2f", rider.id, busy)
        # if orders were tied to this return event, mark them completed
        orders = data.get('orders', None)
        if orders is not None:
            for o in orders:
                o.status = OrderStatus.COMPLETED
                logger.info("Order %s status->COMPLETED at %s", o.id, self.time)

    def run(self, until=None):
        if until is None:
            until = self.end_minute
        while self.event_queue and self.time <= until:
            ev = heapq.heappop(self.event_queue)
            # advance time
            self.time = ev.time
            if self.time > until:
                break
            if ev.kind == 'order_arrival':
                self.handle_order_arrival(ev.payload)
            elif ev.kind == 'delivery_batch':
                self.handle_delivery_batch(ev.payload)
            elif ev.kind == 'rider_return':
                self.handle_rider_return(ev.payload)
            elif ev.kind == 'rider_online':
                self.handle_rider_online(ev.payload)
            elif ev.kind == 'rider_offline':
                self.handle_rider_offline(ev.payload)
        return self.metrics
