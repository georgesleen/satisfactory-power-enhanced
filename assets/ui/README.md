# Power building menus

A browser prototype of transformer, capacitor-bank and cryo-station interaction menus, plus a minimal vanilla power-pole extension mock. **Not Unreal, SML, or a connection to a running game.** Transformer transport, heat, capacitor energy and island loss run through the real engine-free C++ core compiled to WebAssembly. The cryo supply and pole topology remain clearly labeled concepts.

## Build and preview

From the repository root:

```sh
nix develop .#ui -c make ui
nix develop .#ui -c make ui-preview
```

Open <http://127.0.0.1:8080/>. Stop with Ctrl+C. Use `UI_PORT=8081` for a different loopback port. The separate UI shell supplies Emscripten and Python. The default development shell stays light and does not need Emscripten or licensed game tools.

To preview another tuning file without editing `tools/balance/tuning.json`, pass its path. Run `make ui` again afterwards to return to the real file.

```sh
nix develop .#ui -c make ui TUNING=/tmp/tuning.json
```

```sh
nix build .#ui          # staged static browser package
nix run .#ui -- --port 8081
```

`build/ui/` contains staged original browser sources, fonts, generated `wasm/core.js` and `wasm/core.wasm`. `build/ui-wasm/` contains the generated tuning header and C++ objects. Generated files are not committed. Serve the built directory, not the source directory. A missing or failed WASM module produces an explicit error, never authored fallback traces.

Source files: `index.html`, `menu.css`, `menu.js`, and `wasm/`. The browser makes no external requests. `wasm/generate_tuning.py` reads the tuning file at every build and records its path and SHA-256 in the snapshot; the transformer details show both. Ratings, thermal thresholds, bank limits and tier capacities are not copied into JavaScript.

## Approved visual direction

The menus follow vanilla building interfaces: a compact building-name header, neutral molded instrument panels, operation lamp plus text, white circuit graph instruments, four-value legends, physical breaker controls and small value plates. There is no independent mod corporate identity, forced dashboard navigation or per-machine rule. Technical detail is collapsed.

The transformer has separate input and output circuit modules. The capacitor bank reuses the graph and breaker components, with an energy gauge and charge/discharge plates. The cryo station has a cooling-supply slot and a superconducting-line schematic. The pole mock adds only tier, loading and a feeding-transformer row to a connection/graph surface. The outside capacity-preview control selects metadata; its graph and feeder stay labeled as the fixed LV simulation.

The implementation specification is [docs/ui-spec.md](../../docs/ui-spec.md): native widget seams, widget tree, dimensions, data, states, input, localization and required assets.

## Controls and accessibility

- Choose a building and scenario with the preview controls outside the building menu.
- Pause freezes the core clock and graph history. Resume continues it. Restart resets the selected scenario and history, preserving pause state.
- The transformer breaker disconnects its link. After a thermal trip it requests the core's genuine manual reset, rejected while too hot. Connecting does not clear a latched trip.
- The capacitor breaker independently disconnects the bank and holds its stored energy. It does not disconnect the transformer. The bank status reads Charging, Discharging, Full, Idle, Empty or Disconnected from core values.
- The cryo concept control previews cooled and cooling-lost states. No cooling quantity, rate, recipe, warm capacity, warm loss or warm trip value is invented. The connected-line plates read `Uncapped`, `N/A` and `0 MW` while cooled.
- The pole menu has a read-only tier-capacity preview plate, preview loading and one feeding-transformer row. The graph and feeder labels, plus the condition strip, identify the fixed LV simulation. Native integration reads tier from network data; tier is not a pole setting.
- The `Capacity preview` study button outside the window cycles LV, MV, HV and SC. Finite preview loading compares the actual LV consumption with the selected tier capacity. SC metadata assumes a cooled, uncapped line: capacity is `Uncapped`, loading is `N/A` with no meter. It does not change the fixture loss model or transformer rating.
- Escape closes an open picker first, then the building menu. Closing moves focus to the reopen control. Opening focuses Close. Tab and Shift+Tab follow document order through the preview controls and the menu. Up/Down cycle visible menu or picker controls. Enter and Space activate native buttons.
- Status text accompanies lamp colors. SVG graphs have current-value accessible descriptions. Meters expose values and units. Focus outlines are visible. There are no flashing effects, and reduced-motion preferences are respected.

