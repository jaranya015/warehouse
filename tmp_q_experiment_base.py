import numpy as np
import time
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
import heapq
import random

warehouse = np.array([
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0],
    [0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0],
    [0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0],
    [0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0],
    [0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0],
    [0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0],
    [0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0],
    [0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0],
    [0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0],
    [0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0],
    [0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0]
])

def validate_points(warehouse, entrance, exit_point, pickup_points):
    if warehouse[entrance] != 0: raise ValueError("Entrance must be on walkway (0)")
    if warehouse[exit_point] != 0: raise ValueError("Exit must be on walkway (0)")
    for point in pickup_points:
        if warehouse[point] != 1: raise ValueError(f"Pickup point {point} must be on shelf (1)")

def generate_pickup_points(warehouse, n, seed=42):
    shelf_positions = list(zip(*np.where(warehouse == 1)))
    rng = np.random.default_rng(seed)
    selected_indices = rng.choice(len(shelf_positions), size=n, replace=False)
    return [shelf_positions[index] for index in selected_indices]

entrance = (0, 0)
exit_point = (17, 19)
n = 10

pickup_points = generate_pickup_points(warehouse=warehouse, n=n, seed=20)

validate_points(warehouse, entrance, exit_point, pickup_points)  

def get_valid_stand_positions(warehouse, item_pos):
    stand_positions = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dr, dc in directions:
        nr, nc = item_pos[0] + dr, item_pos[1] + dc
        if 0 <= nr < warehouse.shape[0] and 0 <= nc < warehouse.shape[1]:
            if warehouse[nr, nc] == 0:
                stand_positions.append((nr, nc))
    return stand_positions

def a_star_search(warehouse, starts, targets):
    def heuristic(pos):
        return min(abs(pos[0] - t[0]) + abs(pos[1] - t[1]) for t in targets)
    
    pq = []
    visited = set()
    counter = 0 
    for st in starts:
        heapq.heappush(pq, (heuristic(st), 0, counter, st, [st]))
        counter += 1
        
    while pq:
        f, g, _, curr, path = heapq.heappop(pq)
        
        if curr in targets:
            return g, path
            
        if curr in visited:
            continue
        visited.add(curr)
        
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = curr[0] + dr, curr[1] + dc
            if 0 <= nr < warehouse.shape[0] and 0 <= nc < warehouse.shape[1]:
                if warehouse[nr, nc] == 0 and (nr, nc) not in visited:
                    new_g = g + 1
                    new_f = new_g + heuristic((nr, nc))
                    heapq.heappush(pq, (new_f, new_g, counter, (nr, nc), path + [(nr, nc)]))
                    counter += 1
    return float('inf'), []

def build_distance_matrix(warehouse, entrance, exit_point, pickup_points):
    all_nodes = [entrance] + pickup_points + [exit_point]
    num_nodes = len(all_nodes)
    dist_matrix = np.zeros((num_nodes, num_nodes))
    valid_positions = []
    
    for i, node in enumerate(all_nodes):
        if i == 0 or i == num_nodes - 1:
            valid_positions.append([node])
        else:
            valid_positions.append(get_valid_stand_positions(warehouse, node))
            
    for i in range(num_nodes):
        for j in range(num_nodes):
            if i == j:
                dist_matrix[i][j] = 0
            elif i < j:
                dist, _ = a_star_search(warehouse, valid_positions[i], valid_positions[j])
                dist_matrix[i][j] = dist
                dist_matrix[j][i] = dist 
                
    return dist_matrix, valid_positions

def calculate_route_cost(route, dist_matrix):
    return sum(dist_matrix[route[i]][route[i+1]] for i in range(len(route)-1))

def q_learning_route(dist_matrix, episodes=10000, alpha=0.15, gamma=1.0,
                     epsilon_start=1.0, epsilon_end=0.02, seed=42):
    rng = np.random.default_rng(seed)
    n_nodes = len(dist_matrix)
    pickup_nodes = list(range(1, n_nodes - 1))
    full_mask = (1 << len(pickup_nodes)) - 1
    q, episode_costs = {}, []
    
    def q_values(state):
        if state not in q:
            q[state] = np.zeros(len(pickup_nodes), dtype=float)
        return q[state]
        
    for episode in range(episodes):
        epsilon = epsilon_end + (epsilon_start - epsilon_end) * (1 - episode / episodes)
        current, mask, total_cost = 0, 0, 0.0
        while mask != full_mask:
            state = (current, mask)
            available = [a for a in range(len(pickup_nodes)) if not (mask & (1 << a))]
            values = q_values(state)
            if rng.random() < epsilon:
                action = int(rng.choice(available))
            else:
                best = np.max(values[available])
                action = int(rng.choice([a for a in available if values[a] == best]))
            next_node = pickup_nodes[action]
            step_cost = dist_matrix[current, next_node]
            next_mask = mask | (1 << action)
            reward = -step_cost
            if next_mask == full_mask:
                reward -= dist_matrix[next_node, n_nodes - 1]
                future = 0.0
            else:
                next_available = [a for a in range(len(pickup_nodes)) if not (next_mask & (1 << a))]
                future = np.max(q_values((next_node, next_mask))[next_available])
            values[action] += alpha * (reward + gamma * future - values[action])
            total_cost += step_cost
            current, mask = next_node, next_mask
        episode_costs.append(total_cost + dist_matrix[current, n_nodes - 1])
        
    current, mask, route = 0, 0, [0]
    while mask != full_mask:
        available = [a for a in range(len(pickup_nodes)) if not (mask & (1 << a))]
        values = q_values((current, mask))
        action = int(available[np.argmax(values[available])])
        current = pickup_nodes[action]
        mask |= 1 << action
        route.append(current)
    route.append(n_nodes - 1)
    return route, calculate_route_cost(route, dist_matrix), episode_costs

def stitch_route(route, warehouse, valid_stands):
    path, stands = [], []
    for i in range(len(route) - 1):
        starts = valid_stands[route[i]] if i == 0 else [path[-1]]
        _, segment = a_star_search(warehouse, starts, valid_stands[route[i + 1]])
        path.extend(segment if i == 0 else segment[1:])
        if i < len(route) - 2:
            stands.append(segment[-1])
    return path, stands, len(path) - 1
