> **⚠️ Proprietary — All Rights Reserved.** © 2026 Sandeep Grover. This repository is licensed to Sandeep Grover and may **not** be used, run, copied, modified, distributed, or used to train models without prior written permission. Public visibility does not grant a license. See [LICENSE](LICENSE).

---

# Tunnel Pressure Wave Simulator

1D Method of Characteristics (MOC) solver for pressure wave propagation inside railway tunnels. Designed for parametric batch studies of two-train crossing scenarios.

## Architecture

```
main.py           - CLI entry point, argument parsing
batch_runner.py   - parametric sweep over tunnel/train/crossing combos
moc_solver.py     - 1D MOC physics engine (Riemann invariants, portal BCs, friction)
results/          - CSV output from batch runs
```

## Physics Model

- **1D compressible flow** using forward (R+) and backward (R-) Riemann invariants
- **Wave speed**: speed of sound C0 ~343 m/s (valid for train Mach < 0.4)
- **Pressure source**: step pressure rise at nose entry, rarefaction at tail exit
  - `ΔP_entry = 0.5 * ρ * v² * φ / (1 - φ)`  where φ = blockage ratio
- **Portal boundary conditions**: open portals → full wave reflection with sign inversion
- **Friction**: Darcy-Weisbach attenuation along train body
- **CFL stability**: dt = 0.9 * dx / C0

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Default: 27 simulations (3 tunnels x 3 trains x 3 crossing points)
python main.py

# Custom batch
python main.py \
  --tunnels 500 1000 2000 \
  --trains 100 200 \
  --crossings 0.25 0.5 0.75 \
  --speed 55.56 \
  --output results/my_study.csv
```

## Output

CSV with columns: `sim_id`, `tunnel_length_m`, `train_length_m`, `crossing_point_pct`, `train_speed_kmh`, `peak_overpressure_kPa`, `peak_underpressure_kPa`, `sim_duration_s`

## Limitations

- Acoustic approximation (linearised): accurate for train speeds up to ~150 km/h; at higher speeds use non-linear MOC
- Does not model cross-passages or pressure relief ducts
- Single-train model (crossing modelled via doubled source term at mid-tunnel)

## Author

Dr. Sandeep Grover - computational simulation specialist
