"""
1D Method of Characteristics solver for tunnel pressure wave propagation.

Physics based on:
  - Riemann invariants for 1D compressible flow in a duct
  - Train entry/exit as step pressure sources
  - Open portals as full pressure reflection (inverted wave)
  - Wall friction via Darcy-Weisbach along train body
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple


GAMMA = 1.4          # ratio of specific heats for air
R_AIR = 287.0        # J/(kg·K)
T0 = 293.15          # ambient temperature, K
P0 = 101325.0        # ambient pressure, Pa
RHO0 = P0 / (R_AIR * T0)
C0 = np.sqrt(GAMMA * R_AIR * T0)   # speed of sound ~343 m/s


@dataclass
class TunnelParams:
    length: float           # m
    area: float = 50.0      # m²  (cross-section)
    friction_coeff: float = 0.02   # Darcy-Weisbach f

@dataclass
class TrainParams:
    length: float           # m
    area: float = 10.0      # m²  (frontal area)
    speed: float = 55.56    # m/s  (~200 km/h)

    @property
    def blockage_ratio(self) -> float:
        return self.area / 50.0   # train area / tunnel area


@dataclass
class SimulationResult:
    time: np.ndarray
    x_nodes: np.ndarray
    pressure: np.ndarray        # shape (n_time, n_nodes)  [Pa gauge]
    scenario: str = ""
    peak_pressure: float = 0.0
    peak_suction: float = 0.0

    def summary(self) -> str:
        return (
            f"Scenario: {self.scenario}\n"
            f"  Peak overpressure : {self.peak_pressure/1000:.2f} kPa\n"
            f"  Peak underpressure: {self.peak_suction/1000:.2f} kPa\n"
            f"  Duration simulated: {self.time[-1]:.1f} s\n"
        )


def _entry_pressure_rise(train: TrainParams) -> float:
    """
    Approximate pressure rise when train nose enters tunnel portal.
    Simplified Riemann solution for piston entry into a duct.
    """
    phi = train.blockage_ratio
    delta_p = 0.5 * RHO0 * train.speed**2 * phi / (1 - phi)
    return delta_p


def run_1d_moc(
    tunnel: TunnelParams,
    train: TrainParams,
    crossing_point: float,          # 0..1 fraction along tunnel where trains cross
    n_nodes: int = 200,
    dt_factor: float = 0.9,
    t_end: float | None = None,
) -> SimulationResult:
    """
    Run 1D MOC simulation for a single-train or crossing scenario.

    Uses finite-difference MOC on a uniform grid.
    Wave speed = C0 (acoustic approximation — valid for M_train < 0.4).
    """
    dx = tunnel.length / (n_nodes - 1)
    dt = dt_factor * dx / C0           # CFL condition
    if t_end is None:
        # simulate until train has fully traversed + 2 round-trip times
        t_end = tunnel.length / train.speed + 4 * tunnel.length / C0

    x = np.linspace(0.0, tunnel.length, n_nodes)
    n_steps = int(t_end / dt) + 1

    # state arrays: forward (R+) and backward (R-) Riemann invariants
    r_plus  = np.zeros(n_nodes)   # forward-running wave
    r_minus = np.zeros(n_nodes)   # backward-running wave

    pressure_history = np.zeros((n_steps, n_nodes))
    time_arr = np.arange(n_steps) * dt

    # precompute train-nose and tail positions vs time
    nose_x  = train.speed * time_arr                        # train 1 (enters from x=0)
    tail_x  = nose_x - train.length
    # pressure wave magnitudes
    dp_entry  =  _entry_pressure_rise(train)
    dp_exit   = -dp_entry * 0.7   # rarefaction when tail exits (empirical ~70%)

    fired_entry  = False
    fired_exit   = False

    for k in range(n_steps):
        t = time_arr[k]

        # ---- source terms: train entry / exit ----
        if not fired_entry and nose_x[k] >= 0 and nose_x[k] <= dx:
            # impulsive pressure rise at portal x=0
            r_plus[0] += dp_entry / (RHO0 * C0)
            fired_entry = True

        if not fired_exit and tail_x[k] >= 0 and tail_x[k] <= dx:
            r_plus[0] += dp_exit / (RHO0 * C0)
            fired_exit = True

        # ---- friction attenuation along train body ----
        friction_loss = (tunnel.friction_coeff * dx / (4 * np.sqrt(tunnel.area / np.pi))
                         * RHO0 * (train.speed ** 2) / 2)
        # apply small exponential damping per step on waves inside train span
        for i in range(n_nodes):
            if tail_x[k] < x[i] < nose_x[k]:
                r_plus[i]  *= (1 - 0.001 * friction_loss / dp_entry)
                r_minus[i] *= (1 - 0.001 * friction_loss / dp_entry)

        # ---- advect waves one step ----
        r_plus_new  = np.zeros(n_nodes)
        r_minus_new = np.zeros(n_nodes)

        # forward wave moves right
        r_plus_new[1:]  = r_plus[:-1]
        # backward wave moves left
        r_minus_new[:-1] = r_minus[1:]

        # ---- boundary conditions (open portals → full reflection, sign flip) ----
        # x=0 portal: r_minus reflected as r_plus with opposite sign
        r_plus_new[0]  = -r_minus[1]
        # x=L portal: r_plus reflected as r_minus with opposite sign
        r_minus_new[-1] = -r_plus[-2]

        r_plus  = r_plus_new
        r_minus = r_minus_new

        # ---- reconstruct gauge pressure ----
        pressure_history[k, :] = RHO0 * C0 * (r_plus - r_minus) / 2

    result = SimulationResult(
        time=time_arr,
        x_nodes=x,
        pressure=pressure_history,
        scenario=f"L={tunnel.length}m train={train.length}m xing@{crossing_point:.0%}",
        peak_pressure=float(pressure_history.max()),
        peak_suction=float(pressure_history.min()),
    )
    return result
