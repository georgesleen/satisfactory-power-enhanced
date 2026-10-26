# Roadmap

Each phase must be fun on its own. A later phase must not be needed to make an
earlier one work.

All phases describe planned gameplay, not implemented game features. The core
energy accounting is host-tested. Runtime transformers remain gated on the
engine questions in [Development](development.md#open-engine-questions).

Design interesting challenges and competing solutions together. Each phenomenon
must have a recognizable consequence, legible diagnostics, and at least two
sensible approaches with tradeoffs, not a bad number requiring its matching
box. The player should say "I want this because it solves my problem", without
appeals to realism or progression. Unlocks add capabilities and never
retroactively invalidate a healthy LV factory.

## Phase 0: technical spike

- Set up an SML C++ mod project for the current game version.
- Find the hooks for circuit rebuild, power balance, and fuse trip.
- Prove that the mod can split one vanilla circuit and limit the power flow
  between the parts.
- Measure the cost of the tier-island solve on a large save.
- Run the transformer probe on a dedicated server to verify transfer order and
  conservation in the engine.
- Verify bidirectional railway power, preserving vanilla regeneration without
  creating or double-counting it.

## Phase 1: core grid

- MV and HV wires and poles. The vanilla line is LV.
- Railways as HV lines, with a built-in transformer in each train station.
- Transformers with a MW rating.
- Load sharing between transformers, with cascade trips.
- Transformer overclocking with power shards.
- Tier capacities for LV, MV, and HV.
- Transmission loss by load, tier, and a distance metric validated against
  compact local wiring.
- Local overload: heat warning, then a trip of the overloaded element only.
- Optional capacitor banks for extreme pulsed loads, as an alternative to extra
  headroom, not mandatory equipment for every machine.
- Superconducting lines with no capacity cap and cryo stations that consume a
  cooling supply; a line without cooling stops superconducting.
- Zipline speed by tier.
- Ambient feedback: lights dim and flicker, lines sag and hum, trips flash.
- Diagnostic tool and load overlay.
- Unlocks tied to the vanilla milestones.
- Implement the transformer, capacitor-bank and cryo-station interaction menus
  before minimal tier, loading and feeding-transformer additions to vanilla
  power-pole menus. Follow the [UI specification](ui-spec.md); the real-core
  browser reference is not native UMG/FactoryGame integration.
- Follow the [art direction](art-direction.md) for equipment. Accept UVs,
  baked materials, LODs, collision and exports through the
  [asset pipeline](asset-pipeline.md), then verify real equipment imports and
  building behavior in the target engine.

### Player-facing acceptance

- Run the [design balance scenarios](design.md#balance-acceptance-scenarios)
  with recorded vanilla and Satisfactory Plus recipes at their respective
  milestones before fixing tier capacities.
- One reasonably sized factory runs comfortably on vanilla LV wires, including
  ordinary overclocking and normal pulses. No per-machine tier configuration or
  transformer per small block is needed.
- MV/HV provide value when aggregating factories or generator sites and when
  spanning long distances, not because ordinary local wiring is crippled.
- Compare compact pole branches and building daisy chains at equal load and
  footprint. Branch count alone must not create punitive loss. Extending the
  supply route should make stepping up worthwhile.
- Demonstrate warnings before local trips, identify the overloaded element,
  and verify unaffected islands stay supplied where upstream capacity remains.
- Compare extra headroom with a charged capacitor under an extreme peak.
  Verify finite stored energy, charging demand, and depletion under sustained
  deficit. Neither approach should be mandatory for every ordinary machine.
- Verify station transformers preserve native railway regeneration in both
  accounting and delivered energy.
- Verify diagnostics report the chosen island-level approximation honestly,
  rather than pretending to measure independently solved branch currents.
- Validate [feature motivations](design.md#feature-motivations) in play.
  Keep HV viable beside SC; reject arbitrary cooling-station spacing,
  penalty-removal research, or compulsory synchronization boxes that add no
  choice. Integrate or cut chores instead of tuning around them.

## Phase 2: grid dynamics

- Brownout: when a line sags, machines on it run slower instead of stopping.
- Generator ramp rates: base load and peaker plants.
- Black start: a small generator or battery bank to restart a dead grid.
- Load shedding that extends the vanilla priority switch.
- Retain the verified vanilla regeneration behavior as grid dynamics expand.
- Power Engineering MAM research tree.
- Prototype frequency stability/inertia and power-quality candidates against the
  [design gates](design.md#candidate-power-quality-as-a-visible-puzzle), without
  committing them to gameplay.

### Power-quality candidate acceptance

- Distinguish fundamental frequency stability, displacement power factor and
  reactive Q, waveform harmonics/THD, and distortion's effect on true power
  factor. Do not classify every machine as inductive.
- Show island-level waveform and spectrum comparisons before/after changes,
  labeling voltage versus current distortion and any illustrative approximation.
- Compare meaningful alternatives such as isolation, filtering, and
  transmission arrangements. Neither correction capacitors nor higher tiers
  are universal cures; MW/MWh pulse buffering remains a separate function.
- Consider capacitor resonance only with predictive feedback and safe warning/
  trip behavior, never destruction.
- Require visually legible decisions, several viable solutions, and
  set-and-forget operation without periodic tuning. Re-run the ordinary-LV
  factory comfort scenarios for vanilla and S+ before accepting any penalty.
- Leave exact mechanics and tuning undecided until a fun/balance prototype
  demonstrates these criteria.

## Phase 3: late game and buildings

- Substation buildings and parts.
- Pumped hydro storage that uses pipes and terrain height.
- Flywheels.
- Control room building with a grid diagram.

## Phase 4: long distance

- Prototype [independent-grid interties](design.md#candidate-synchronizing-independent-grids):
  automatic AC synchronization versus HVDC coupling versus staying isolated.
  These dynamics are candidates, not promised shipped mechanics.
- Underground and submarine cable.

### Synchronization candidate acceptance

- Start with one nominal frequency and independently drifting grids, not fixed
  50/60 Hz compatibility or machine-specific settings. Distinguish frequency
  domains from transformer-connected voltage tier-islands.
- Match voltage, frequency, and phase automatically before closing an AC
  intertie. Compare shared reserves against propagated disturbances.
- Demonstrate rated HVDC transfer with independent frequency/phase, converter
  losses, and build costs; do not claim complete fault isolation.
- Show readiness, loading, and limits with clear predictive feedback, optionally
  a synchroscope. Require safe trips, no destruction or manual breaker-timing
  minigame, and no repeated synchronization chores.
- Integrate synchronization into the intertie if a separate building adds no
  decision. Require meaningful AC, HVDC, and isolated choices, set-and-forget
  operation, and ordinary LV comfort before fixing dynamics or capacities.

## Not planned

- Voltage or current type per machine.
- Three-phase balancing.
- Random equipment failure.
