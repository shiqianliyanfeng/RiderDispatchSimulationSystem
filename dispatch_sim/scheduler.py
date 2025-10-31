from typing import List
from .models import Rider, Order, RiderState, OrderStatus
from .path_planner import PathPlanner
import logging

logger = logging.getLogger(__name__)

# Try to import OR-Tools; if not installed, fall back to greedy solver
try:
    from ortools.constraint_solver import pywrapcp
    ORTOOLS_AVAILABLE = True
except Exception:
    ORTOOLS_AVAILABLE = False


class Scheduler:
    def __init__(self, riders: List[Rider], planner: PathPlanner):
        self.riders = riders
        self.planner = planner

    def dispatch(self, orders: List[Order], current_time: int):
        """Dispatch considering time windows. """
        # Only consider orders that are pending for assignment
        unassigned = [o for o in orders if o.assigned_rider is None and o.status == OrderStatus.PENDING]

        # sort by deadline (appointment first)
        def deadline(o: Order):
            return o.window_end if o.window_end is not None else current_time

        unassigned.sort(key=deadline)

        # Only consider online and idle riders
        idle_riders = [r for r in self.riders if r.online and r.state == RiderState.IDLE and r.can_take()]

        if ORTOOLS_AVAILABLE and idle_riders and unassigned:
            try:
                depots = [(0.0, 0.0)]
                dropoffs = [o.dropoff for o in unassigned]
                locations = depots + dropoffs
                num_depots = len(depots)
                num_dropoffs = len(dropoffs)
                num_nodes = len(locations)

                dist_matrix = [[int(self.planner.travel_time_minutes(locations[i], locations[j])) for j in range(num_nodes)] for i in range(num_nodes)]

                manager = pywrapcp.RoutingIndexManager(num_nodes, len(idle_riders), 0)
                routing = pywrapcp.RoutingModel(manager)

                def time_callback(from_index, to_index):
                    return dist_matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

                transit_callback_index = routing.RegisterTransitCallback(time_callback)
                routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

                routing.AddDimension(transit_callback_index, 30, 99999, False, "Time")
                time_dimension = routing.GetDimensionOrDie("Time")

                for i in range(num_nodes):
                    if i == 0:
                        time_dimension.CumulVar(manager.NodeToIndex(0)).SetRange(current_time, 99999)
                        print(f"Depot : time window [{current_time}, 99999]")
                    else:
                        o = unassigned[i - 1]
                        start = o.window_start if o.window_start is not None else o.request_time
                        end = o.window_end if o.window_end is not None else 99999
                        time_dimension.CumulVar(manager.NodeToIndex(i)).SetRange(start, end)
                        print(f"Order {o.id}: time window [{start}, {end}], dropoff {o.dropoff}")

                # Add capacity constraint
                def demand_callback(from_index):
                    node = manager.IndexToNode(from_index)
                    if node == 0:
                        return 0  # depot
                    else:
                        return 1  # each order has demand 1
                demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
                routing.AddDimensionWithVehicleCapacity(
                    demand_callback_index,
                    0,  # null capacity slack
                    [r.capacity for r in idle_riders],  # vehicle capacities
                    True,  # start cumul to zero
                    "Capacity"
                )
                capacity_dimension = routing.GetDimensionOrDie("Capacity")

                search_parameters = pywrapcp.DefaultRoutingSearchParameters()
                search_parameters.time_limit.seconds = 10
                search_parameters.log_search = True  # 启用详细求解日志
                solution = routing.SolveWithParameters(search_parameters)

                if solution:
                    assignments = []
                    for vidx, rider in enumerate(idle_riders):
                        rider.assigned_orders = []
                        idx = routing.Start(vidx)
                        batch_orders = []
                        while not routing.IsEnd(idx):
                            node = manager.IndexToNode(idx)
                            if node >= 1:
                                order = unassigned[node - 1]
                                eta = solution.Min(time_dimension.CumulVar(idx))
                                # 可选：if order.window_end is not None and eta > order.window_end: continue
                                order.assigned_rider = rider.id
                                order.status = OrderStatus.ASSIGNED
                                order.est_delivery_time = eta
                                batch_orders.append(order)
                            idx = solution.Value(routing.NextVar(idx))
                        if batch_orders:
                            rider.state = RiderState.ASSIGNED
                            rider.assigned_orders = batch_orders
                            logger.info("Assigned batch %s to rider %s", [o.id for o in batch_orders], rider.id)
                            assignments.append((rider, batch_orders))
                    return assignments
                else:
                    return self.dispatch_greedy(orders, current_time)
            except Exception as e:
                import traceback
                logger.warning("ORTOOLS scheduling failed, falling back to greedy.")
                traceback.print_exc()
                return self.dispatch_greedy(orders, current_time)
        else:
            return self.dispatch_greedy(orders, current_time)
        
    def dispatch_greedy(self, orders: List[Order], current_time: int):
        assignments = []
        # Build a mutable pool of unassigned orders
        candidate_pool = [o for o in orders if o.assigned_rider is None and o.status == OrderStatus.PENDING]
        for r in self.riders:
            if not (r.online and r.state == RiderState.IDLE and r.can_take()):
                continue
            # Sort by earliest window_end (deadline), then request_time
            candidate_orders = sorted(
                candidate_pool,
                key=lambda o: (o.window_end if o.window_end is not None else float('inf'), o.request_time)
            )
            batch = []
            current_time_cursor = current_time
            current_loc = r.location
            for o in candidate_orders:
                if len(batch) >= r.capacity:
                    break
                # Estimate arrival time at this order
                travel = int(round(self.planner.travel_time_minutes(current_loc, o.dropoff)))
                eta = current_time_cursor + travel
                # Check time window feasibility
                if o.window_end is not None and eta > o.window_end + 5:
                    continue
                batch.append((o, eta))
                current_time_cursor = eta
                current_loc = o.dropoff
            if batch:
                # Route optimization: get dropoff points and re-sequence with insertion + 2-opt
                dropoffs = [o.dropoff for o, _ in batch]
                route = self.planner.insertion_heuristic(r.location, dropoffs)
                route = self.planner.two_opt(route)
                # Recompute ETAs for optimized route
                current_time_cursor = current_time
                current_loc = r.location
                batch_final = []
                for pt in route:
                    o = next(x for x, _ in batch if x.dropoff == pt)
                    travel = int(round(self.planner.travel_time_minutes(current_loc, pt)))
                    eta = current_time_cursor + travel
                    if o.window_end is not None and eta > o.window_end + 5:
                        continue
                    batch_final.append((o, eta))
                    current_time_cursor = eta
                    current_loc = pt
                # Assign
                for (o, eta) in batch_final:
                    o.assigned_rider = r.id
                    o.status = OrderStatus.ASSIGNED
                    o.est_delivery_time = eta
                    r.assigned_orders.append(o)
                r.state = RiderState.ASSIGNED
                logger.info("Assigned batch %s to rider %s", [o.id for o, _ in batch_final], r.id)
                assignments.append((r, [o for o, _ in batch_final]))
                # Remove assigned orders from candidate pool
                assigned_ids = set(o.id for o, _ in batch_final)
                candidate_pool = [o for o in candidate_pool if o.id not in assigned_ids]
        return assignments
