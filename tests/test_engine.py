import unittest
from dispatch_sim.engine import SimulationEngine, Event
from dispatch_sim.models import Rider, Order, OrderStatus, RiderState

class TestSimulationEngine(unittest.TestCase):
    def setUp(self):
        self.sim = SimulationEngine(start_minute=0, end_minute=60)
        self.rider = Rider(location=(0.0, 0.0), base_location=(0.0, 0.0), star=5, capacity=2)
        self.sim.add_rider(self.rider, online=True)
        self.order = Order(pickup=(0.0, 0.0), dropoff=(1.0, 1.0), request_time=1, window_start=1, window_end=10)
        self.sim.add_order(self.order)

    def test_order_lifecycle(self):
        # Run simulation
        metrics = self.sim.run(until=20)
        # Order should be completed
        self.assertEqual(self.order.status, OrderStatus.COMPLETED)
        # Rider should be idle and online
        self.assertEqual(self.rider.state, RiderState.IDLE)
        self.assertTrue(self.rider.online)
        # Rider should have no assigned orders
        self.assertEqual(len(self.rider.assigned_orders), 0)

    def test_rider_online_offline(self):
        # Rider goes offline at minute 5
        self.sim.schedule_event(Event(5, 'rider_offline', self.rider))
        # Add another order at minute 6
        order2 = Order(pickup=(0.0, 0.0), dropoff=(2.0, 2.0), request_time=6, window_start=6, window_end=15)
        self.sim.add_order(order2)
        self.sim.run(until=20)
        # order2 should not be assigned because rider is offline
        self.assertIsNone(order2.assigned_rider)
        self.assertEqual(order2.status, OrderStatus.PENDING)
        # Rider should be offline
        self.assertFalse(self.rider.online)
        self.assertEqual(self.rider.state, RiderState.OFFLINE)

    def test_multiple_riders(self):
        rider2 = Rider(location=(0.0, 0.0), base_location=(0.0, 0.0), star=4, capacity=1)
        self.sim.add_rider(rider2, online=True)
        order2 = Order(pickup=(0.0, 0.0), dropoff=(2.0, 2.0), request_time=2, window_start=2, window_end=15)
        self.sim.add_order(order2)
        self.sim.run(until=20)
        # Both orders should be completed
        self.assertEqual(self.order.status, OrderStatus.COMPLETED)
        self.assertEqual(order2.status, OrderStatus.COMPLETED)
        # Both riders should be idle and online
        self.assertEqual(self.rider.state, RiderState.IDLE)
        self.assertEqual(rider2.state, RiderState.IDLE)
        self.assertTrue(self.rider.online)
        self.assertTrue(rider2.online)

if __name__ == '__main__':
    unittest.main()
