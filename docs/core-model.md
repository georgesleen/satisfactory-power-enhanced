# Core model

The core is the engine-free simulation code in `Source/EnhancedPowerCore/`. It
holds the rules that must be exact: units, transformer heat and trips, fast
buffers, transformer energy accounting, island loss, distance proxies, and
transformer topology. Unreal glue calls these functions; it does not repeat
their math.

This document is the contract. The implementation and the tests are written
from it independently.

## Conventions

- Language: C++20. No Unreal headers, no exceptions thrown, no global state.
- Namespace: `EnhancedPower`. All declarations below live in it.
- Headers: `Source/EnhancedPowerCore/Public/EnhancedPowerCore/<Name>.h`.
- Sources: `Source/EnhancedPowerCore/Private/<Name>.cpp`.
- `Export.h` defines an empty `ENHANCEDPOWERCORE_API` only when the build has
  not defined it. Non-inline function declarations carry this macro for the
  Unreal runtime module; host builds need no engine headers or DLL machinery.
- Functions are pure: they read their arguments and return a value. They never
  write through a parameter.
- Floating point is `double`. Tests compare with an absolute tolerance of
  `1e-9` unless a section states otherwise.
- "Precondition" means the caller guarantees it. Numeric inputs are finite
  unless a section explicitly specifies non-finite behavior. Only the stated
  clamping and special-input rules are part of the contract.

## Units (`Units.h`)

```cpp
struct Megawatts  { double Value = 0.0; };
struct Megajoules { double Value = 0.0; };
struct Seconds    { double Value = 0.0; };
struct Meters     { double Value = 0.0; };
```

Each type supports, as `constexpr` free or friend functions:

- `+`, `-` between two values of the same type, and unary `-`.
- `*` and `/` by a `double` (both `X * double` and `double * X`; division
  only as `X / double`).
- `X / X` returns `double`.
- Defaulted `operator<=>` and `operator==`.

Cross-unit operations:

- `Megawatts * Seconds` and `Seconds * Megawatts` return `Megajoules`.
- `Megajoules / Seconds` returns `Megawatts`.
- `Megajoules / Megawatts` returns `Seconds`.

No implicit conversion exists between units or from `double`.

## Thermal (`Thermal.h`)

Transformer heat. Heat is dimensionless. A transformer at its rating settles at
heat 1.

```cpp
struct ThermalParameters {
    Seconds TimeConstant;
    double WarningHeat = 1.0;
    double TripHeat = 1.44;
};
struct ThermalState {
    double Heat = 0.0;
    bool Tripped = false;
};
enum class ThermalStatus { Normal, Warning, Tripped };

ThermalState StepThermal(const ThermalParameters& Parameters, const ThermalState& State,
                         double LoadRatio, Seconds Delta);
ThermalStatus ClassifyThermal(const ThermalParameters& Parameters, const ThermalState& State);
std::optional<Seconds> TimeToTrip(const ThermalParameters& Parameters, const ThermalState& State,
                                  double LoadRatio);
std::optional<ThermalState> TryResetThermal(const ThermalParameters& Parameters,
                                            const ThermalState& State);
```

Preconditions: `TimeConstant > 0`, `0 < WarningHeat < TripHeat`.

`StepThermal`:

1. If `Delta <= 0`, return `State` unchanged.
2. `r = max(LoadRatio, 0)`. A negative or NaN ratio counts as 0.
3. `AlreadyTripped = State.Tripped || State.Heat >= TripHeat`.
   `Target = AlreadyTripped ? 0 : r * r`.
4. `Heat' = Target + (State.Heat - Target) * exp(-Delta / TimeConstant)`.
   If `!AlreadyTripped`, `Target <= TripHeat`, and rounding makes
   `Heat' >= TripHeat`, use `nextafter(TripHeat, 0)` instead. A trajectory
   approaching the trip threshold from below must not trip through rounding.
5. `Tripped' = AlreadyTripped || Heat' >= TripHeat`.
6. Return `{Heat', Tripped'}`.

The exact exponential makes one step of `2 * d` equal two steps of `d` when
the ratio does not change and no trip occurs.

`ClassifyThermal`: `Tripped` if `State.Tripped` or `State.Heat >= TripHeat`;
else `Warning` if `State.Heat >= WarningHeat`; else `Normal`.

`TimeToTrip` gives the time until a trip if `LoadRatio` stays constant:

- If `State.Tripped` or `State.Heat >= TripHeat`, return `Seconds{0}`.
- `r = max(LoadRatio, 0)`; if `r * r <= TripHeat`, return `std::nullopt`
  (the load never trips).
