'use strict';

const SAMPLE_SECONDS = 60;
const TICK_MILLISECONDS = 1000;
const state = { tick: 0, scenario: 'steady', selected: 'accelerator', paused: false, tab: 'overview', history: [] };
const elements = Object.fromEntries([...document.querySelectorAll('[id]')].map(element => [element.id, element]));
const equipment = {
  accelerator: { name: 'Accelerator connection', rating: 400 },
  factory: { name: 'Factory connection', rating: 600 },
  railway: { name: 'Railway backbone', rating: 1600 },
  generator: { name: 'Generator collection', rating: 1200 }
};

function sample(tick, scenario) {
  const outage = scenario === 'outage';
  const factoryTrip = scenario === 'overload' && tick >= 18;
  const acceleratorTrip = scenario === 'pulsed' && tick >= 22;
  const pulse = scenario === 'pulsed' && tick % 8 >= 4 && tick % 8 <= 6;
  const requestedFactory = scenario === 'overload' ? 720 : 480;
  const requestedAccelerator = pulse ? 540 : 180;
  const bufferPower = !outage && !acceleratorTrip && pulse ? 100 : 0;
  const factory = outage || factoryTrip ? 0 : requestedFactory;
  const accelerator = outage || acceleratorTrip ? 0 : requestedAccelerator - bufferPower;
  const load = outage ? 0 : factory + accelerator + 100;
  const loss = outage ? 0 : Math.round(load * 24 / 760);
  const production = outage ? 0 : 1200;
  const factoryThermal = factoryTrip ? 100 : scenario === 'overload' ? 45 + tick * 55 / 18 : 48;
  const acceleratorThermal = acceleratorTrip ? 100 : scenario === 'pulsed' ? Math.min(98, 42 + tick * 2.3) : 42;
  const dischargedSeconds = Math.floor(Math.min(tick, 22) / 8) * 3 + Math.max(0, Math.min(3, Math.min(tick, 22) % 8 - 4));
  const bufferEnergy = scenario === 'pulsed' ? 0.75 - dischargedSeconds * 100 / 3600 : 0.75;
  return { tick, production, factory, accelerator, load, loss, headroom: production - load - loss, factoryTrip, acceleratorTrip, outage, pulse, bufferPower, bufferEnergy, factoryThermal, acceleratorThermal };
}

function text(id, value) { elements[id].textContent = value; }
function power(id, value) { elements[id].innerHTML = `${value.toLocaleString('en-US')} <small>MW</small>`; }
function addEvent(time, message) {
  const entry = document.createElement('li');
  const timestamp = document.createElement('time');
  timestamp.textContent = `${time} s into demo`;
  entry.append(timestamp, document.createTextNode(message));
  elements.events.prepend(entry);
  while (elements.events.children.length > 5) elements.events.lastElementChild.remove();
}
function selectedTransfer(point) {
  return state.selected === 'factory' ? point.factory : state.selected === 'accelerator' ? point.accelerator : point.load + point.loss;
}
function localStatus(point, selected) {
  if (point.outage) return 'OFFLINE / UPSTREAM SUPPLY LOST';
  if ((selected === 'factory' && point.factoryTrip) || (selected === 'accelerator' && point.acceleratorTrip)) return 'TRIPPED / LOCAL FEED ISOLATED';
  if ((selected === 'factory' && state.scenario === 'overload') || (selected === 'accelerator' && point.pulse && state.scenario === 'pulsed')) return 'WARNING / ABOVE MW RATING';
  return 'CONNECTED / WITHIN RATING';
}

