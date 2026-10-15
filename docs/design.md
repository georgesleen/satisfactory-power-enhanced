# Design

## Goal

Vanilla power has one rule: total supply must exceed total demand. Distance,
layout, and grid shape do not matter. This mod makes power a spatial puzzle,
like belts and trains.

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

## Core mechanics

### Voltage tiers

| Tier | Wire | Unlock | Use |
|---|---|---|---|
| LV | Vanilla power line | Start | Factory floors, small generators |
| MV | New | Tier 3 (coal power) | Generator plants, links between factory blocks |
| HV | New wire and railways | Tier 6 (trains) | Long-distance transmission |
| SC | Superconductor | Tier 8 or 9 | Zero-loss, high-capacity trunk lines |

Machines connect at LV, as in vanilla. Each tier has a capacity. A large
generator plant exceeds LV capacity, so its output must leave on a higher tier.
Capacity values are open; see [Open decisions](#open-decisions).

### Railways

Railways carry power in vanilla. With this mod, a railway is an HV line. Each
train station has a built-in transformer between the railway and the station's
LV connector. When the player unlocks trains, the rail network becomes the
transmission backbone: a station can power an outpost from a central power
plant, so each outpost does not need its own plant.

### Tier-islands

A tier-island is a set of connected lines and buildings on one tier.
Transformers are the only links between islands. The capacity of an island is
the capacity of its tier. The mod solves power flow between islands only, not
along each line.

### Transformers

A transformer is the only link between two tier-islands. It has a MW rating,
and its load is visible on the building. An overload on one island does not
spread to another.

### Transmission loss

Loss on an island grows with its total line length and its load, and falls as
the tier goes up. Long LV runs lose a lot of power; HV lines across the map
lose little. Loss is the reason to step up for distance. Without loss, a
transformer is only a cost.

### Local overload

An overloaded island or transformer heats up visibly. After a delay, only that
island or transformer trips. Vanilla trips the whole circuit instead.

### Superconductors

Late-game wire (Tier 8 or 9) with zero loss and very high capacity. It is the
reward for building out a full grid.

Superconducting lines need cooling. Cryo stations along the line consume a
cooling supply (nitrogen or Cooling Systems). A line without cooling acts as a
normal line with high loss.

### Diagnostic tool and overlay

A handheld tool shows the tier, load, and loss of the line or building the
player looks at. An overlay colors lines by the load on their island.

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

## Decisions

- **Own mod.** TrueGrid puts rules on machines; this mod puts rules on wires.
  The core rules differ too much to share one mod. See
  [Prior art](prior-art.md).
- **Capacity per tier-island**, not per wire. The solve stays cheap on large
  factories.
- **Four tiers:** LV, MV, HV, SC.
- **Superconductors consume a cooling supply.**

## Open decisions

1. **Tier capacities**, the station transformer rating, and the exact SC
   milestone.
2. **Engine hooks.** Whether SML can replace the vanilla fuse and circuit
   logic cleanly. A prototype must answer this before the mechanics are fixed.
3. **Cooling supply.** Which items or fluids, the rate, and the station
   spacing.