- Else return `TimeConstant * ln((r*r - Heat) / (r*r - TripHeat))`.

`TryResetThermal` is the manual breaker reset:

- If `!State.Tripped`, return `State` unchanged.
- If `State.Heat >= WarningHeat`, return `std::nullopt` (still too hot).
- Else return `{State.Heat, false}`.

## Fast buffer (`FastBuffer.h`)

A capacitor bank: small, fast energy storage for short peaks.

```cpp
struct BufferParameters {
    Megajoules Capacity;
    Megawatts MaxCharge;
    Megawatts MaxDischarge;
    double ChargeEfficiency = 1.0;
};
struct BufferState {
    Megajoules Stored;
};
struct BufferStep {
    BufferState State;
    Megawatts Absorbed;
    Megawatts Delivered;
};

BufferStep StepBuffer(const BufferParameters& Parameters, const BufferState& State,
                      Megawatts Balance, Seconds Delta);
```

`Balance` is the island balance without the buffer: positive is surplus,
negative is deficit. Preconditions: `Capacity >= 0`, `MaxCharge >= 0`,
`MaxDischarge >= 0`, `0 < ChargeEfficiency <= 1`.

1. `S = clamp(State.Stored, 0, Capacity)`.
2. If `Delta <= 0` or `Balance == 0`, return `{{S}, 0, 0}`.
3. Deficit (`Balance < 0`):
   `Delivered = min(-Balance, MaxDischarge, S / Delta)`,
   `S' = S - Delivered * Delta`, `Absorbed = 0`.
4. Surplus (`Balance > 0`):
   `Absorbed = min(Balance, MaxCharge, (Capacity - S) / (Delta * ChargeEfficiency))`,
   `S' = S + Absorbed * Delta * ChargeEfficiency`, `Delivered = 0`.
5. Return `{{clamp(S', 0, Capacity)}, Absorbed, Delivered}`.

The buffer never delivers energy it does not hold.

## Transformer link (`TransformerLink.h`)

Energy accounting for one transformer. The transformer holds a small energy
store, the escrow. The secondary island may draw only energy that the escrow
already holds, so the link never creates energy, whatever order the engine
settles the two islands in. The primary island refills the escrow.

```cpp
struct LinkParameters {
    Megawatts Rating;
    double Efficiency = 1.0;
    Megajoules EscrowCapacity;
    Megawatts MaxRecharge;
};
struct LinkState {
    Megajoules Escrow;
    Megawatts LastDelivered;
};
struct LinkPlan {
    Megawatts SecondaryOffer;
    Megawatts PrimaryRequest;
};
struct LinkSettlement {
    LinkState State;
    Megajoules Loss;
    Megajoules Overflow;
    Megajoules OverDelivery;
    Megajoules OverConsumption;
};

LinkPlan PlanLink(const LinkParameters& Parameters, const LinkState& State, Seconds Delta,
                  bool PrimaryAvailable);
LinkSettlement SettleLink(const LinkParameters& Parameters, const LinkState& State,
                          const LinkPlan& Plan, Seconds Delta, Megawatts PrimaryConsumed,
                          Megawatts SecondaryDelivered);
```

Preconditions: `Rating > 0`, `0 < Efficiency <= 1`, `EscrowCapacity > 0`,
`MaxRecharge >= 0`, `0 <= State.Escrow <= EscrowCapacity`,
`State.LastDelivered >= 0`.

`PlanLink`:

1. If `Delta <= 0`, return `{0, 0}`.
2. `E = clamp(State.Escrow, 0, EscrowCapacity)`.
3. `Reserved = min(E, Rating * Delta)`; `SecondaryOffer = Reserved / Delta`.
4. If `!PrimaryAvailable`, `PrimaryRequest = 0`.
5. Else:
   `ExpectedDraw = min(State.LastDelivered * Delta, Reserved)`,
   `Room = EscrowCapacity - (E - ExpectedDraw)`,
   `PrimaryRequest = min(Room / (Efficiency * Delta), State.LastDelivered / Efficiency + MaxRecharge)`.

`SettleLink` takes what the engine reports after its solve. Start with a plan
from `PlanLink` for the same parameters, state, and delta. An engine adapter may
reduce either power to a nonnegative value to meet its representable range or
open the connection; it must never increase either value. Settle that plan
exactly once before planning the next interval.

1. If `Delta <= 0`, return `{State, 0, 0, 0, 0}`.
2. `E = clamp(State.Escrow, 0, EscrowCapacity)`.
3. `Delivered = clamp(SecondaryDelivered, 0, Plan.SecondaryOffer)`;
   `OverDelivery = max(SecondaryDelivered - Plan.SecondaryOffer, 0) * Delta`.