function drawChart(id, series, minimum, maximum, unit, height = 155, reference = null) {
  const width = id.includes('frequency') || id.includes('factor') ? 500 : 1000;
  const left = 52, right = width - 17, top = 15, bottom = height - 32;
  const x = index => left + index / SAMPLE_SECONDS * (right - left);
  const y = value => bottom - (value - minimum) / (maximum - minimum) * (bottom - top);
  let markup = '';
  for (let line = 0; line <= 4; line++) {
    const value = minimum + (maximum - minimum) * line / 4;
    const label = unit === 'PF' ? value.toFixed(2) : unit === 'Hz' ? value.toFixed(1) : Math.round(value);
    markup += `<line class="gridline" x1="${left}" y1="${y(value)}" x2="${right}" y2="${y(value)}"/><text text-anchor="end" x="${left - 10}" y="${y(value) + 3}">${label}</text>`;
  }
  for (let seconds = 0; seconds <= SAMPLE_SECONDS; seconds += 15) {
    markup += `<text text-anchor="middle" x="${x(seconds)}" y="${height - 12}">${seconds === SAMPLE_SECONDS ? 'now' : `${seconds - SAMPLE_SECONDS} s`}</text>`;
  }
  markup += `<text x="${left}" y="10">${unit === 'PF' ? 'PF (unitless)' : unit}</text>`;
  if (reference !== null) markup += `<line x1="${left}" y1="${y(reference)}" x2="${right}" y2="${y(reference)}" stroke="#7f8884" stroke-dasharray="3 5"/>`;
  for (const item of series) {
    markup += `<path class="series" stroke="${item.color}" ${item.dashed ? 'stroke-dasharray="7 5"' : ''} d="${item.values.map((value, index) => `${index ? 'L' : 'M'}${x(index).toFixed(1)},${y(value).toFixed(1)}`).join(' ')}"/>`;
  }
  elements[id].innerHTML = markup;
}

let filteredExample = false;
function drawHarmonics() {
  const harmonics = filteredExample ? [1, 0.08, 0.05, 0.04] : [1, 0.32, 0.2, 0.12];
  const orders = [1, 3, 5, 7];
  const x = milliseconds => 52 + milliseconds / 40 * 425;
  const y = amplitude => 95 - amplitude * 48;
  let waveform = '';
  for (const amplitude of [-1.5, 0, 1.5]) waveform += `<line class="gridline" x1="52" y1="${y(amplitude)}" x2="477" y2="${y(amplitude)}"/><text x="43" y="${y(amplitude) + 3}" text-anchor="end">${amplitude.toFixed(1)}</text>`;
  for (const milliseconds of [0, 10, 20, 30, 40]) waveform += `<text x="${x(milliseconds)}" y="196" text-anchor="middle">${milliseconds} ms</text>`;
  for (const reference of [true, false]) {
    const points = Array.from({ length: 241 }, (_, index) => {
      const milliseconds = index / 6;
      const phase = milliseconds / 20 * Math.PI * 2;
      const value = reference ? Math.sin(phase) : harmonics.reduce((sum, amplitude, harmonic) => sum + amplitude * Math.sin(phase * orders[harmonic]), 0);
      return `${index ? 'L' : 'M'}${x(milliseconds).toFixed(1)},${y(value).toFixed(1)}`;
    });
    waveform += `<path class="series" stroke="${reference ? '#858f8d' : '#308694'}" ${reference ? 'stroke-dasharray="5 5"' : ''} d="${points.join(' ')}"/>`;
  }
  elements['waveform-chart'].innerHTML = `<text x="52" y="10">Normalized current / fundamental peak = 1</text>${waveform}`;
  let spectrum = '<text x="52" y="10">Current amplitude / % of fundamental</text>';
  for (const percentage of [0, 50, 100]) {
    const vertical = 170 - percentage * 1.4;
    spectrum += `<line class="gridline" x1="52" y1="${vertical}" x2="477" y2="${vertical}"/><text x="42" y="${vertical + 3}" text-anchor="end">${percentage}%</text>`;
  }
  harmonics.forEach((amplitude, index) => {
    const horizontal = 88 + index * 115;
    spectrum += `<rect x="${horizontal - 17}" y="${170 - amplitude * 140}" width="34" height="${amplitude * 140}" fill="${index ? '#c78337' : '#308694'}"/><text x="${horizontal}" y="${163 - amplitude * 140}" text-anchor="middle">${Math.round(amplitude * 100)}%</text><text x="${horizontal}" y="187" text-anchor="middle">${orders[index] * 50} Hz</text><text x="${horizontal}" y="201" text-anchor="middle">H${orders[index]}</text>`;
  });
  elements['spectrum-chart'].innerHTML = spectrum;
  const currentTHD = Math.hypot(...harmonics.slice(1)) * 100;
  text('harmonic-explanation', `${filteredExample ? 'Filtered example' : 'Nonlinear load example'}: current THD ${currentTHD.toFixed(1)}% from the shown 3rd, 5th and 7th amplitudes relative to the fundamental. Voltage is not modeled. ${filteredExample ? 'Residual harmonics remain; this is not a universal correction.' : 'Compare selected harmonic reduction with the button above.'}`);
  text('filter-toggle', filteredExample ? 'Show unfiltered example' : 'Show filtered example');
  elements['filter-toggle'].setAttribute('aria-pressed', String(filteredExample));
}

