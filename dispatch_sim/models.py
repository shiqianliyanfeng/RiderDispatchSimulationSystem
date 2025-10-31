from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import uuid


class RiderState(Enum):
    OFFLINE = "offline"
    ONLINE = "online"
    IDLE = "idle"
    ASSIGNED = "assigned"
    DELIVERING = "delivering"
    RETURNING = "returning"


class OrderStatus(Enum):
    CREATED = "created"
    ARRIVED = "arrived"
    PENDING = "pending"
    ASSIGNED = "assigned"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Rider:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    star: int = 3
    state: RiderState = RiderState.OFFLINE
    online: bool = False
    location: tuple = (0.0, 0.0)
    base_location: tuple = (0.0, 0.0)
    capacity: int = 3
    assigned_orders: list = field(default_factory=list)
    available_at: int = 0  # minute when rider will be free
    busy_since: Optional[int] = None

    def can_take(self):
        return self.online and self.state == RiderState.IDLE and len(self.assigned_orders) < self.capacity

    def go_online(self):
        self.online = True
        self.state = RiderState.IDLE

    def go_offline(self):
        self.online = False
        self.state = RiderState.OFFLINE


@dataclass
class Order:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pickup: tuple = (0.0, 0.0)
    dropoff: tuple = (0.0, 0.0)
    request_time: int = 0  # minutes since simulation start
    window_start: Optional[int] = None  # earliest delivery minute (for appointment)
    window_end: Optional[int] = None  # latest delivery minute
    assigned_rider: Optional[str] = None
    status: OrderStatus = OrderStatus.CREATED
    order_type: str = "immediate"  # 'immediate' or 'appointment'
    assigned_time: Optional[int] = None
    pickup_time: Optional[int] = None
    delivery_time: Optional[int] = None
    pickup_duration: int = 1  # minutes spent at pickup (dwell)
    est_pickup_time: Optional[int] = None
    est_delivery_time: Optional[int] = None
