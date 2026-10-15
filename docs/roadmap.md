# Roadmap

Each phase must be fun on its own. A later phase must not be needed to make an
earlier one work.

## Phase 0: technical spike

- Set up an SML C++ mod project for the current game version.
- Find the hooks for circuit rebuild, power balance, and fuse trip.
- Prove that the mod can split one vanilla circuit and limit the power flow
  between the parts.
- Measure the cost of the tier-island solve on a large save.

## Phase 1: critical path (MVP)

- MV and HV wires and poles. The vanilla line is LV.
- Railways as HV lines, with a built-in transformer in each train station.
- Transformers with a MW rating.
- Tier capacities.
- Transmission loss by length, load, and tier.
- Local overload: heat warning, then a trip of the overloaded element only.
- Superconducting lines with cryo stations that consume a cooling supply.
- Diagnostic tool and load overlay.
- Unlocks tied to the vanilla milestones.

## Phase 2: grid dynamics

- Brownout: when a line sags, machines on it run slower instead of stopping.
- Generator ramp rates: base load and peaker plants.
- Black start: a small generator or battery bank to restart a dead grid.
- Load shedding that extends the vanilla priority switch.
- Frequency and inertia, if they stay readable in play.

## Phase 3: late game and buildings

- Substation buildings and parts.
- Pumped hydro storage that uses pipes and terrain height.
- Flywheels.
- Control room building with a grid diagram.

## Phase 4: long distance

- HVDC links between grids that are not in sync.
- Underground and submarine cable.

## Not planned

- Voltage or current type per machine.
- Three-phase balancing.
- Harmonics.
- Random equipment failure.
- Reactive power, unless a version appears that is visible and has no
  per-machine work.