function renderCharts() {
  drawChart('power-chart', [
    { color: '#899187', values: state.history.map(point => point.production) },
    { color: '#dc8e37', values: state.history.map(point => point.load + point.loss) }
  ], 0, 1600, 'MW', 370);
  drawChart('diagnostic-chart', [
    { color: '#308694', values: state.history.map(point => point.factory) },
    { color: '#d98830', values: state.history.map(point => point.accelerator) }
  ], 0, 800, 'MW', 220);
  const positions = Array.from({ length: SAMPLE_SECONDS + 1 }, (_, index) => index);
  drawChart('frequency-chart', [{ color: '#308694', values: positions.map(time => time < 15 ? 50 : 50 - 0.7 * Math.exp(-(time - 15) / 12) * Math.cos((time - 15) / 8)) }], 49, 51, 'Hz', 215, 50);
  drawChart('factor-chart', [{ color: '#c78337', values: positions.map(time => 0.92 - 0.13 * Math.exp(-((time - 25) ** 2) / 80)) }], 0.7, 1, 'PF', 215);
  drawHarmonics();
}

function render() {
  const point = sample(state.tick, state.scenario);
  power('production', point.production);
  power('load', point.load + point.loss);
  power('headroom', point.headroom);
  power('loss', point.loss);
  text('clock', `Demo: ${state.tick} s`);
  text('run-state', state.paused ? 'Paused' : 'Running');
  text('pause', state.paused ? 'Resume' : 'Pause');
  elements.pause.setAttribute('aria-pressed', String(state.paused));
  text('generator-state', `${point.production.toLocaleString('en-US')} MW available`);
  text('factory-note', `${point.factory} MW served`);
  text('backbone-state', point.outage ? 'No power' : 'Connected');
  text('factory-state', point.outage ? 'No power' : point.factoryTrip ? 'Disconnected: too hot' : state.scenario === 'overload' ? 'Too much load' : 'Connected');
  text('accelerator-state', point.outage ? 'No power' : point.acceleratorTrip ? 'Disconnected: too hot' : point.pulse ? 'Large power spike' : 'Connected');
  text('buffer-energy', `${point.bufferEnergy.toFixed(2)} MWh`);
  text('buffer-state', point.outage || point.acceleratorTrip ? 'Not connected' : point.bufferPower ? `Supplying ${point.bufferPower} MW` : 'Ready');
  elements.equipment.value = state.selected;
  const selected = equipment[state.selected];
  const status = localStatus(point, state.selected);
  const warning = status.startsWith('WARNING');
  const disconnected = status.startsWith('TRIPPED');
  text('equipment-name', selected.name);
  text('equipment-status', point.outage ? 'No power from generators' : disconnected ? 'Disconnected: too hot' : warning ? 'Too much load' : 'Connected');
  elements['equipment-status'].classList.toggle('danger', point.outage || disconnected || warning);
  const thermal = point.outage ? 20 : state.selected === 'factory' ? point.factoryThermal : state.selected === 'accelerator' ? point.acceleratorThermal : 36;
  text('thermal-value', disconnected ? 'Tripped' : warning ? 'Heating up' : 'Normal');
  elements['heat-fill'].style.width = `${thermal}%`;
  elements['heat-fill'].style.background = disconnected ? '#b75e39' : warning ? '#d39543' : '#879f76';
  text('equipment-load', `${selectedTransfer(point)} / ${selected.rating} MW`);
  text('equipment-explanation', point.outage ? 'The generators are offline. Restore their supply to power this connection again.' : disconnected ? 'This connection got too hot and switched off. The rest of your grid is still running.' : warning ? 'More power is passing through than this connection can handle. Add another transformer or split the load.' : state.selected === 'accelerator' ? 'This load fits comfortably. The nearby capacitor bank helps with short power spikes.' : state.selected === 'factory' ? 'This connection has room to spare. Normal factory operation stays below its limit.' : 'This part of the network is supplying the substation. Choose a factory connection to look more closely.');
  const tripped = point.factoryTrip || point.acceleratorTrip;
  text('grid-health', point.outage ? 'Generators offline' : tripped ? 'One area disconnected' : 'Power available');
  text('grid-explanation', point.outage ? 'No power is reaching the substation.' : tripped ? 'One connection switched off. The rest of the grid is still running.' : state.scenario === 'steady' ? 'Your grid has room to grow.' : 'There is enough generation, but a local connection is overloaded.');
  text('diagnostic-status', point.outage ? 'The generators are offline' : tripped ? 'One area switched off. The rest kept running.' : state.scenario === 'steady' ? 'Everything is running normally' : 'A connection is taking too much load');
  text('diagnostic-explanation', point.outage ? 'All downstream areas have lost their supply. This is not an overload trip. The small pulse buffer is not a backup generator.' : tripped ? `${point.factoryTrip ? 'The factory floor' : 'The accelerator'} overloaded its connection and was disconnected. Add capacity or reduce that load before restoring it. Restart demo to try again.` : state.scenario === 'overload' ? `The factory wants 720 MW through a 600 MW connection. Heat has been building for ${state.tick} seconds.` : state.scenario === 'pulsed' ? 'The accelerator has unusually large spikes. Even with help from its capacitor, those peaks exceed the connection limit.' : 'There is enough generation and both factory connections are within their limits. No action needed.');
  document.querySelectorAll('[data-select]').forEach(button => {
    button.setAttribute('aria-pressed', String(button.dataset.select === state.selected));
  });
  renderCharts();
}

