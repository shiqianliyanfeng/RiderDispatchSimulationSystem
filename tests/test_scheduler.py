import unittest
from dispatch_sim.scheduler import Scheduler
from dispatch_sim.models import Rider, Order, OrderStatus, RiderState
from dispatch_sim.path_planner import PathPlanner

class TestScheduler(unittest.TestCase):
    def setUp(self):
        self.riders = [
            Rider(location=(0.0, 0.0), base_location=(0.0, 0.0), star=5, capacity=2),
            Rider(location=(0.0, 0.0), base_location=(0.0, 0.0), star=4, capacity=1)
        ]
        for r in self.riders:
            r.go_online()
        self.planner = PathPlanner()
        self.scheduler = Scheduler(self.riders, self.planner)

    def test_dispatch_single_order(self):
        order = Order(pickup=(0.0, 0.0), dropoff=(1.0, 1.0), request_time=0, window_start=0, window_end=10, status=OrderStatus.PENDING)
        assignments = self.scheduler.dispatch([order], current_time=0)
        self.assertEqual(order.assigned_rider, self.riders[0].id)
        self.assertEqual(order.status, OrderStatus.ASSIGNED)
        self.assertEqual(len(self.riders[0].assigned_orders), 1)

    def test_dispatch_capacity(self):
        orders = [
            Order(pickup=(0.0, 0.0), dropoff=(1.0, 1.0), request_time=0, window_start=0, window_end=10, status=OrderStatus.PENDING),
            Order(pickup=(0.0, 0.0), dropoff=(2.0, 2.0), request_time=0, window_start=0, window_end=10, status=OrderStatus.PENDING),
            Order(pickup=(0.0, 0.0), dropoff=(3.0, 3.0), request_time=0, window_start=0, window_end=10, status=OrderStatus.PENDING)
        ]
        assignments = self.scheduler.dispatch(orders, current_time=0)
        assigned_counts = [len(r.assigned_orders) for r in self.riders]
        self.assertEqual(assigned_counts, [2, 1])
        for o in orders:
            self.assertEqual(o.status, OrderStatus.ASSIGNED)

    def test_dispatch_only_online(self):
        self.riders[1].go_offline()
        order = Order(pickup=(0.0, 0.0), dropoff=(1.0, 1.0), request_time=0, window_start=0, window_end=10, status=OrderStatus.PENDING)
        assignments = self.scheduler.dispatch([order], current_time=0)
        self.assertEqual(order.assigned_rider, self.riders[0].id)
        self.assertEqual(order.status, OrderStatus.ASSIGNED)
        self.assertEqual(len(self.riders[0].assigned_orders), 1)
        self.assertEqual(len(self.riders[1].assigned_orders), 0)

    def test_dispatch_no_idle(self):
        self.riders[0].state = RiderState.DELIVERING
        self.riders[1].state = RiderState.DELIVERING
        order = Order(pickup=(0.0, 0.0), dropoff=(1.0, 1.0), request_time=0, window_start=0, window_end=10, status=OrderStatus.PENDING)
        assignments = self.scheduler.dispatch([order], current_time=0)
        self.assertIsNone(order.assigned_rider)
        self.assertEqual(order.status, OrderStatus.PENDING)
        self.assertEqual(len(self.riders[0].assigned_orders), 0)
        self.assertEqual(len(self.riders[1].assigned_orders), 0)

if __name__ == '__main__':
    unittest.main()