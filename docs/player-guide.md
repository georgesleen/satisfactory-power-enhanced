# Planned gameplay guide

This is a guide to the intended design, not a playable release or instructions
for working game features. Runtime transformer behavior still needs engine
ordering and energy-conservation verification. Ratings, loss tuning, and some
unlocks remain open. See [Design](design.md) and [Roadmap](roadmap.md).

## Keep ordinary factories ordinary

Machines keep their vanilla power connectors. You do not select a voltage for
each machine. Vanilla LV wires should comfortably run one reasonably sized
factory, including ordinary overclocking and normal pulses. You should not need
a transformer for every machine or small production block.

The aim is interesting challenges with interesting solutions, not a checklist
of matching fix-it boxes. Each problem should be recognizable in diagnostics
and offer at least two sensible approaches. A distant, extremely pulsed factory
could use an oversized feed, local fast storage, local generation, or split
feeds, trading space, logistics, and efficiency. Later unlocks must not
invalidate healthy LV wiring, and HV should remain viable beside cooled SC.

| Tier | Planned role |
|---|---|
| LV | Familiar local wiring throughout a factory |
| MV | Combine factories or generator sites and make regional links, starting around coal power |
| HV | Long-distance wire or railway transmission, starting around trains |
| SC | Late-game, zero-loss transmission with no capacity cap and a cooling supply |

Higher tiers solve distance and aggregation. A large plant exporting power to
several factories can justify a higher-tier backbone; that does not make higher
tiers mandatory inside each factory. Final LV, MV, and HV capacities will be
tuned against vanilla and Satisfactory Plus production at their respective
milestones.

## A simple shared grid

```text
Central generator plant
  -> step-up transformer
  -> HV wire or railway
  -> step-down transformer at the destination
  -> ordinary LV factory wiring
```

A railway station has a planned built-in transformer between its HV railway and
LV connector. This lets a central plant supply outposts along the train route.
Vanilla regenerative braking should continue returning energy through these
connections. The mod preserves that recovery; it does not invent another
source of train energy.

Connected wiring on one tier forms a tier-island. Transformers join islands
and have their own power ratings. Multiple transformers can share a load, but
if one trips, the remaining transformers need spare capacity to carry it.
Power shards raise transformer ratings at the cost of more heat and loss.

## Read warnings before rebuilding

The planned diagnostic tool shows tier, island load, and loss. The overlay
colors lines by their island's load, not a separately calculated current in
every branch. Dimming lights, rising hum, and a heating transformer warn before
a local trip.

- **High local load:** check the island and transformer rating. For an unusually
  large factory, split distribution or add capacity at the constrained link.
- **High loss on a long route:** step up for transmission and step down near the
  factory. Compact branches or local daisy chains should not be punished merely
  for having many connections.
- **A brief extreme peak:** add headroom or consider a fast buffer. Ordinary
  factory pulses should not force a capacitor at every machine.
- **A local trip:** identify the overloaded island or transformer, remove the
  overload, and restore that element. Other supplied islands should keep
  running. Loss of one shared transformer can still overload the survivors.

The loss distance metric is undecided. Total wire length is cheap but can
penalize dense factories; spatial extent or a path proxy can miss detours.
The chosen approximation must preserve useful long-distance upgrades without
turning short local wiring into a layout tax.

## Capacitors, batteries, and cooling

A planned capacitor bank is a **fast real-energy buffer** for extreme pulses.
It charges from spare supply and discharges during a peak, within its power
and stored-energy limits. More grid headroom is an equally valid alternative.
It cannot sustain a factory whose average demand exceeds supply.

Batteries store energy for longer shortages or outages. The capacitor's role
is fast peak support, not replacing sustained generation or battery reserves.
Neither creates energy.

This buffer uses MW for charge/discharge power and MWh for stored energy. It
is not a reactive power-factor correction bank, which would be rated in Mvar
and affect MVA loading. Power-factor correction would not supply free real
energy or remove all harmonic distortion.

SC lines instead need cryo stations consuming a cooling supply. With cooling,
they offer zero-loss transmission with no capacity cap and fast zipline travel.
The transformers at each end limit the power that an SC line carries. Without
cooling, a line stops superconducting and becomes a lossy line, which can trip.
The warm-state loss parameters, cooling item or fluid, consumption rate, station
spacing, and exact late-game unlock are not settled.

## Optional depth is not a requirement

Power Engineering research is planned for optional upgrades such as transformer
ratings and automatic reclosing. Frequency and power quality are candidates for
a fun/balance prototype, not committed gameplay:

- Fundamental frequency stability concerns changes in the base AC frequency,
  not extra frequency components in a distorted waveform.
- Displacement power factor concerns the phase offset of fundamental voltage
  and current; reactive power Q is measured in Mvar.
- Harmonics are waveform components at multiples of the fundamental. THD
  describes distortion; voltage and current THD are different readings.
- True power factor compares real MW with apparent MVA. Distortion as well as
  phase offset can reduce it, so reactive correction alone may not fix it.

The candidate interface would show island-level waveforms and spectra before
and after a change, clearly identifying approximations rather than claiming
branch-by-branch simulation. Possible choices include isolation, filtering,
or a different transmission arrangement. Neither a higher tier nor correction
capacitors should be treated as a universal fix. Do not assume every machine
is inductive or that a fictional machine's name proves its electrical behavior.

Capacitor resonance is only a possible mechanic if predictive feedback makes
the risk clear and warnings/local trips keep failure safe, with no equipment
destruction. Any power-quality feature must offer multiple useful solutions,
be visually understandable, and stay solved without periodic tuning. Ordinary
factories must remain comfortable on LV. Exact mechanics and tuning are open;
none of these concepts is a prerequisite for the planned core grid.

## Candidate: joining independent grids

Synchronization and asynchronous exchange are also fun/balance candidates, not
promised game mechanics. The starting idea is one nominal frequency, with
independent grids drifting in frequency and phase. This is not a proposal for
50/60 Hz machine compatibility settings. Transformer-connected voltage islands
in one synchronized AC grid would share a frequency.

- **AC intertie:** an automatic synchronizer matches voltage, frequency, and
  phase before joining grids. You gain shared supply and reserves, but
  disturbances may propagate between them.
- **HVDC exchange:** rated converters transfer power while the grids retain
  independent frequencies and phases. Conversion loss and build cost pay for
  this flexibility; it is not complete isolation from every fault or imbalance.
- **Stay isolated:** keep independent supply and reserves instead of exchanging
  power. This must remain a meaningful option.

A synchroscope and readiness indicators could explain synchronization, without
a manual breaker-timing minigame. Synchronization should be integrated into the
intertie if a separate box adds no decision, and stay solved without repeated
chores. Predictive feedback and safe trips, not equipment destruction, should
explain limits. Dynamics, ratings, and tuning remain open and must preserve
ordinary LV comfort before any candidate is accepted.
