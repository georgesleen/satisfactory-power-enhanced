# Design

## Goal

Vanilla power has one rule: total supply must exceed total demand. Distance,
layout, and grid shape do not matter. This mod makes power a spatial puzzle,
like belts and trains.

This document specifies planned gameplay, not working game behavior. The runtime
transformer implementation is blocked until engine update ordering and energy
conservation are proven.

## Principles

1. **Fun first, realism second.** Real grid behavior is a source of ideas, not
   a requirement.
2. **Rules live on wires, not machines.** Machines have no voltage tier and no
   current type. The player never configures power per machine.
3. **Every mechanic gives a reason to build something.** Substations,
   transmission lines, and storage are things players want to make look good.
4. **Failures are readable.** The cause shows on the object: a hot
   transformer, a glowing line, a slow machine.
5. **Fail soft before hard.** An overload warns first, then trips only the
   overloaded element. A full blackout is rare.
6. **Visibility is part of the core.** A mechanic without in-game feedback does
   not ship.
7. **Complexity, not tedium.** A mechanic adds decisions, not actions. It
   must pass four checks:
   - The work grows with the number of decisions, not the number of machines.
   - A solved problem stays solved: build it once, blueprint it, and forget it.
   - A failure is readable, and one action fixes it.
   - Optional depth is opt-in: MAM research, presets, or automation.

8. **Interesting challenges and interesting solutions, designed together.**
   The player should say, "I want this because it solves my problem." Each
   phenomenon needs a recognizable consequence, legible diagnostics, and at
   least two sensible approaches with tradeoffs, not a bad number followed by
   its mandatory matching box. Its purpose must stand without appeals to
   realism or progression. Unlocks add capabilities, never retroactively
   invalidate a healthy LV factory, and do not create a checklist of devices.

### Feature motivations

These are balance aims, not a requirement to use every technique. Power-quality
and independent-grid features remain candidates. For example, a distant factory
with extreme pulses could use an oversized feed, local fast storage, local
generation, or split feeds. Compare space, logistics, and efficiency costs;
design the challenge and its competing solutions in the same playtest.

| Feature | Problem it should help solve | Alternative or tradeoff |
|---|---|---|
| Higher voltage | Move aggregated power farther with less loss | Local generation or shorter routes; LV remains comfortable locally |
| Transformer | Interface ordinary factory wiring with a shared transmission grid | Keep a local grid; rate the interface for the chosen demand |
| MW/MWh fast buffer | Serve extreme short peaks without oversizing the whole supply | Extra headroom or rescheduling; batteries for longer deficits |
| Power-factor correction | Recover constrained apparent-power capacity where phase offset matters | More capacity or load separation; not a universal energy-saving fix |
| Harmonic mitigation | Solve a demonstrable converter-district loading or waveform problem | Filtering, isolation, or layout changes; not an abstract pollution tax |
| AC synchronization | Share supply and reserves between independent grids | Keep local reserves or use asynchronous exchange; joining can spread disturbances |
| HVDC | Exchange power without coupling frequency and phase | AC sharing or isolation; converter capacity, cost, and losses |
| SC | Compact high-capacity, efficient transmission | Cooling logistics and build cost; HV remains a viable alternative |

Reject arbitrary cryo-station spacing chores, research needed merely to remove
inflated loss penalties, and compulsory synchronization boxes with no decision.
Integrate or cut such requirements rather than making players service a rule.
Cooling and research must buy a useful choice, not repair an intentionally
unpleasant baseline.

## Core mechanics

### Voltage tiers

| Tier | Wire | Unlock | Use |
|---|---|---|---|
| LV | Vanilla power line | Start | Ordinary wiring throughout a reasonably sized factory |
| MV | New | Tier 3 (coal power) | Aggregating factories and generator sites; regional links |
| HV | New wire and railways | Tier 6 (trains) | Long-distance transmission and larger shared backbones |
| SC | Superconductor | Tier 8 or 9 | Zero-loss, high-capacity trunk lines |

