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

| Tier | Wire | Use |
|---|---|---|
| LV | Vanilla power line | Factory floors, small generators |
| MV | New | Generator plants, links between factory blocks |
| HV | New | Long-distance transmission |
| SC | Superconductor, late game | Zero-loss, high-capacity trunk lines |

Machines connect at LV, as in vanilla. Each tier has a capacity. A large
generator plant exceeds LV capacity, so its output must leave on a higher tier.
Capacity values are open; see [Open decisions](#open-decisions).

### Transformers

A transformer is the only link between two tiers. It has a MW rating, and its
load is visible on the building. A transformer splits the grid into separate
tier-islands, so an overload on one island does not spread to another.

### Transmission loss

Loss grows with line length and load, and falls as the tier goes up. Long LV
runs lose a lot of power; HV lines across the map lose little. Loss is the
reason to step up for distance. Without loss, a transformer is only a cost.

### Local overload

An overloaded line or transformer heats up visibly. After a delay, only that
element trips. Vanilla trips the whole circuit instead.

### Superconductors

Late-game wire (Tier 8 or 9) with zero loss and very high capacity. It is the
reward for building out a full grid.

### Diagnostic tool and overlay

A handheld tool shows the tier, load, and loss of the line or building the
player looks at. An overlay colors lines by load.

## Constraints

- **Daisy chains.** Satisfactory 1.2 lets power flow from building to building
  ("Upgraded Power Connectors"). Capacity rules must cover these links.
- **Solver cost.** A full power-flow solve on a large factory every tick is too
  slow. The model must stay cheap on factories with tens of thousands of
  buildings.
- **Saves.** The mod must define what happens when a player adds it to an
  existing save or removes it.
- **Multiplayer.** New grid state must replicate to clients.

## Open decisions

1. **Own mod or contribute to TrueGrid.** TrueGrid already does tiers and
   transformers, with rules on machines. See [Prior art](prior-art.md).
   Leaning: own mod, because the core rules differ.
2. **Capacity model.**
   - Per wire: more spatial and tactile; needs a flow solve on the wire graph.
   - Per tier-island: each island between transformers is one node, capped by
     its weakest line; cheap, less tactile.
3. **Superconductor upkeep.**
   - A cooling supply that the line consumes (nitrogen or Cooling Systems at
     each station); without cooling, the line acts as a normal high-loss line.
   - A build cost only, with no running upkeep.
4. **Tier capacities and unlock milestones.**
5. **Engine hooks.** Whether SML can replace the vanilla fuse and circuit
   logic cleanly. A prototype must answer this before the mechanics are fixed.
