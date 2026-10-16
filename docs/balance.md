# Initial balance

These values are **initial tuning**, not final game balance. `ep-balance` is a
host CLI. It does not run Satisfactory. The scenarios are explicit building
mixes and layouts, not measured saves or complete recipe plans.

## Method

The root CMake project adds `tools/balance`. The CLI links
`enhanced_power_core` and `nlohmann_json::nlohmann_json`. The light shell resolves
the required JSON package without licensed engine files.

```sh
nix develop path:. --command cmake -S . -B build/balance-host -G Ninja
nix develop path:. --command cmake --build build/balance-host --target ep-balance -j4
nix develop path:. --command ./build/balance-host/tools/balance/ep-balance --tuning tools/balance/tuning.json tools/balance/scenarios
nix develop path:. --command ctest --test-dir build/balance-host -R 'enhanced_power_balance|enhanced_power_building_extraction' --output-on-failure
```

The balance and extraction tests pass: `100% tests passed out of 3`.
The extraction tests check stable wiki records and scenario references. The
report test checks factory comfort, branch layouts, remote supply, collection
plants, warning before trip, finite storage, and energy accounting. Python tests
run with `-B`, so they do not create a cache in the source tree.

Each scenario records machine classes, counts, clocks, recipes for variable
consumers, positions, and wiring. Fixed consumers run at full duty. No scenario
uses Somersloops. Clock scaling and production amplification describe vanilla
loads; they are not substitutes for core simulation rules. Variable loads use
a linear ramp between the recipe limits. The peak column synchronizes them.
The pulse study also compares evenly spaced start phases.

The CLI calls the core's `IslandLoss`, `TotalWireLength`, `SpatialExtent`,
`LoadWeightedFeedDistance`, `StepThermal`, and `StepBuffer`. Python extracts
facts and checks report gates. It does not implement these rules. The reported
energy residual is an accounting check, not a second buffer solver.

Loss tables use mean demand. Peak demand sizes local wiring. Loss is reported
relative to consumer demand; the report does not solve a new supply-dependent
loss equilibrium. Split cases add local LV loss to the trunk load. They exclude
transformer conversion loss. Collection cases exclude downstream factory loss.
Only unlocked tiers appear in loss comparisons.

## Building facts and source checks

The dedicated server has no usable Docs JSON. `buildings.json` comes from the
**official wiki**, not from the server or SatisfactoryTools. The extractor reads
the stable records of these two wiki tables:

