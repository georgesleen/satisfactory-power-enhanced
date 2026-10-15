# Prior art

## Satisfactory mods

### TrueGrid

[ficsit.app](https://ficsit.app/mod/TrueGrid),
[source](https://github.com/lazypsyco/TrueGrid). The closest existing mod.

- Five tiers: LV 500 MW, MV 1 GW, HV 5 GW, SV 30 GW, QV 60 GW.
- Transformers between tiers and converters between current types.
- Each machine type needs AC or DC.
- At most three generators per circuit.
- Options: reactive power with capacitors and inductors, distance loss,
  conversion loss, and a minimum voltage.
- Distance loss lowers the capacity of a whole circuit by its size, not the
  loss along each line.
- The repository has no license, so its code cannot be reused.
- Small user base: about 1.4k downloads in October 2026, in the bottom quarter
  of ficsit.app mods by downloads.

This mod differs from TrueGrid in its core rule: no tiers or current types on
machines, and no generator cap.

### Satisfactory Plus

[ficsit.app](https://ficsit.app/mod/SatisfactoryPlus). A full overhaul in
alpha, about 250k downloads in October 2026. Target host for this mod.

- Needs a new save.
- Replaces most recipes and adds new ores and production chains.
- Rebuilds power generation on Refined Power; does not change transmission.
- Keeps tiers 0 to 9 and adds a tier 10.
- Turns off conflicting mods automatically; other mods load but have no
  support.
- Cross-mod compatibility uses KPatchwork packs built on KDataForge.
- No multiplayer support yet.

### Adjacent mods

- [Refined Power](https://ficsit.app/mod/RefinedPower): new generators; does
  not change how power moves.
- [Power Checker](https://ficsit.app/mod/PowerChecker),
  [Power Control Room](https://ficsit.app/mod/PowerControlRoom): grid
  monitors.
- [Peaker Power Plants](https://ficsit.app/mod/PeakerMod): generators that
  follow demand.
- [Power Tower Plus](https://ficsit.app/mod/PowerTowerPlus),
  [Cable Choices Plus](https://ficsit.app/mod/AB_CableMod): range and looks
  only.
- [Wireless Power](https://ficsit.app/mod/WirelessPower),
  [Universal Power](https://ficsit.app/mod/UniversalPower): remove wiring.
- No existing mod adds superconductors.

## Other games

| Source | Mechanic | Lesson |
|---|---|---|
| Immersive Engineering (Minecraft) | LV, MV, and HV wires on connectors; transformers; loss grows with wire length. | Tiers on wires and connectors feel physical. Closest model for this mod. |
| Oxygen Not Included | Machines have no tier; wires have a wattage cap; transformers protect sub-grids; overloads damage only the overloaded wire. | "This wire is too small here" is easy to read and fun. |
| Create (Minecraft) | Stress budget per network; goggles show the numbers. | A clear budget plus a diagnostic tool. |
| GregTech, IC2 (Minecraft) | Every machine has a voltage; overvoltage destroys machines; cables lose power per block. | Rules on machines become busywork. Avoid. |
| Mekanism, Thermal (Minecraft) | Cable tiers set throughput; no voltage. | Simple, but gives no decisions. |
| GregTech superconductors | Late-game zero-loss cable. | A good late-game reward. |
