# Substation interaction prototype

A standalone browser study of an Enhanced Power building menu. **Not Unreal, SML, or game integration.** All readings and events are simulated. Demo controls affect only the local example.

## Preview

From the repository root, with Python 3 available:

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory assets/ui
```

Open <http://127.0.0.1:8765/>. Stop with Ctrl+C. Source: `index.html`, `terminal.css`, `terminal.js`. No build, packages, external fonts, CDN, network APIs, or third-party JavaScript. The preview itself makes no external requests. SVG illustrations are original; no game logos or textures are included.

## Visual references

These actual wiki-hosted game screenshots were opened and visually inspected in Chromium before redesigning the menu. They are references, not runtime assets or claims of game integration:

- [Power pole interface](https://satisfactory.wiki.gg/images/Power_pole_-_graph.png), from the [official wiki Power page](https://satisfactory.wiki.gg/wiki/Power): a large white plotting surface, simple colored graph legend/readings beneath it, and a compact adjacent storage module. This drives the default view's graph-first structure and three plain-language totals.
- [Pipeline interface](https://satisfactory.wiki.gg/images/Pipeline_Water_content.png), from [Pipelines](https://satisfactory.wiki.gg/wiki/Pipelines): grouped physical gauge/readout/control modules, a thin window titlebar, and pale value plates. This drives the separate connection module, visual transformer illustration, simple heat bar, and capacitor readout. No copied dial or flush control is used.
- [MAM general research interface, Update 3-8](https://satisfactory.wiki.gg/images/Update_8_-_MAM_4.png), from [MAM](https://satisfactory.wiki.gg/wiki/MAM): focused content with a narrow selection area and recognizable window chrome. This is explicitly a historical reference, not a claim about the latest game's MAM. The prototype uses a slim titlebar and a small set of familiar menu tabs rather than a telemetry wall.

The palette is an original pale gray modular interpretation with orange selections, not a pixel-perfect recreation. The default menu deliberately omits serial numbers, tier jargon, topology, equations and detailed diagnostics. Connections, event explanations and optional quality concepts are secondary views. It is a building interaction menu, not a control-room dashboard.

## Interaction

- **Power:** large production/usage history, power produced, power used, spare capacity, selected connection, one plain-language explanation, and a small capacitor bank module. The connection selector changes the inspected equipment.
- **Connections:** a secondary generator -> railway -> substation -> factory/accelerator diagram. Select a connection to inspect it in Power. It shows connected areas, not solved individual-wire current.
- **What happened?:** a plain-language cause and local consequence, recent events, and the two transformer traces.
- **Power quality:** optional research presentation. A simple power-triangle explanation comes first; waveform/spectrum/frequency/PF illustrations are behind an expandable detail section.
- **Try the demo:** normal operation, sustained factory overload, oversized accelerator spikes, and generator outage. Pause freezes the sample clock and histories. Restart clears the selected scenario's events/trip and starts at zero, preserving pause state. Neither control sends a game command.

Tabs support Left/Right, Home and End. Native controls, visible keyboard focus, stable connection buttons and textual status accompany color. Event announcements occur only when an event is added, not on every sample tick. No smooth or flashing animation is used; reduced-motion rules are included. Smaller screens stack modules.

## Sample contract

One-second deterministic samples feed a rolling 60-second history. Pre-trigger history is normal operation. Ratings, loss and protection timing are authored design samples, not final balance or a physical grid/thermal solver.

| Scenario | Behavior |
| --- | --- |
| Normal | 1,200 MW produced; 480 MW factory + 180 MW accelerator + 100 MW auxiliaries; 24 MW sample loss. The main view shows 784 MW power used, including that loss, leaving 416 MW spare. |
| Factory overload | Factory requests 720 MW through a 600 MW connection. It heats, then trips at 18 s; accelerator remains supplied. |
| Oversized spikes | Accelerator requests 540 MW at seconds 4-6 of each 8-second cycle. Buffer provides 100 MW; remaining 440 MW exceeds a 400 MW connection. That connection trips during its third peak at 22 s. Factory remains supplied. |
| Generators offline | Production and downstream power fall to zero. Connections show loss of supply, not false local overload trips. The pulse buffer is isolated, not a modeled black-start source. |

Power used includes upstream transformer transfer, auxiliary load and sample losses. Capacitor discharge is additional power delivered locally, not upstream consumption. The buffer begins at 0.75 MWh and falls by discharged MW times seconds / 3,600; no recharge sequence is modeled. Heat is an illustrative warning indicator, not temperature. Trips latch until demo restart.

## Optional quality concepts

These are not implemented or committed game mechanics:

- Sinusoidal teaching example: 700 MW + 500 Mvar requires 860.23 MVA, using 86% of a sample 1,000 MVA connection and leaving 139.77 MVA spare; PF is 0.814. This triangle assumes no harmonics and cannot alone determine distorted apparent power.
- Normalized two-cycle current waveform and authored 50/150/250/350 Hz component amplitudes. Not an FFT or game measurement.
- Reversible filtered/unfiltered comparison reduces selected harmonics and calculates residual current THD from those amplitudes. Voltage THD, resonance and real filter design are not modeled.
- Separate illustrative fundamental-frequency recovery and true-PF history. These do not affect the main scenarios.

MW is real power, MWh stored energy, Hz frequency, Mvar reactive power and MVA apparent power. Displacement PF describes fundamental phase; true PF also reflects distortion. A MW/MWh pulse-energy capacitor bank is not a reactive correction bank or a universal harmonic filter. No example creates free energy or assumes all fictional machines are inductive.

## Review captures

`renders/overview.png`, `renders/diagnostics.png`, and `renders/quality.png` are actual Chromium screenshots of this menu, not in-game renders. The default view is designed for 1280x900; optional detail views can scroll.
