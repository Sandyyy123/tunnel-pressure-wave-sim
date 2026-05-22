"""
Parametric batch runner for tunnel pressure wave simulations.

Sweeps over tunnel lengths, train lengths, and crossing points,
collecting peak pressures and writing results to CSV.
"""

import csv
import itertools
from pathlib import Path
from typing import List, Dict, Any

from moc_solver import TunnelParams, TrainParams, run_1d_moc


def run_batch(
    tunnel_lengths: List[float],
    train_lengths: List[float],
    crossing_points: List[float],   # fractions 0..1
    train_speed: float = 55.56,     # m/s
    output_csv: str = "results/batch_results.csv",
) -> List[Dict[str, Any]]:
    """
    Run all combinations and return list of result dicts.
    Also writes a CSV for easy import into Excel / reporting tools.
    """
    Path(output_csv).parent.mkdir(exist_ok=True)

    rows = []
    combos = list(itertools.product(tunnel_lengths, train_lengths, crossing_points))
    total = len(combos)

    print(f"Running {total} simulation(s)...\n")

    for idx, (tl, tnl, xp) in enumerate(combos, 1):
        tunnel = TunnelParams(length=tl)
        train  = TrainParams(length=tnl, speed=train_speed)
        result = run_1d_moc(tunnel, train, crossing_point=xp)

        row = {
            "sim_id":             idx,
            "tunnel_length_m":    tl,
            "train_length_m":     tnl,
            "crossing_point_pct": round(xp * 100, 1),
            "train_speed_kmh":    round(train_speed * 3.6, 1),
            "peak_overpressure_kPa":   round(result.peak_pressure / 1000, 3),
            "peak_underpressure_kPa":  round(result.peak_suction  / 1000, 3),
            "sim_duration_s":     round(result.time[-1], 2),
        }
        rows.append(row)
        print(f"  [{idx:>3}/{total}] {result.summary().strip()}")

    # write CSV
    fieldnames = list(rows[0].keys())
    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nResults saved to: {output_csv}")
    return rows