The display and rolling 60-second histories update at 4 Hz. Instrument, action and status nodes remain mounted between samples; only changed text, attributes and graph paths update. The layout changes only on building selection. The browser schedules 0.05-second core steps. The adapter subdivides at its generated tuning step and at each thermal time-constant boundary. Every subdivision advances the clock, also for a custom time constant that has no exact binary value. Wall-time accumulation is capped at 0.25 seconds per frame so returning from a background tab pauses elapsed simulation rather than causing a large catch-up jump.

## Real-core scenarios and limits

| Scenario | Behavior |
| --- | --- |
| Normal supply | Tuning-derived comfortable demand, actual capped transformer delivery, local loss and finite bank storage. No forced trip. |
| Sustained overload | Requested demand exceeds the conservative link rating. The bank helps until empty. Unserved MW and a capacity warning appear. Ordinary saturation does not fabricate a thermal trip. |
| Pulsed load | Tuning-derived demand alternates at the thermal time constant. Actual bank charge/discharge and unmet demand follow the core limits. |
| Upstream outage | Primary supply disappears after one thermal time constant. Initially funded transformer escrow and bank energy carry the output briefly, then exhaust. This is supply loss, not a false overload trip. |
| Empty grid | Demand and initial stored energy are zero. The transformer reads `No load`, not an outage. The graph is genuinely empty, not a prerecorded normal trace. |
| Thermal test (imposed load) | A labeled, externally imposed thermal ratio exercises warning, trip and reset through `StepThermal`, `ClassifyThermal`, `TimeToTrip` and `TryResetThermal`. Electrical transport remains hard-capped separately. This is not end-to-end transient-overload behavior. |

The adapter calls `PlanLink`, `SettleLink`, `StepBuffer` and `IslandLoss` for actual energy accounting. Transformer efficiency is explicitly unity because no conversion-efficiency tuning is specified. Escrow and capacitor initial energy are funded initial conditions, not created during the run. Snapshot details expose loss, storage, unserved demand and the cumulative energy residual.

**Core/gameplay gap:** `PlanLink` limits actual transfer to its rating. Heat driven by actual transfer therefore cannot produce an ordinary overload trip with the current thresholds. Delayed transient-overload capability is undecided. Local vanilla fuse behavior remains unknown until the separate real-game probe is run. The prototype does not change the core or invent a transport ceiling to hide that gap.

Cryo cooling is presentation-only. Only a cooled, uncapped, lossless SC line is modeled by current tuning. The pole has one simulated feeder, not discovered game topology. Optional electrical quality, PF, harmonic and frequency teaching dashboards from the older study have been removed; none are silently presented as implemented mechanics.

## Visual sources and licensing

Reference game captures and comparisons are kept only in untracked `notes/`; they are not runtime or public screenshot assets. Primary visual references:

- [Power Switch](https://satisfactory.wiki.gg/wiki/Power_Switch): dual circuits, white plotting modules, four-value legends, operation lamp and physical breaker.
- [Power poles](https://satisfactory.wiki.gg/wiki/Power_Poles): compact connection and circuit surface.
- [Pipeline Pump](https://satisfactory.wiki.gg/wiki/Pipeline_Pump): grouped physical gauges and white value plates. The retained pump reference is historical Early Access.
- [Constructor](https://satisfactory.wiki.gg/wiki/Constructor): building-name header, functional grouping and production status. The retained screenshot is historical.
- [MAM](https://satisfactory.wiki.gg/wiki/MAM): window chrome and focused hierarchy. Update 8 reference is historical; the recipe-choice 1.0 reference supplies a newer comparison.

Icons, instrument geometry and line diagrams are original SVG/CSS. No game logos, textures, screenshots or extracted UI assets are distributed. Roboto is a licensed browser substitute, not a claim about the game's proprietary font asset. Source: <https://github.com/google/fonts/tree/main/ofl/roboto>. The font and SIL Open Font License 1.1 are in `fonts/`.

## Captures

Tracked files under `renders/` show the earlier simulated-data study, not these menus. To inspect these menus, build and serve them with `nix develop .#ui -c make ui-preview`.

For comparable captures, use Normal supply, pause after 62 seconds of real core history and collapse the details. Captures of the browser menus are not in-game captures.