function resetScenario() {
  state.tick = 0;
  elements.events.replaceChildren();
  state.history = Array.from({ length: SAMPLE_SECONDS + 1 }, () => sample(0, 'steady'));
  state.history[SAMPLE_SECONDS] = sample(0, state.scenario);
  addEvent(0, { steady: 'Normal sample loaded. All feeds connected.', overload: 'Factory demand stepped to 720 MW. TX-03 thermal warning.', pulsed: 'Accelerator pulse sequence armed. 100 MW buffer discharge limit.', outage: 'Generator group unavailable. HV and LV islands de-energized.' }[state.scenario]);
  render();
}
function selectTab(name, focus = false) {
  state.tab = name;
  for (const tab of document.querySelectorAll('[data-tab]')) {
    const active = tab.dataset.tab === name;
    tab.setAttribute('aria-selected', String(active));
    tab.tabIndex = active ? 0 : -1;
    elements[tab.dataset.tab].hidden = !active;
    if (active && focus) tab.focus();
  }
}

document.addEventListener('click', event => {
  const selection = event.target.closest('[data-select]');
  if (selection) {
    state.selected = selection.dataset.select;
    if (state.tab === 'islands') selectTab('overview', true);
    render();
  }
  const tab = event.target.closest('[data-tab]');
  if (tab) selectTab(tab.dataset.tab);
});
document.querySelector('[role=tablist]').addEventListener('keydown', event => {
  const keys = ['ArrowLeft', 'ArrowRight', 'Home', 'End'];
  if (!keys.includes(event.key)) return;
  event.preventDefault();
  const names = ['overview', 'islands', 'diagnostics', 'quality'];
  const index = names.indexOf(state.tab);
  selectTab(names[event.key === 'Home' ? 0 : event.key === 'End' ? 3 : (index + (event.key === 'ArrowRight' ? 1 : 3)) % 4], true);
});
elements.scenario.addEventListener('change', () => { state.scenario = elements.scenario.value; resetScenario(); });
elements.pause.addEventListener('click', () => { state.paused = !state.paused; render(); });
elements.reset.addEventListener('click', resetScenario);
elements.equipment.addEventListener('change', () => { state.selected = elements.equipment.value; render(); });
elements['filter-toggle'].addEventListener('click', () => { filteredExample = !filteredExample; drawHarmonics(); });
resetScenario();
setInterval(() => {
  if (state.paused) return;
  state.tick++;
  const point = sample(state.tick, state.scenario);
  state.history.push(point);
  if (state.history.length > SAMPLE_SECONDS + 1) state.history.shift();
  if (state.scenario === 'overload' && state.tick === 18) addEvent(state.tick, 'TX-03 local trip latched. Factory isolated; accelerator remains supplied.');
  if (state.scenario === 'pulsed' && state.tick <= 22 && state.tick % 8 === 4) addEvent(state.tick, 'Pulse peak: 540 MW demand, 100 MW buffer, 440 MW transformer transfer.');
  if (state.scenario === 'pulsed' && state.tick === 22) addEvent(state.tick, 'Third pulse peak: TX-04 local trip latched. Factory remains supplied.');
  render();
}, TICK_MILLISECONDS);