4. `Consumed = clamp(PrimaryConsumed, 0, Plan.PrimaryRequest)`;
   `OverConsumption = max(PrimaryConsumed - Plan.PrimaryRequest, 0) * Delta`.
5. `Credit = Consumed * Delta * Efficiency`;
   `Loss = Consumed * Delta * (1 - Efficiency)`.
6. `E' = E - Delivered * Delta + Credit`.
7. `Overflow = max(E' - EscrowCapacity, 0)`; then `E' = clamp(E', 0, EscrowCapacity)`.
8. Return `{{E', Delivered}, Loss, Overflow, OverDelivery, OverConsumption}`.

`OverDelivery` and `OverConsumption` report engine behavior that breaks the
plan. They are diagnostics: the escrow never pays for over-delivery and never
credits over-consumption.

Invariants for any inputs that meet the preconditions:

- `E' >= 0`.
- `E' - E == Credit - Delivered * Delta - Overflow` (within `1e-6` MJ).
- `Delivered * Delta <= E` (within `1e-6` MJ).

A link that starts empty offers nothing on its first step and requests
`min(EscrowCapacity / (Efficiency * Delta), MaxRecharge)` from the primary
side; it supplies the secondary side only after the primary side has paid in.

## Island loss (`Loss.h`)

```cpp
struct TierParameters {
    Megawatts Capacity;
    Meters ReferenceDistance;
    double ReferenceLossFraction;
};

Megawatts IslandLoss(const TierParameters& Tier, Megawatts Load, Meters Distance);
```

Loss is quadratic in load and linear in distance. At full capacity over the
reference distance, the island loses `ReferenceLossFraction` of its load.

Preconditions: `Capacity > 0`, `ReferenceDistance > 0`,
`ReferenceLossFraction >= 0`.

- If `Load <= 0` or `Distance <= 0`, return 0.
- Else return
  `ReferenceLossFraction * (Load / Capacity) * (Distance / ReferenceDistance) * Load`.

The result is not clamped; a loss above the load means the layout cannot work.

## Distance proxies (`IslandGraph.h`)

The loss formula needs one distance per island. These functions compute the
candidate proxies on a wire graph so the balance harness can compare them.
They run when an island is rebuilt, not every tick.

```cpp
struct Position { double X = 0.0; double Y = 0.0; double Z = 0.0; };
struct IslandNode {
    Position Location;
    Megawatts Load;
    bool IsFeed = false;
};
struct IslandEdge {
    std::size_t From = 0;
    std::size_t To = 0;
    Meters Length;
};
struct IslandGraph {
    std::vector<IslandNode> Nodes;
    std::vector<IslandEdge> Edges;
};

Meters TotalWireLength(const IslandGraph& Graph);
Meters SpatialExtent(const IslandGraph& Graph);
std::optional<Meters> LoadWeightedFeedDistance(const IslandGraph& Graph);
```

Positions are in meters. Edges are undirected. An edge whose `From` or `To` is
not a valid node index is ignored by every function. A negative edge length
counts as 0.

- `TotalWireLength`: sum of the lengths of the valid edges. 0 for no edges.
- `SpatialExtent`: largest straight-line distance between any two nodes.
  0 for fewer than two nodes.
- `LoadWeightedFeedDistance`: shortest wire-path distance from each node to its
  nearest feed node, using edge lengths. Returns
  `sum(Load_i * Distance_i) / sum(Load_i)` over nodes with `Load_i > 0`.
  Nodes with `Load_i <= 0` do not contribute. Returns `std::nullopt` if there
  is no feed node, if no node has a positive load, or if a node with a
  positive load cannot reach any feed node. A loaded feed node contributes
  distance 0.

## Transformer topology (`TransformerTopology.h`)

Transformers are directional: power flows from the primary island to the
secondary island. The directed graph of islands and transformers must stay
acyclic, so no loop of transformers can feed itself.

```cpp
struct DirectedLink {
    std::size_t FromIsland = 0;
    std::size_t ToIsland = 0;
};

bool HasDirectedCycle(std::size_t IslandCount, std::span<const DirectedLink> Links);
bool WouldCreateCycle(std::size_t IslandCount, std::span<const DirectedLink> Links,
                      DirectedLink Candidate);
```

- A link with an index at or above `IslandCount` is ignored.
- A link from an island to itself is a cycle.
- Parallel links between the same two islands in the same direction are not a
  cycle.
- `WouldCreateCycle` returns `HasDirectedCycle` of `Links` plus `Candidate`.
  An ignored candidate returns the result for `Links` alone.