Machines connect at LV, as in vanilla. Vanilla wires must comfortably support a
single reasonably sized factory, including ordinary overclocking and normal
pulses. A transformer per machine or small production block is not the intended
play loop. MV and HV earn their place through distance and aggregation, not
artificially cramped local wiring.

Each tier has a capacity. A large generator plant collecting output for several
factories can outgrow LV; this does not mean an ordinary factory or small local
generator site must upgrade. Capacity values remain open and must pass the
[balance acceptance scenarios](#balance-acceptance-scenarios), not an invented
fixed MW cap.

### Railways

Railways carry power in vanilla. With this mod, a railway is an HV line. Each
train station has a built-in transformer between the railway and the station's
LV connector. When the player unlocks trains, the rail network becomes the
transmission backbone: a station can power an outpost from a central power
plant, so each outpost does not need its own plant.

Vanilla already exposes regenerative braking and returns power to the railway
under dynamic braking. Preserve that behavior across station transformers; the
mod does not add a second regeneration source.

### Tier-islands

A tier-island is a set of connected lines and buildings on one tier.
Transformers are the only links between islands. The capacity of an island is
the capacity of its tier. The mod solves power flow between islands only, not
along each line.

### Transformers

A transformer is the only link between two tier-islands. It has a MW rating,
and its load is visible on the building. An overload on one island does not
spread to another.

Two or more transformers can feed one island and share its load. If one
trips, the others take its load and can trip in turn. Spare capacity or a
ring layout prevents the cascade.

A power shard in a transformer raises its rating. Each shard also raises its
heat and loss.

### Transmission loss

Loss grows with load and transmission distance, and falls as the tier goes up.
Long LV runs should give a useful reason to step up; HV should carry power
across the map efficiently. Short, dense local wiring must not incur punitive
loss solely because it has many branches or daisy-chain links.

The island model is chosen; its distance metric is not. Total wire length is
cheap and accounts for every span, but can unfairly charge a compact factory
for all its internal wiring. Spatial extent or a path-length proxy better
represents transmission distance, but can undercount detours or separate
branches. Choose and measure a cheap proxy against local and long-distance
layouts before fixing the loss formula. This is not a per-wire flow solve.

### Local overload

An overloaded island or transformer heats up visibly. After a delay, only that
island or transformer trips. Vanilla trips the whole circuit instead.

### Load spikes and capacitor banks

The particle accelerator, converter, and quantum encoder pulse their power
draw. Capacity checks must account for peaks, but ordinary factory pulses and
ordinary overclocking belong within comfortable LV operation.

For extreme pulsed loads, a capacitor bank is an optional alternative to extra
grid and transformer headroom. It charges when supply headroom is available and
discharges during peaks, within its stored energy and charge/discharge limits.
It cannot cover a sustained supply deficit or create energy. Capacitors are
not mandatory equipment for each pulsing machine; batteries serve longer
energy-storage needs.

Here, "capacitor bank" means a fast real-energy buffer, rated by charge/discharge
power in MW and stored energy in MWh. It is not a reactive power-factor
correction bank, whose ratings would use Mvar and whose circuit loading would
involve MVA. Power-factor correction is not committed; it would not provide
free real energy or automatically remove harmonic distortion. Machine names
alone do not establish their electrical power factor.

### Superconductors

Late-game wire (Tier 8 or 9) with zero loss and very high capacity. It is the
reward for building out a full grid.

Superconducting lines need cooling. Cryo stations along the line consume a
cooling supply (nitrogen or Cooling Systems). A line without cooling acts as a
normal line with high loss.

A pioneer on a zipline moves faster on a higher tier. On an SC line, the
zipline is fast travel.

### Three ways to move power

| Method | Strength | Cost |
|---|---|---|
| HV wire | Cheap and flexible | Loss over distance; towers to build |
| Railway | Free with the train network | Capacity limited by the station transformer |
| SC line | Zero loss, very high capacity, fast zipline travel | Expensive; needs a cooling supply |

### Diagnostic tool and overlay

A handheld tool shows the tier, load, and loss of the line or building the
player looks at. An overlay colors lines by the load on their island.

### Ambient feedback

- Lights on an island dim when the island nears capacity and flicker before a
  trip.
- Lines sag and hum more as load rises. Transformers buzz louder as they heat.
- A trip makes an arc flash and a bang.

### Power Engineering research

A MAM research tree holds optional upgrades: lower loss, more tolerance before
a trip, higher transformer ratings, and breakers that reclose automatically.
Depth that not every player wants goes here, so the base rules stay simple.

## Constraints

- **Daisy chains.** Satisfactory 1.2 lets power flow from building to building
  ("Upgraded Power Connectors"). Capacity rules must cover these links.
- **Solver cost.** A full power-flow solve on a large factory every tick is too
  slow. The model must stay cheap on factories with tens of thousands of
  buildings.
- **Saves.** The mod must define what happens when a player adds it to an
  existing save or removes it.
- **Multiplayer.** New grid state must replicate to clients.
- **Satisfactory Plus.** The mod must work inside
  [Satisfactory Plus](prior-art.md#satisfactory-plus). S+ replaces recipes and
  generators. Rules must key on wires, poles, railways, and transformers, never
  on generator or machine classes. Recipes, unlocks, and the cooling supply
  must be data that an S+ compatibility pack can replace.

## Balance acceptance scenarios

These are future playtest gates, not measured results. Record actual recipes,
machine counts, clocks, average and peak demand, layout, distance, and losses.
Use representative production targets at each milestone, not a tiny fixture
chosen to fit a predetermined cap. Tune capacities and loss together; no final
MW ratings are specified here.

| Milestone | Vanilla scenario | Satisfactory Plus scenario | Acceptance |
|---|---|---|---|
| Local production | Coal-era iron and steel component factory with miners, smelters, foundries, constructors, and assemblers | A complete early iron-component factory using S+ recipes and generators at its corresponding power milestone | Ordinary LV wiring supports the whole factory comfortably, including routine overclocking and normal cycling; no transformer per production block |
| Regional growth | Train-era aluminum factory supplied by its local distribution network | A representative intermediate metals and chemical production factory at the S+ regional-power milestone | A single reasonably sized factory remains practical on LV; aggregating several such factories or generator sites gives MV/HV a useful role |
| Transmission | Central generator plant feeding several distant factory outposts over HV wire and railway station transformers | Central S+ generation supplying separated production sites at the corresponding transmission unlock | Stepping up materially reduces long-distance loss; stepping down restores ordinary LV factory wiring without machine configuration |
| Late pulses | Late-game factory containing particle accelerators, converters, or quantum encoders | A late S+ production factory with its actual peak-load recipes, including pulsed consumers where present | Normal operation does not require a capacitor at every machine; an extreme synchronized peak can be served by extra headroom or a suitably sized capacitor bank |

For both recipe sets, compare compact pole branches and building daisy chains
with the same demand and similar footprint. Neither should fail merely because
it has more local connections. Then move the supply far away without changing
the factory: distance should make transmission upgrades useful. Also test a
large collecting generator plant separately from one ordinary factory so its
export demand does not become the baseline LV requirement.

An extreme-load test must show a readable warning before a local trip and
explain which island or transformer exceeded its rating. A capacitor test must
show depletion under sustained deficit and account for charging energy. Railway
tests must preserve vanilla regeneration through station transformers without
counting it twice.

## Candidate: power quality as a visible puzzle

Power factor and harmonic distortion deserve a fun/balance prototype, not a
blanket exclusion or a commitment to ship. Keep these concepts distinct:

- **Fundamental frequency stability:** the base AC frequency changing over time;
  a supply/demand and inertia concept, not harmonic content.
- **Displacement power factor and reactive power Q:** phase offset between
  fundamental voltage and current. Reactive correction can address suitable
  loads; Q uses Mvar, while apparent power uses MVA.
- **Harmonics and THD:** waveform components at multiples of the fundamental;
  total harmonic distortion measures their contribution relative to the
  fundamental. Voltage and current distortion must be labeled separately.
- **True power factor:** real power divided by apparent power. Both phase offset
  and waveform distortion can reduce it; correcting displacement alone does
  not necessarily restore true power factor.

Explore island-level diagnostics with clearly labeled illustrative waveforms
and frequency spectra, comparing before/after a proposed intervention. These
must not pretend the island solver resolves every branch waveform. Machine
electrical classifications need evidence, not assumptions that every motor
input or fictional machine is an inductive load.

Candidate solutions include isolating troublesome loads, filtering, and changing
transmission/distribution arrangements. Their useful effects need demonstration,
not an assumption that a higher tier cures distortion. Reactive correction
capacitors are not universal filters or the fast MW/MWh pulse buffers.
Capacitor resonance is a possible decision only if a predictive UI can explain
it before construction; failures must warn and trip safely, never destroy
equipment.

Prototype gates: several meaningful solutions rather than one mandatory device;
visually legible cause and effect; set-and-forget designs with no periodic
retuning; and ordinary factories remaining comfortable on LV. Compare solutions
in the vanilla and S+ balance scenarios. Exact penalties, sources, equations,
unlocks, and whether any of these mechanics ship remain undecided.

## Candidate: synchronizing independent grids

Explore frequency drift and synchronization with the same fun-first prototype
status as power quality. Start with one nominal frequency; independently
operating grids may drift enough to make reconnecting a meaningful decision.
Do not introduce fixed 50/60 Hz machine compatibility rules or per-machine
settings.

A frequency domain is not a voltage tier-island: transformer-connected tier
islands in a synchronized AC grid share a fundamental frequency. Independent
grids may have different instantaneous frequencies and phases. Compare three
choices:

| Choice | Benefit | Tradeoff |
|---|---|---|
| AC intertie with automatic synchronization | Share generation and reserves once joined | Voltage, frequency, and phase must match before closing; disturbances can propagate through the joined grid |
| HVDC asynchronous coupling | Transfer power between grids whose frequency and phase remain independent | Rated converter transfer, conversion loss, and build cost; not magical isolation from every fault or power imbalance |
| Keep grids isolated | Avoid dependence on a shared intertie and limit propagation | Each grid needs its own supply and reserves; no power exchange |

An automatic synchronizer should match voltage, frequency, and phase, then
close safely. A synchroscope and explicit readiness indicators could make this
legible, not turn it into a manual breaker-timing minigame. Integrate the
synchronizer into the intertie if a separate building would only be a checkbox.
Ordinary local wiring and transformer placement must not require repeated
synchronization actions.

Prototype gates: demonstrate reconnecting drifting grids, shared-reserve
benefits and disturbance tradeoffs, and useful isolated/HVDC alternatives.
Show intertie loading, readiness, and transfer limits before committing a
connection; warn and trip safely rather than destroy equipment. Preserve
set-and-forget operation and ordinary LV comfort. Exact dynamics, tolerances,
ratings, costs, unlocks, and whether these mechanics ship remain open.

## Decisions

- **Own mod.** TrueGrid puts rules on machines; this mod puts rules on wires.
  The core rules differ too much to share one mod. See
  [Prior art](prior-art.md).
- **Capacity per tier-island**, not per wire. The solve stays cheap on large
  factories.
- **Four tiers:** LV, MV, HV, SC.
- **Superconductors consume a cooling supply.**
- **LV factory comfort.** Ordinary factories, overclocking, and normal pulses
  fit vanilla wiring; higher tiers address distance and aggregation.
- **Capacitors are optional peak support**, not a requirement per machine.

## Open decisions

1. **Tier capacities**, the station transformer rating, and the exact SC
   milestone.
2. **Engine hooks.** Whether SML can replace the vanilla fuse and circuit
   logic cleanly. A prototype must answer this before the mechanics are fixed.
3. **Cooling supply.** Which items or fluids, the rate, and the station
   spacing.
4. **Loss distance metric.** Total wire length versus spatial extent or a
   path-length proxy, subject to the compact-factory acceptance scenarios.
5. **Power quality and frequency.** Prototype frequency/inertia, displacement
   and true power factor, harmonic diagnostics, and synchronization/intertie
   choices against the candidate gates above. None is committed gameplay or a
   prerequisite for the core grid.
