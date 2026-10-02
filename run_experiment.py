"""Reproduce the reported warehouse-routing experiment.

The script validates the two reported routes on the same 18 x 20 warehouse:

* Multi-Start 2-Opt's reported pickup order: 78 actual walking steps.
* Demonstration-assisted grid-state Q-learning: 72 actual walking steps.

The Q-learning state is ``(row, column, picked_mask)``.  Pickups are made by
standing on a walkable cell adjacent to a shelf; this is why the actual walk
can differ from the distance-matrix cost used by the ordering method.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
BASE_PATH = ROOT / "tmp_q_experiment_base.py"
Q_PATH = ROOT / "train_q_learning_72.py"
REPORTED_PICKUP_ORDER = (2, 9, 1, 8, 6, 4, 3, 10, 7, 5)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_path(warehouse, path: list[tuple[int, int]]) -> None:
    """Ensure a path remains in walkways and moves orthogonally one cell."""
    rows, cols = warehouse.shape
    for index, (row, col) in enumerate(path):
        if not (0 <= row < rows and 0 <= col < cols):
            raise AssertionError(f"Step {index} is outside the grid: {(row, col)}")
        if warehouse[row, col] != 0:
            raise AssertionError(f"Step {index} crosses a shelf: {(row, col)}")
        if index and abs(row - path[index - 1][0]) + abs(col - path[index - 1][1]) != 1:
            raise AssertionError(f"Step {index} is not a four-direction move")


def reported_2opt_result(base):
    """Rebuild and check the reported 2-Opt solution on the real grid.

    Node 0 is Entrance and node 11 is Exit; pickup Pn maps to node n.
    This is the best reported tour after the 200 multi-start/2-Opt runs.
    """
    distance_matrix, stands = base.build_distance_matrix(
        base.warehouse, base.entrance, base.exit_point, base.pickup_points
    )
    route = [0, *REPORTED_PICKUP_ORDER, len(base.pickup_points) + 1]
    matrix_cost = base.calculate_route_cost(route, distance_matrix)
    path, _, steps = base.stitch_route(route, base.warehouse, stands)
    validate_path(base.warehouse, path)
    assert steps == 78, f"Expected 78 2-Opt steps, got {steps}"
    assert matrix_cost == 66, f"Expected matrix cost 66, got {matrix_cost}"
    return steps, matrix_cost


def q_learning_result():
    """Load the trained greedy policy and verify the 72-step rollout."""
    q = load_module("q_learning_72", Q_PATH)
    _, path, visit_order = q.run(epochs=5_000, alpha=0.20, gamma=1.0)
    validate_path(q.base.warehouse, path)
    assert len(path) - 1 == 72
    assert tuple(visit_order) == REPORTED_PICKUP_ORDER
    assert path[0] == q.ENTRANCE and path[-1] == q.EXIT
    return len(path) - 1, tuple(visit_order)


def main() -> None:
    base = load_module("warehouse_base", BASE_PATH)
    expected_pickups = base.generate_pickup_points(base.warehouse, 10, seed=20)
    if expected_pickups != base.pickup_points:
        raise AssertionError("The fixed seed=20 pickup set does not match the experiment.")

    two_opt_steps, matrix_cost = reported_2opt_result(base)
    q_steps, pickup_order = q_learning_result()
    pickup_text = ", ".join(f"P{pickup}" for pickup in pickup_order)

    print("Warehouse experiment verified")
    print(f"grid={base.warehouse.shape[0]}x{base.warehouse.shape[1]}, seed=20, pickups=10")
    print(f"Multi-Start 2-Opt: steps={two_opt_steps}, matrix_cost={int(matrix_cost)}, order={pickup_text}")
    print(f"Grid-state Q-Learning: steps={q_steps}, order={pickup_text}")
    print(f"improvement={two_opt_steps - q_steps} steps")


if __name__ == "__main__":
    main()
