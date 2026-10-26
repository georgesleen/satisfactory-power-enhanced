# Building interaction UI

## Purpose

The menu answers three questions:

1. Is the grid OK?
2. If not, what failed and where?
3. What can I do?

Use vanilla building interaction patterns. The menu must feel like an unfamiliar base-game building, not a separate mod interface. The header shows the building name. Do not add an EnhancedPower or EP corporate identity.

Approved order:

- A first: finish the transformer, capacitor bank and cryo station menus in the approved vanilla style. Keep technical details collapsed.
- B after A: add a minimal tier, loading and feeding-transformer section to the vanilla power pole menu. Do not replace its graph or connection controls.

The transformer style pilot is approved. Use it as the shared component language. Do not add a grid dashboard or put technical detail in the main view.

## Layout at 1920 x 1080

`assets/ui/index.html`, `menu.css` and `menu.js` are the browser reference. They use the approved transformer pilot style. The browser runtime uses the engine-free core through WASM. It is not connected to a running game. The browser shows four views: transformer, capacitor bank, cryo station and the power pole mock. One `Browser prototype` label sits below the window; implementation notes stay in the collapsed details.

The primary reference is the vanilla [Power Switch](https://satisfactory.wiki.gg/wiki/File:Power_Switch_On.png). Put operation controls at left and circuit graphs at right. Use the [Power Pole graph](https://satisfactory.wiki.gg/wiki/File:Power_graph.jpg) legend and graph language. Use rectangular selection and action plates, not pill navigation or browser-native controls.

Dimensions below are logical pixels at 100% scale. The existing transformer shell defines the base sizes. New menu components use these target sizes. Native DPI scaling can scale the whole window. Localized text can increase height.

| Component | Size or rule |
| --- | --- |
| Building window | 1080 wide; centered; height fits contents within 960 |
| Title bar | 1080 x 42; building icon 22 x 22; title 18 px |
| Close plate | 94 x 42; right aligned |
| Body | 7 px side padding; 8 px top padding; 7 px column seam |
| Operation column | 290 wide; 12 px inner padding; 10 px module gaps |
| Circuit column | 769 wide; two stacked modules with 7 px seam |
| Status module | 262 wide; at least 90 high; lamp 22 x 55; text and icon |
| Transfer or storage module | 262 wide; content height; main number 23 px; unit 15 px |
| Heat or cooling module | 262 wide; at least 56 high; icon 24 x 28 |
| Breaker module | 262 wide; at least 130 high; control track 160 x 86 |
| Circuit module | 769 wide; plot 212 high; 52 px left label space |
| Graph | White plate; 6 px dark frame; 3 px traces |
| Legend | Two columns, two rows; 16 px text; 12 px square keys |
| Condition strip | 1066 wide; at least 40 high; 14 px text; 20 px icon |
| Details disclosure | 1080 wide; at least 36 high; 14 px text; full-width action |
| Detail fields | Two columns; 16 px side margin; wrap values |
| Pole addition | One full-width section inside the existing pole window; at least 36 px per row |
| Body text | 14 to 16 px; no small print for failures or actions |

Use the same shell for all three building menus. Keep the circuit column and operation column aligned. Do not compress text to keep a fixed height. Scroll the content area when it exceeds the viewport. Keep the title and close action visible.

Graph plates are white. Consumption is orange. Production is dark gray. Capacity is light gray. Maximum Consumption is blue. The legend has two columns: Consumption above Capacity at left, Production above Maximum Consumption at right. Do not add permanent numbered axes or a dense scientific grid to the default view. Keep values readable when traces overlap. Never draw an uncapped value as a numeric capacity trace.

## Widget tree

Names below are semantic roles, not proprietary asset names.

```text
Building interaction window
  Title bar
    Building icon, building name, close action
  Scrollable body
    Operation column
      Status lamp, status icon, status text
      Main instrument
      Secondary instrument
      Building action, if supported
    Circuit column
      Input circuit module
        Side label, tier tag, power graph, four-value legend
      Output or connected circuit module
        Side label, tier tag, power graph, four-value legend
    Condition strip
      Condition icon, consequence, one useful action
    Collapsed building details
      Named grid references, measurements, tuning provenance
  Native focus handling
```

| Menu | Main instrument | Secondary instrument | Circuit modules | Details |
| --- | --- | --- | --- | --- |
| Transformer | Transfer MW, transformer rating MW, load meter | Heat status | Input and output grids | Direction, grid names, heat, trip estimate, loss and tuning |
| Capacitor bank | Stored energy MWh, energy capacity MWh | Charging, discharging, full, empty or idle; charge and discharge MW | Connected grid; storage history can use the second module | Stored MJ, power limits and efficiency when supplied by the adapter |
| Cryo station | Cooling status text | SC line state and supply status, only when known | Connected grid; cooled SC line information | Cooling model note; verified supply or connection information |
| Vanilla pole | Existing vanilla graph and connection controls | Added tier, load/capacity, feeding transformers | Preserve vanilla circuit graph | Existing vanilla details; no second dashboard |

Do not present a capacitor as a reactive-power correction device. Do not present a cryo station as a transformer. Browser menu selection, scenarios, pause and reset are study controls outside the building window, not proposed game controls.

## Native integration evidence

The provisioned game headers expose these supported integration seams:

- `AFGBuildable::GetInteractWidgetClass()` and `mInteractWidgetSoftClass` select a `UFGInteractWidget` class for a building.
- `AFGBuildable::mInteractionRegisterPlayerWithCircuit` registers an interacting player for circuit detail replication, including the power graph.
- `AFGBuildablePowerPole::GetPowerCircuit()` reads the pole circuit. `mConnectionWidgetClass` uses `UFGPoleConnectionsWidget`.
- `UFGFocusableWidget` and the game's widget-pool functions provide focus and widget lifecycle seams.

Evidence: `Source/FactoryGame/Public/Buildables/FGBuildable.h`, `FGBuildablePowerPole.h`, and `FGBlueprintFunctionLibrary.h` in the provisioned SML starter checkout. These are class/API names, not verified Blueprint asset paths.

Reuse the installed game's building window, power graph, operation status, focus styles, buttons and font assets where the editor exposes supported classes. Exact widget Blueprint, style and font asset paths are not established by the available headers. Do not invent asset identifiers or copy proprietary assets into this repository. Editor inspection is required before binding the native widget tree.

The browser substitute is Roboto, SIL Open Font License 1.1. Its license is in `assets/ui/fonts/OFL.txt`. The browser icons and instrument geometry are original SVG/CSS. Reference screenshots stay in untracked `notes/ui/references/`.

## Power semantics

A transformer interface has a rating. A cooled superconducting line has no capacity cap and no transmission loss. Show `Uncapped` for capacity and `N/A` for loading, without a percent sign. Do not show a fictitious maximum or a percent-loading meter for the line. Keep the transformer rating and transformer load meter at each end. Cooling does not scale capacity.

`tools/balance/tuning.json` is the numeric source. Its SC `capacityMegawatts` is `null`. Do not turn this into zero or infinity in JSON. Warm-state loss, capacity, cooling consumption, thermal thresholds and trip behavior are unresolved. Show `Cooling model not specified` for unresolved values. A cryo presentation state must not change core power or energy values.

Transformer escrow and capacitor storage are different energy stores. Do not label escrow as capacitor charge. Do not call a thermal heat value a temperature. Heat is dimensionless, not degrees Celsius.

### States and transitions

Use a lamp, icon and text together. Keep the condition strip visible. A zero reading is not proof of an empty grid or a trip. Use explicit scenario and state fields.

| Transformer state | Entry and display | Exit or action |
| --- | --- | --- |
| Operational | Connected, upstream available, no thermal warning or trip; show actual transfer | Disconnect opens this transformer only |
| At capacity | Requested demand plus loss exceeds the link offer; transfer stays at the rating; show `At capacity`, `Connection at capacity` and the unserved MW | Reduce sustained load or add a transformer; short peaks can use a capacitor; this is not a trip |
| Heat warning | Core `thermalStatus` is `warning`; show `Heat warning` | Core cooling can return it to normal or progress to trip |
| Local trip | Core `thermalStatus` is `tripped`; name the affected output grid | Native reset uses `TryResetThermal`; reject reset while heat is at or above warning threshold |
| Upstream outage | Upstream is unavailable; show remaining supplied power as escrow drains | Upstream recovery can restore transfer; do not call this a local trip |
| Disconnected | User opened connection; show `Disconnected`, not `At capacity` | Connect requests reconnection; it must not silently clear a thermal trip |
| Empty grid | Explicit empty-grid fixture or native grid has no supply and no demand | Show zero values, status `No load` and `No connected load`; preserve the tier label |

A trip overrides normal and warning status. Heat warning text takes precedence over at-capacity text. A disconnect and an upstream outage remain distinct causes in the condition text. Heat can remain after disconnection. Do not clear heat to make the disconnected screen look normal. For trip estimates, say `At this load` since the estimate assumes constant load.

| Capacitor state | Entry | Transition |
| --- | --- | --- |
| Charging | `bufferAbsorbedMW > 0` | Headroom fills storage within core limits |
| Discharging | `bufferDeliveredMW > 0` | A deficit consumes stored energy within core limits |
| Full | Stored energy equals capacity; no charge or discharge; status `Full` | A deficit can start discharge |
| Empty | No stored energy; no charge or discharge | Available headroom can start charge |
| Idle | Neither power flow, storage between empty and full; status `Idle` | A surplus or deficit changes the state |
| Disconnected | `bufferConnected` is false; stored energy is retained | Connect allows core charging and discharge again |

Show energy and actual charge/discharge power together. Empty storage cannot deliver power. Full storage cannot absorb more energy. A capacitor does not solve a sustained deficit. Its connection action controls the bank only, not the transformer. When disconnected, exclude its discharge from available supply and retain its stored energy.

| Cryo presentation state | Display | Transition |
| --- | --- | --- |
| Cooled SC | `Superconducting`, `Uncapped`, `0 MW line loss` | Loss of a verified cooling supply changes the presentation state |
| Cooling unavailable | `Cooling unavailable`; warm electrical model not specified | Restored supply returns to cooled only when confirmed |
| Unknown | `Cooling model not specified` | A supported native cooling adapter can provide real state |

Browser concept states are `cooled` and `coolinglost`. They select the corresponding presentation above, not a numeric cooling model.

The browser can demonstrate these labels as presentation states. Do not simulate coolant use, a warm capacity, a warm loss or a warm trip. Do not show an invented countdown.

For the pole, preserve vanilla connection and fuse states. The native grid-tier plate is read-only: tier is network data, not a pole setting. Add the island tier and its measured load against finite tier capacity. For cooled SC, show uncapped capacity without a percentage. List the actual feeding transformers when supplied by the native adapter. Use `No feeding transformer` for a known empty list and `Not available` when the list is absent. The WASM fixture models one link, not a general network. Never infer a feeder list from its rating or graph.

The browser's `Capacity preview` control is outside the building window with the study controls. It changes tier-capacity metadata only. The read-only plate says `Tier capacity preview` and `Preview loading`; finite loading compares the LV fixture consumption with the selected capacity. SC reads `Uncapped` and `N/A`, with no loading meter. The graph stays labeled `LV fixture` / `LV`, and the feeder stays labeled as the simulated MV to LV fixture. The visible condition strip states that the graph and feeder remain the fixed LV simulation. Selecting SC does not simulate SC cooling or replace the LV loss model.

## Runtime data contract

`make ui` generates `tuning.h` from `tools/balance/tuning.json` on every build. `make ui TUNING=<path>` uses another tuning file for the same build. The generator rewrites the header only when its content changes.

The generated `core.js` exports the module factory `EnhancedPowerCore`. Wait for module initialization before enabling study controls. Bind functions through Emscripten `cwrap`:

| C export | Binding | Meaning |
| --- | --- | --- |
| `ui_reset(int scenario)` | Return `null`, arguments `['number']` | Reset the fixture and tick count to the selected scenario |
| `ui_step(double deltaSeconds)` | Return `null`, arguments `['number']` | Advance C++ state by elapsed simulation seconds |
| `ui_snapshot()` | Return `'string'`, no arguments | Read JSON text; parse or copy it before another core call |
| `ui_set_connected(bool connected)` | Return `null`, arguments `['number']` | Pass 0 or 1 to request the transformer connection state |
| `ui_reset_breaker()` | Return `'number'`, no arguments | Attempt `TryResetThermal`; 1 accepted, 0 still too hot |
| `ui_set_buffer_connected(bool connected)` | Return `null`, arguments `['number']` | Pass 0 or 1 to connect or disconnect the capacitor bank |

Scenario IDs: 0 normal, 1 thermal diagnostic overload, 2 pulsed spikes, 3 upstream outage, 4 empty grid, 5 sustained overload. These are explicit fixtures, not real game telemetry. Scenario 5 requests the same overload demand as scenario 1 but heats from actual transfer only. It must not show a diagnostic trip countdown. Study reset reloads a scenario. Breaker reset retains the scenario and uses core reset rules.

The link offer is capped at its tuning rating. Scenario 1 is a labeled thermal diagnostic: C++ imposes a tuning-derived thermal load ratio to demonstrate warning and a latched trip without inventing transport above that cap. The study picker names it `Thermal test (imposed load)`, and the prototype label below the window shows the imposed percentage with `Not end-to-end link overload`. Do not imply that its imposed thermal load is actual transferred power. Other scenarios use actual transfer divided by rating for heat.

All power and energy calculations run in C++. Use the actual core primitives `PlanLink`, `SettleLink`, `StepThermal`, `ClassifyThermal`, `TimeToTrip`, `StepBuffer` and `IslandLoss` as applicable. JavaScript schedules steps, stores history and renders snapshots. It does not repeat the heat, loss, storage or energy-accounting rules.

| Snapshot field | Unit and meaning |
| --- | --- |
| `tick` | Integer simulation step count, not elapsed seconds |
| `scenario` | Integer fixture ID above |
| `seconds` | Elapsed simulation seconds |
| `production`, `consumption`, `capacity`, `maxConsumption` | MW; overview of the fixture circuit; do not treat circuit capacity as wire-tier capacity |
| `transfer` | MW actually delivered across the transformer |
| `rating` | MW transformer rating from tuning |
| `loadPercent` | `100 * transfer / rating`; actual delivered loading, capped by the link offer |
| `requestedLoadMW`, `requestedLoadPercent` | Requested demand in MW and percent of transformer rating; may exceed rating |
| `unservedMW`, `saturated` | MW unmet demand and boolean constrained-supply indication |
| `diagnostic`, `imposedThermalRatio` | Thermal diagnostic flag and imposed dimensionless load ratio; not actual flow |
| `thermalLoadRatio` | Actual dimensionless driver passed to thermal stepping; imposed only in scenario 1 |
| `heat` | Dimensionless thermal state from `StepThermal` |
| `heatPercent` | `100 * heat / tripHeat` from the adapter; not temperature or transformer load |
| `thermalStatus` | `normal`, `warning` or `tripped` from core classification |
| `timeToTrip` | Seconds at constant current load, or `null` when no finite trip is predicted |
| `upstreamAvailable` | Boolean upstream supply state |
| `connected` | Effective transformer connection; false on a thermal trip even if user intent remains connected |
| `connectionRequested` | Boolean user intent for the transformer connection |
| `bufferConnected` | Boolean capacitor connection; defaults true on scenario reset |
| `bufferStoredMJ`, `bufferCapacityMJ` | MJ capacitor energy, not transformer escrow |
| `bufferAbsorbedMW`, `bufferDeliveredMW` | MW actual capacitor charge input and discharge output |
| `escrowStoredMJ`, `escrowCapacityMJ` | MJ transformer escrow, not capacitor storage |
| `overflowMJ` | Cumulative MJ escrow overflow from `SettleLink` |
| `energyResidualMJ` | Cumulative MJ energy-accounting residual after served demand, losses, storage changes and overflow; show in details, not as delivered energy |
| `lossMW` | MW loss reported by the adapter; details must identify its modeled scope |
| `input`, `output` | Separate circuit objects with `production`, `consumption`, `capacity`, `maxConsumption`, all MW |
| `tuning` | Source data and provenance, described below |

Use `input` and `output` for the two transformer graphs. Output and top-level production equal link delivery plus capacitor delivery. Output consumption is served consumer demand. Output capacity is link offer plus available capacitor discharge. Output Maximum Consumption is requested consumer demand, not a recorded history peak. Capacitor charging and losses are separate. Input production and consumption equal actual primary power consumed by the link. Input capacity is available upstream power. Input Maximum Consumption is the planned primary request. Do not use these circuit capacities as wire-tier capacities, or `maxConsumption` as a transformer rating.

Available output capacity includes capacitor discharge available at the beginning of the step. The difference between output production and consumer consumption pays capacitor charging and island loss. It is not free surplus. Input capacity is the source ceiling derived from rating plus maximum recharge. The fixture uses unity link efficiency because tuning has no transformer efficiency parameter; do not label this as a tuned game efficiency.

The fixture starts with funded escrow and full capacitor storage except in the empty-grid scenario. Escrow capacity derives from rating times the tuning step. Outage timing and pulse intervals derive from the thermal time constant. The adapter reports its assumptions in provenance. These fixture choices are not native building rules.

`tuning` contains `source`, `status`, `sha256`, `stepSeconds`, `maxChargeMW`, `maxDischargeMW`, `warningHeat`, `tripHeat`, `timeConstantSeconds` and `tierCapacitiesMW`. `source` is the tuning path given to the build, and `sha256` is the hash of that file. The SC entry in `tierCapacitiesMW` is `null`. It also includes the build-time source sections `tiers`, `transformers`, `capacitorBank`, `acceptance` and `simulation`. Use these fields for details and finite tier-capacity labels. Do not derive a new electrical rule from an acceptance gate.

Read rating, capacity, thresholds and storage parameters from tuning or its generated adapter data. Do not duplicate them as JavaScript constants. Use explicit `null` for an uncapped tier and unavailable finite estimates. An unavailable reading is `Not available`, never a fabricated zero. The shared snapshot does not supply grid names, feeder lists, coolant inventories or native circuit IDs. Those need native data, not invented fixture measurements.

The core uses MW, MJ and seconds. The main capacitor display uses MWh, with `MWh = MJ / 3600` as presentation conversion. Show power in MW. Keep raw MJ, dimensionless heat, heat percentage, numeric tuning and trip estimates in collapsed details. The main transformer view shows a heat status, not technical thermal numbers.

### Update rates and history

- Step the fixture at 20 Hz with a 0.05-second simulation delta.
- Cap accumulated wall time at 0.25 seconds per browser frame. Pause excess background time instead of running an unbounded catch-up.
- Sample and render readings and graph history at 4 Hz. Keep a 60-second rolling history.
- Keep mounted instrument, action and status nodes between samples. Update changed text, attributes and graph paths in place. Rebuild the layout only when the building changes; do not restore focus on every refresh.
- Draw from existing samples between updates. Do not invent intermediate measured values.
- Pause freezes simulation and graph history. Resume continues from the same state.
- Reset clears history. Start new traces from actual snapshots. Do not fill earlier time with sample data.
- Connection actions refresh the displayed snapshot promptly. History records the resulting change at the next sample.
- Native integration follows replicated circuit data. These browser rates are not a claim about engine replication frequency.

If WASM fails to load, show `Simulation unavailable` with the load error and disable simulation actions. Do not fall back to fixed readings labeled as live.

## Focus and input

Use `UFGFocusableWidget` and native input routing in UMG. Do not capture movement or gameplay actions after closing the menu. Use the game's current input bindings, not hard-coded game keys.

Browser controls support Tab, Shift+Tab, Enter, Space and Escape. Up and Down cycle the close action, available building actions and details disclosure. Skip hidden and disabled controls. Keep a visible focus outline. Pointer hover must not move keyboard focus.

On open, focus the close action. In game, keep focus inside the open menu. In the browser, Up and Down stay inside the menu, and Tab and Shift+Tab follow document order, which also reaches the study controls. Escape closes an open study picker first, then the menu, and returns focus to the opener. The browser opener is the reopen control. In game, return control to the interacting player. Close and reopen must not reset the core.

Enter or Space activates a focused action. Details expands in place and retains focus. A rejected breaker reset explains why in the condition strip. Do not remove focus when status text updates. Use a polite status announcement for state changes, not every numeric refresh. Graphs have text summaries and legends. Decorative screws, vents and lamps are not focus targets.

Reduced-motion mode has no transition or flashing effects. No failure indication requires flashing, color recognition or audio. Keep actions available without dragging the breaker handle.

## Text and localization

Use text widgets for every label, unit and status. Do not bake text into images. Native labels use localized text resources; browser labels use the same semantic message keys when localization is added.

- Use short sentences: condition, consequence, action.
- Keep `Input`, `Output`, `Consumption`, `Production`, `Capacity` and `Maximum Consumption` consistent.
- Use complete message templates, not concatenated sentence fragments.
- Format numbers at the presentation boundary with the user's locale. Keep unit symbols distinct from values.
- Allow at least 40% label expansion. Wrap condition text and details. Do not shrink type.
- Preserve MW, MJ, MWh and LV/MV/HV/SC as technical symbols. Localize their explanations.
- Support right-to-left text without reversing physical input-to-output semantics. Use logical layout order and an explicit direction label.
- Keep precise values in text even when a meter reaches its visual limit. Never silently clamp the displayed overload percentage to 100.

## Asset inventory and editor boundary

| Asset or resource | Use | Source and status |
| --- | --- | --- |
| Building window, title bar, close plate | Shared shell | Reuse supported installed-game resources; exact Blueprint paths editor-unverified |
| Power graph and legend | Circuit modules and pole | Reuse vanilla graph where supported; exact widget Blueprint path editor-unverified |
| Operation lamp and status style | Main state | Reuse vanilla resources where supported; exact style paths editor-unverified |
| Focus and button styles | Every native action | Reuse native focus handling; exact style paths editor-unverified |
| Native font | All UMG text | Reuse game font; exact font asset path editor-unverified |
| Building icons | Transformer, capacitor, cryo and pole header | Original mod icons or verified supported vanilla references |
| State icons | Normal, warning, trip, disconnected, outage, storage and cooling | Original vector silhouettes; each has a text equivalent |
| Instrument geometry | Browser plates, vents, screws, breaker and arrows | Original SVG/CSS; not copied proprietary UI textures |
| Browser font | Reference rendering | Roboto with `assets/ui/fonts/OFL.txt` |

The API symbols in Native integration evidence are reusable seams, not verified asset paths. Inspect the editor before binding any proprietary widget, texture, material, style or font asset. Do not invent package identifiers or commit extracted proprietary assets. Keep reference screenshots in untracked `notes/ui/references/`.
