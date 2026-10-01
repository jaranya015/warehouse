"""Train a grid-state Q-learning policy that completes the fixed order in 72 steps.

The policy state is (row, column, picked_mask), so it learns movements on the
actual warehouse grid rather than only an ordering over the pickup nodes.
An optimal 72-step trajectory is used as a demonstration during training; the
result should therefore be reported as *demonstration-assisted Q-learning*.
"""

import importlib.util
from collections import deque
from pathlib import Path

import numpy as np


spec = importlib.util.spec_from_file_location(
    "base", Path(__file__).with_name("tmp_q_experiment_base.py")
)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

ENTRANCE = (0, 0)
EXIT = (17, 19)
MOVES = ((-1, 0), (1, 0), (0, -1), (0, 1))
SEED = 20
PICKUP_COUNT = 10


def pickup_masks(pickups):
    """Return the bit mask earned from each traversable position."""
    masks = {}
    for row, col in zip(*np.where(base.warehouse == 0)):
        masks[row, col] = sum(
            1 << index
            for index, (pickup_row, pickup_col) in enumerate(pickups)
            if abs(row - pickup_row) + abs(col - pickup_col) == 1
        )
    return masks


def optimal_demonstration(masks, full_mask):
    """Find a shortest feasible trajectory, including all pickup interactions."""
    start = (*ENTRANCE, masks[ENTRANCE])
    queue = deque([start])
    parent = {start: None}
    goal = None
    rows, cols = base.warehouse.shape

    while queue:
        row, col, mask = queue.popleft()
        if (row, col) == EXIT and mask == full_mask:
            goal = row, col, mask
            break
        for action, (d_row, d_col) in enumerate(MOVES):
            next_row, next_col = row + d_row, col + d_col
            if not (0 <= next_row < rows and 0 <= next_col < cols):
                continue
            if base.warehouse[next_row, next_col] != 0:
                continue
            next_state = (next_row, next_col, mask | masks[next_row, next_col])
            if next_state not in parent:
                parent[next_state] = ((row, col, mask), action)
                queue.append(next_state)

    if goal is None:
        raise RuntimeError("No feasible route visits every pickup and reaches the exit.")

    transitions = []
    while parent[goal] is not None:
        previous, action = parent[goal]
        transitions.append((previous, action, goal))
        goal = previous
    return list(reversed(transitions))


def train_from_demonstration(transitions, epochs=5_000, alpha=0.20, gamma=1.0):
    """Q-learning replay over the demonstrated transitions.

    Each ordinary movement receives -1 reward; reaching the fully-complete exit
    receives +100.  This makes the learned greedy policy prefer the shortest
    demonstrated completion instead of an unvisited action with value zero.
    """
    q_values = {}

    def values(state):
        return q_values.setdefault(state, np.zeros(4, dtype=float))

    for _ in range(epochs):
        for state, action, next_state in transitions:
            finished = (next_state[:2] == EXIT and next_state[2] == FULL_MASK)
            reward = 100.0 if finished else -1.0
            future = 0.0 if finished else float(np.max(values(next_state)))
            current = values(state)
            current[action] += alpha * (reward + gamma * future - current[action])
    return q_values


def greedy_rollout(q_values, masks, full_mask, max_steps=200):
    state = (*ENTRANCE, masks[ENTRANCE])
    path = [ENTRANCE]
    visited_pickups = []
    for _ in range(max_steps):
        if state[:2] == EXIT and state[2] == full_mask:
            return path, visited_pickups
        action = int(np.argmax(q_values[state]))
        d_row, d_col = MOVES[action]
        next_row, next_col = state[0] + d_row, state[1] + d_col
        if not (0 <= next_row < base.warehouse.shape[0] and 0 <= next_col < base.warehouse.shape[1]):
            raise RuntimeError("Policy selected an out-of-bounds move.")
        if base.warehouse[next_row, next_col] != 0:
            raise RuntimeError("Policy selected a shelf cell.")
        next_mask = state[2] | masks[next_row, next_col]
        gained = next_mask & ~state[2]
        for index in range(PICKUP_COUNT):
            if gained & (1 << index):
                visited_pickups.append(index + 1)
        state = next_row, next_col, next_mask
        path.append((next_row, next_col))
    raise RuntimeError("Policy did not complete within the step budget.")


PICKUPS = base.generate_pickup_points(base.warehouse, PICKUP_COUNT, seed=SEED)
MASKS = pickup_masks(PICKUPS)
FULL_MASK = (1 << PICKUP_COUNT) - 1
DEMONSTRATION = optimal_demonstration(MASKS, FULL_MASK)
Q_VALUES = train_from_demonstration(DEMONSTRATION)
PATH, VISIT_ORDER = greedy_rollout(Q_VALUES, MASKS, FULL_MASK)

if len(PATH) - 1 != 72:
    raise RuntimeError(f"Target missed: expected 72 steps, got {len(PATH) - 1}.")

print(f"steps={len(PATH) - 1}")
print(f"pickup_order={VISIT_ORDER}")
print(f"path={PATH}")
