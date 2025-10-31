class Metrics:
    def __init__(self):
        self.deliveries = []
        self.on_time = 0
        self.late = 0
        self.total_delivery_time = 0.0
        self.count_delivery_time = 0
        self.total_distance_km = 0.0
        self.count_distance = 0
        self.rider_busy_time = {}  # rider_id -> busy minutes total

    def record_delivery(self, order, time_minute, distance_km: float = None):
        self.deliveries.append({'order_id': order.id, 'time': time_minute, 'window_end': getattr(order, 'window_end', None)})
        # on-time/late
        if getattr(order, 'window_end', None) is not None:
            if time_minute <= order.window_end:
                self.on_time += 1
            else:
                self.late += 1
        # delivery duration: prefer assigned_time if present
        if getattr(order, 'assigned_time', None) is not None and getattr(order, 'delivery_time', None) is not None:
            dur = order.delivery_time - order.assigned_time
            self.total_delivery_time += dur
            self.count_delivery_time += 1
        # distance
        if distance_km is not None:
            self.total_distance_km += distance_km
            self.count_distance += 1

    def summary(self, sim_time: int = None):
        total = len(self.deliveries)
        avg_delivery = (self.total_delivery_time / self.count_delivery_time) if self.count_delivery_time > 0 else 0.0
        avg_distance = (self.total_distance_km / self.count_distance) if self.count_distance > 0 else 0.0
        utilization_percent = None
        if self.rider_busy_time and sim_time:
            utilization_percent = {rid: round(100 * busy / sim_time, 2) for rid, busy in self.rider_busy_time.items()}
        return {
            'total_deliveries_count': total,
            'on_time_deliveries_count': self.on_time,
            'late_deliveries_count': self.late,
            'on_time_rate': (self.on_time / total) if total > 0 else 0.0,
            'avg_delivery_time_min': avg_delivery,
            'avg_distance_km': avg_distance,
            'rider_busy_time': self.rider_busy_time,
            'rider_utilization_percent': utilization_percent,
        }

    def record_rider_idle_period(self, rider, time_minute):
        # rider.busy_since should have start of busy period; compute busy duration until time_minute
        if getattr(rider, 'busy_since', None) is None:
            return
        busy = time_minute - rider.busy_since
        self.rider_busy_time[rider.id] = self.rider_busy_time.get(rider.id, 0) + busy