- [DocsBuildings.json, revision 62020](https://satisfactory.wiki.gg/wiki/Template:DocsBuildings.json?oldid=62020),
  updated 2026-06-02.
- [DocsRecipes.json, revision 62858](https://satisfactory.wiki.gg/wiki/Template:DocsRecipes.json?oldid=62858),
  updated 2026-09-01.

`Module:DocsUtils` loads these tables for wiki building and recipe displays.
The extractor maps descriptor keys `Desc_...` to scenario building keys
`Build_...`. It excludes non-stable records and buildings without power facts.
The clock exponent follows [Clock speed](https://satisfactory.wiki.gg/wiki/Clock_speed):
200% clock uses 250% base power. Amplification follows
[Production amplification](https://satisfactory.wiki.gg/wiki/Production_amplification).
Generation scales with clock, not with the consumer exponent.

To reproduce the table, download the two source records once, then run:

```sh
curl --fail --location 'https://satisfactory.wiki.gg/wiki/Template:DocsBuildings.json?oldid=62020&action=raw' -o /tmp/ep-wiki-buildings.json
sleep 3
curl --fail --location 'https://satisfactory.wiki.gg/wiki/Template:DocsRecipes.json?oldid=62858&action=raw' -o /tmp/ep-wiki-recipes.json
python3 -B tools/balance/extract_buildings.py /tmp/ep-wiki-buildings.json /tmp/ep-wiki-recipes.json --source 'Official Satisfactory Wiki: DocsBuildings.json oldid=62020; DocsRecipes.json oldid=62858; https://satisfactory.wiki.gg/wiki/Clock_speed; https://satisfactory.wiki.gg/wiki/Production_amplification' --output tools/balance/buildings.json
```

Fetch sparingly. The wiki can rate-limit requests. The following spot checks
match both the downloaded facts and separate wiki page text. The five pages
were retrieved in one API request.

| Fact | Checked value | Wiki page evidence |
| --- | ---: | --- |
| Constructor base consumption | 4 MW | [Constructor](https://satisfactory.wiki.gg/wiki/Constructor), `OverclockingInfo` power parameter |
| Manufacturer base consumption | 55 MW | [Manufacturer](https://satisfactory.wiki.gg/wiki/Manufacturer), `OverclockingInfo` power parameter |
| Blender base consumption | 75 MW | [Blender](https://satisfactory.wiki.gg/wiki/Blender), `OverclockingInfo` power parameter |
| Nuclear Power Plant output | 2500 MW | [Nuclear Power Plant](https://satisfactory.wiki.gg/wiki/Nuclear_Power_Plant), output at 100% clock |
| Nuclear Pasta accelerator consumption | 500 to 1500 MW | [Particle Accelerator](https://satisfactory.wiki.gg/wiki/Particle_Accelerator), recipe power table |

The recipe source also gives a 120-second Nuclear Pasta cycle. The
[Power Storage](https://satisfactory.wiki.gg/wiki/Power_Storage) page and building
data specify 100 MWh, 100 MW maximum charge, and unlimited discharge. Its page
specifies a 6 m by 6 m footprint. Its build recipe in DocsRecipes uses 5 Encased
Industrial Beams, 10 Modular Frames, and 100 Wire.

## Initial tuning table

`tuning.json` is the input for these results. Reference loss means the fraction
lost at full tier capacity over the reference distance. It is not a flat tax on
every factory.

| Tier | Unlock tier | Capacity MW | Reference distance m | Reference loss fraction |
| --- | ---: | ---: | ---: | ---: |
| LV | 0 | 12000 | 1000 | 0.12 |
| MV | 3 | 48000 | 1000 | 0.08 |
| HV | 6 | 192000 | 1000 | 0.02 |
| SC | 9 | 768000 | 1000 | 0 |

| Parameter | Initial value |
| --- | --- |
| Local transformer | 2000 MW |
| District transformer | 7000 MW |
| Backbone transformer | 24000 MW |
| Thermal time constant | 15 seconds |
| Warning heat | 1 |
| Trip heat | 1.44 |
| One capacitor bank | 60000 MJ, 2000 MW charge, 2000 MW discharge |
| Capacitor charge efficiency | 0.95 |
| Buffer feed setpoint | 0.95 of transformer rating |
| Comfort gate | Peak consumer demand at most 0.8 of LV capacity |
| Local loss gate | Mean LV loss at most 0.03 of demand |
| Pulse simulation | 1800 seconds, 0.1-second steps, initially full storage |

LV has late-game headroom instead of a small early-game cap. An ordinary quantum
module peaks at 50.310% of LV capacity. Even the extreme district peaks at
79.083%. MV earns its early role through regional loss reduction. HV earns its
role through long-distance shared transport, not through cramped local wiring.
SC's capacity and zero-loss benefit need a larger-grid and cooling-cost playtest.

The transformer sizes are choices, not one mandatory sequence. A local unit
fits the early component examples. A district unit serves the aluminum campus
or quantum module. A large plant can use a backbone unit or parallel feeds.
The thermal delay provides readable overload feedback in the independent heat
study below; it is not proof of engine integration.

## Scenario results

The numeric cells below are copied from real CLI output with the wiki-derived
building table. Local loss uses `LoadWeightedFeedDistance`. The outpost row uses
its unchanged local factory; its remote feeder is compared in the next section.

| Scenario file | Mean MW | Peak MW | LV peak % | Local LV loss % | Comfortable |
| --- | ---: | ---: | ---: | ---: | --- |
| 02-iron | 267.091 | 267.091 | 2.226 | 0.046 | yes |
| 03-steel | 611.941 | 611.941 | 5.100 | 0.134 | yes |
| 04-motors | 953.479 | 953.479 | 7.946 | 0.248 | yes |
| 05-oil | 1744.866 | 1744.866 | 14.541 | 0.539 | yes |
| 06-computers | 2465.726 | 2465.726 | 20.548 | 0.976 | yes |
| 07-aluminum | 2583.647 | 2583.647 | 21.530 | 1.123 | yes |
| 08-pasta | 3550.610 | 4550.610 | 37.922 | 1.654 | yes |
| 09-quantum | 3987.223 | 6037.223 | 50.310 | 1.550 | yes |
| 10-outpost | 2583.647 | 2583.647 | 21.530 | 1.123 | yes |
| 11-pulsed-district | 6490.000 | 9490.000 | 79.083 | 2.528 | yes |

All factory rows pass the comfort and local loss gates. This includes the
ordinary overclocks listed in the scenario files. The extreme district does
not set a mandatory capacitor requirement for one accelerator.

| Collection scenario | Generation MW | Export mean MW | Export peak MW | LV peak % | MV peak % | LV loss % | MV loss % | HV loss % |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 12-central-plant | 30000.000 | 16611.480 | 22661.480 | 188.846 | 47.211 | 47.429 | 7.905 | 0.494 |
| 13-regional-plant | 3900.000 | 3472.377 | 3472.377 | 28.936 | 7.234 | 7.286 | 1.214 | locked |

The regional example collects coal generation for one steel and three motor
campuses. LV capacity is sufficient, but MV materially reduces loss. The central
plant exceeds LV capacity; MV can carry it, but HV has much lower shared trunk
loss. Generator rows must use separate local collection islands before step-up.
The aggregate graph is a comparison of export tiers, not permission to collect
the whole plant on one LV island.

## Distance proxy recommendation

Use **LoadWeightedFeedDistance**. It represents the wire path to a feed and does
not sum every local branch. These aluminum-campus results use the same demand
and machine positions. Small footprint differences come from pole nodes.

| Layout | Proxy | Distance m | LV loss % |
| --- | --- | ---: | ---: |
| Pole branch | TotalWireLength | 10319.392 | 26.662 |
| Daisy chain | TotalWireLength | 7485.365 | 19.340 |
| Pole branch | SpatialExtent | 661.211 | 1.708 |
| Daisy chain | SpatialExtent | 654.428 | 1.691 |
| Pole branch | LoadWeightedFeedDistance | 434.488 | 1.123 |
| Daisy chain | LoadWeightedFeedDistance | 423.917 | 1.095 |

Reject TotalWireLength as the loss distance. It charges compact factories for
branch count. SpatialExtent avoids that penalty but cannot see a route detour.
For the same factory with its source moved away, the wire route is longer than
the straight separation:

| Remote unsplit proxy | Distance m | LV loss % |
| --- | ---: | ---: |
| TotalWireLength | 13319.392 | 34.413 |
| SpatialExtent | 2261.027 | 5.842 |
| LoadWeightedFeedDistance | 3434.488 | 8.874 |

Keeping local wiring on LV and stepping up only the trunk gives:

```text
SPLIT tier=MV proxy=LoadWeightedFeedDistance localLossMW=29.003 trunkLossMW=34.130 totalLossPercent=2.444
SPLIT tier=HV proxy=LoadWeightedFeedDistance localLossMW=29.003 trunkLossMW=2.133 totalLossPercent=1.205
```

The local campus has 1.123% loss, not the remote unsplit 8.874%. The transmission
upgrade is useful without a transformer at each production block. Rebuild the
proxy when topology or representative load weights change; do not run a full
per-wire flow solve each tick. Multiple feed points and light distant branches
still need dedicated layout tests.

## Capacitors and vanilla storage

The extreme district contains six synchronized Nuclear Pasta accelerators and
support buildings. Its 6490 MW mean fits a 7000 MW district transformer, while
its 9490 MW peak does not. Both storage types use the same 95% feed setpoint.
Vanilla storage has unlimited discharge in the study: the finite bound supplied
to `StepBuffer` equals the entire factory peak, so it cannot limit any request.
Vanilla storage has no charge-efficiency penalty. Capacitors do.

The sizing search checks counts from zero upward. A count passes only if there
is no trip, no unserved energy, no feed above the transformer rating, and no
energy decline over the last pulse cycle. For this district the longest recipe
cycle is also its repeat period. This last check prevents a large initial charge
from hiding a long-term recharge deficit. Search results apply to this waveform
and step size, not to every factory.

| Alternative | Units | Maximum heat | Warning s | Trip s | Minimum stored MJ | Charged MJ | Delivered MJ |
| --- | ---: | ---: | --- | --- | ---: | ---: | ---: |
| Synchronized, no buffer | 0 | 1.441 | 84.500 | 112.600 | 0.000 | 0.000 | 0.000 |
| Synchronized, capacitor | 2 | 0.902 | none | none | 39344.000 | 1188614.737 | 1209840.000 |
| Staggered, no buffer | 0 | 0.890 | none | none | 0.000 | 0.000 | 0.000 |
| Extra feed headroom | 0 | 0.547 | none | none | 0.000 | 0.000 | 0.000 |
| Sustained peak, capacitor | 2 | 1.442 | 44.800 | 56.000 | 0.000 | 0.000 | 120000.000 |
| Vanilla Power Storage | 1 | 1.441 | 595.100 | 713.000 | 0.000 | 31100.000 | 391100.000 |
| Vanilla storage comparison | 30 | 0.902 | none | none | 10719344.000 | 1129184.000 | 1209840.000 |
| Minimum repeatable vanilla count | 18 | 0.902 | none | none | 6399344.000 | 1129184.000 | 1209840.000 |

The extra-headroom alternative uses 11862.500 MW. A catalog build can use parallel
district units or a backbone unit instead. Staggering is another valid solution.
Capacitors deplete under sustained peak demand and do not solve a permanent
supply deficit. Passing buffered runs report zero unserved energy and an energy
residual of zero at the report precision. They draw charging energy from the
feed; it is not free energy.

The heat-only study allows feed overload until a thermal trip. It does **not**
call the hard-rated escrow link or simulate engine shortage behavior. Therefore
the unbuffered trip times are thermal design evidence, not runtime supply
promises. The passing buffered sizing rows stay below the rating, but still need
an escrow-link and engine-ordering integration test. Pulse runs exclude wire
loss, so they size storage at the modeled load boundary, not a complete feeder.

### Size and initial material cost

The capacitor footprint uses the asset's nominal 4 m by 4 m placement area.
The initial proposed recipe reuses the storage's structural materials and adds
AI Limiters and Alclad Aluminum Sheets. This recipe is tuning data, not an
implemented build recipe. The CLI prints these exact totals for the minimum
repeatable solutions:

```text
BUILD type=initial-capacitor units=2 footprintM2=32.000 capacityMWh=33.333 AILimiter=20 AlcladAluminumSheet=40 EncasedIndustrialBeam=10 ModularFrame=20 Wire=200
BUILD type=vanilla-storage units=18 footprintM2=648.000 capacityMWh=1800.000 EncasedIndustrialBeam=90 ModularFrame=180 Wire=1800
```

Vanilla storage works. Its slow recharge, not its discharge rate, makes this
repeatable pulse layout large. The capacitor solution uses less placement area
and fewer structural materials, but requires later electronics and aluminum,
has charging loss, and stores far less outage energy. This is its proposed role.
Do not claim a universal cost advantage from mixed material counts. Recipe
throughput, unlocks, clearances, and construction costs need a playtest.

## Open questions and acceptance limits

- Replace illustrative building mixes with recipe-balanced plans or measured
  saves. Confirm full upstream processing, water, transport, and duty cycles.
- The scenarios cover vanilla facts only. Satisfactory Plus needs its actual
  recipes and building power table before its acceptance gates can be claimed.
- Validate the exact variable-power waveform, phase behavior after reload, and
  ordinary overclocks against the installed game version.
- Integrate wire loss and the hard-rated escrow link into the pulse study after
  the engine supply contract is proven. Decide how thermal overload relates to
  the link's hard offer limit. An independent heat test is not that proof.
- Island thermal trips are not simulated by this CLI. The shown local trip is
  the district transformer heat study; other islands are not modeled there.
- Railway HV uses the same tier constants as wire HV. Train traction and
  regeneration accounting still need a separate test; these results do not
  prove that regeneration is preserved or counted once.
- Test several feeds, partial loading, long light branches, and generator
  collection when choosing representative load weights for the distance proxy.
- The capacity headroom at early milestones is deliberate. Confirm that MV
  construction cost is worth regional loss savings without making LV unpleasant.
- Confirm SC capacity, cooling consumption, and construction cost against larger
  export grids. The shown plant does not establish its final capacity limit.
- The minimum storage search uses the longest recipe cycle as its tail window.
  Mixed incommensurate recipe periods need a suitable observation window rather
  than treating that window as a proven repeat period.
