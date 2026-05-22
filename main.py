"""
Tunnel Pressure Wave Simulator - entry point.

Usage:
    # Run default demo (3 tunnel lengths x 3 train lengths x 3 crossing points = 27 sims)
    python main.py

    # Custom batch
    python main.py --tunnels 500 1000 2000 --trains 100 200 --crossings 0.25 0.5 0.75
"""

import argparse
from batch_runner import run_batch


DEFAULT_TUNNEL_LENGTHS  = [500, 1000, 2000]     # metres
DEFAULT_TRAIN_LENGTHS   = [100, 150, 200]        # metres
DEFAULT_CROSSING_POINTS = [0.25, 0.50, 0.75]    # fraction along tunnel


def main():
    parser = argparse.ArgumentParser(description="1D tunnel pressure wave batch simulator")
    parser.add_argument("--tunnels",   nargs="+", type=float, default=DEFAULT_TUNNEL_LENGTHS,
                        help="Tunnel lengths in metres")
    parser.add_argument("--trains",    nargs="+", type=float, default=DEFAULT_TRAIN_LENGTHS,
                        help="Train lengths in metres")
    parser.add_argument("--crossings", nargs="+", type=float, default=DEFAULT_CROSSING_POINTS,
                        help="Crossing points as fractions 0..1")
    parser.add_argument("--speed",     type=float, default=55.56,
                        help="Train speed in m/s (default 200 km/h)")
    parser.add_argument("--output",    type=str,   default="results/batch_results.csv",
                        help="Path for CSV output")
    args = parser.parse_args()

    rows = run_batch(
        tunnel_lengths  = args.tunnels,
        train_lengths   = args.trains,
        crossing_points = args.crossings,
        train_speed     = args.speed,
        output_csv      = args.output,
    )

    print(f"\nSummary: {len(rows)} simulations completed.")
    peak_ops = max(r["peak_overpressure_kPa"]  for r in rows)
    peak_und = min(r["peak_underpressure_kPa"] for r in rows)
    print(f"  Worst overpressure : {peak_ops:.3f} kPa")
    print(f"  Worst underpressure: {peak_und:.3f} kPa")


if __name__ == "__main__":
    main()
