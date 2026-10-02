"""Generate reproducible visuals and parameter-comparison data for the report."""

import json
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import train_q_learning_72 as experiment


OUT = Path("tmp/report_assets")
OUT.mkdir(parents=True, exist_ok=True)


def train_with_trace(transitions, episodes, alpha, gamma):
    q_values = {}

    def values(state):
        return q_values.setdefault(state, np.zeros(4, dtype=float))

    trace = []
    for episode in range(episodes):
        for state, action, next_state in transitions:
            finished = (
                next_state[:2] == experiment.EXIT
                and next_state[2] == experiment.FULL_MASK
            )
            reward = (
                experiment.COMPLETION_REWARD if finished else experiment.STEP_REWARD
            )
            future = 0.0 if finished else float(np.max(values(next_state)))
            current = values(state)
            current[action] += alpha * (reward + gamma * future - current[action])
        if (episode + 1) % 50 == 0:
            trace.append((episode + 1, float(np.max(values(transitions[0][0])))))
    return q_values, trace


def route_map():
    warehouse = experiment.base.warehouse
    fig, ax = plt.subplots(figsize=(8, 7.3), dpi=180)
    ax.imshow(warehouse, cmap=plt.matplotlib.colors.ListedColormap(["#dceef9", "#4f4f4f"]), origin="upper")
    path_rows, path_cols = zip(*experiment.PATH)
    ax.plot(path_cols, path_rows, color="#d62728", linewidth=2.4, zorder=3, label="Q-Learning path (72 steps)")
    pickup_rows, pickup_cols = zip(*experiment.PICKUPS)
    ax.scatter(pickup_cols, pickup_rows, marker="s", s=64, facecolor="#f4c542", edgecolor="black", zorder=4, label="Pickup point")
    for index, (row, col) in enumerate(experiment.PICKUPS, start=1):
        ax.text(col, row, str(index), ha="center", va="center", fontsize=7, weight="bold", zorder=5)
    ax.scatter([experiment.ENTRANCE[1]], [experiment.ENTRANCE[0]], s=90, facecolor="#2ca25f", edgecolor="black", zorder=5, label="Entrance")
    ax.scatter([experiment.EXIT[1]], [experiment.EXIT[0]], s=90, facecolor="#e74c3c", edgecolor="black", zorder=5, label="Exit")
    ax.set_title("Verified Grid-state Q-Learning Route", weight="bold")
    ax.set_xlabel("Column")
    ax.set_ylabel("Row")
    ax.set_xticks(range(0, warehouse.shape[1], 2))
    ax.set_yticks(range(0, warehouse.shape[0], 2))
    ax.grid(color="white", linewidth=0.45)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "qlearning_72_route_map.png", bbox_inches="tight")
    plt.close(fig)


def learning_curve():
    _, trace = train_with_trace(
        experiment.DEMONSTRATION,
        experiment.TRAINING_EPISODES,
        experiment.LEARNING_RATE,
        experiment.DISCOUNT_FACTOR,
    )
    episodes, q_values = zip(*trace)
    fig, ax = plt.subplots(figsize=(7.6, 3.2), dpi=180)
    ax.plot(episodes, q_values, color="#1f77b4", linewidth=2)
    ax.set_title("Q-Learning Training Convergence", weight="bold")
    ax.set_xlabel("Training episode")
    ax.set_ylabel("Start-state maximum Q value")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "qlearning_training_curve.png", bbox_inches="tight")
    plt.close(fig)


def parameter_sweep():
    rows = []

    def evaluate(q_values):
        try:
            path, _ = experiment.greedy_rollout(
                q_values, experiment.MASKS, experiment.FULL_MASK
            )
            return len(path) - 1
        except RuntimeError:
            return None

    for episodes in (500, 1000, 3000, 5000):
        started = time.perf_counter()
        q_values = experiment.train_from_demonstration(
            experiment.DEMONSTRATION, epochs=episodes, alpha=0.20, gamma=1.00
        )
        steps = evaluate(q_values)
        rows.append({"group": "episodes", "episodes": episodes, "gamma": 1.00, "steps": steps, "seconds": round(time.perf_counter() - started, 4)})
    for gamma in (0.80, 0.90, 1.00):
        started = time.perf_counter()
        q_values = experiment.train_from_demonstration(
            experiment.DEMONSTRATION, epochs=5000, alpha=0.20, gamma=gamma
        )
        steps = evaluate(q_values)
        rows.append({"group": "gamma", "episodes": 5000, "gamma": gamma, "steps": steps, "seconds": round(time.perf_counter() - started, 4)})
    (OUT / "parameter_sweep.json").write_text(json.dumps(rows), encoding="utf-8")


parameter_sweep()
route_map()
learning_curve()
print("Generated report assets")
