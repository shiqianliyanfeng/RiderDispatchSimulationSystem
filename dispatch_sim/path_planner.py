import math


class PathPlanner:
    """Very small path/time estimator using Euclidean distance."""

    def nearest_neighbor_route(self, start: tuple, points: list) -> list:
        """Return a greedy route visiting all points from start."""
        route = []
        current = start
        remaining = points[:]
        while remaining:
            next_pt = min(remaining, key=lambda p: self.distance_km(current, p))
            route.append(next_pt)
            current = next_pt
            remaining.remove(next_pt)
        return route

    def insertion_heuristic(self, start: tuple, points: list) -> list:
        """Build route by repeated cheapest insertion."""
        if not points:
            return []
        route = [points[0]]
        for p in points[1:]:
            best_pos = None
            best_increase = float('inf')
            for i in range(len(route) + 1):
                prev = start if i == 0 else route[i - 1]
                nxt = route[i] if i < len(route) else None
                increase = self.distance_km(prev, p)
                if nxt is not None:
                    increase += self.distance_km(p, nxt) - self.distance_km(prev, nxt)
                if increase < best_increase:
                    best_increase = increase
                    best_pos = i
            route.insert(best_pos, p)
        return route

    def two_opt(self, route: list) -> list:
        """Simple 2-opt local search to improve route (list of points)."""
        improved = True
        best = route[:]
        while improved:
            improved = False
            for i in range(0, len(best) - 2):
                for j in range(i + 2, len(best)):
                    new_route = best[:i + 1] + best[i + 1:j + 1][::-1] + best[j + 1:]
                    old_dist = sum(self.distance_km(best[k], best[k + 1]) for k in range(len(best) - 1))
                    new_dist = sum(self.distance_km(new_route[k], new_route[k + 1]) for k in range(len(new_route) - 1))
                    if new_dist + 1e-6 < old_dist:
                        best = new_route
                        improved = True
                        break
                if improved:
                    break
        return best

    def distance_km(self, a: tuple, b: tuple) -> float:
        dx = a[0] - b[0]
        dy = a[1] - b[1]
        return math.sqrt(dx * dx + dy * dy)

    def travel_time_minutes(self, a: tuple, b: tuple, speed_kmh: float = 60.0) -> float:
        dist_km = self.distance_km(a, b)
        # speed in km per minute
        speed_km_per_min = speed_kmh / 60.0
        if speed_km_per_min <= 0:
            return float('inf')
        return dist_km / speed_km_per_min
