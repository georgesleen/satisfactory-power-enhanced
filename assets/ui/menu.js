'use strict';

const $ = selector => document.querySelector(selector);
const menu = $('.interaction-window');
const names = { transformer: 'Transformer', capacitor: 'Capacitor bank', cryo: 'Cryo station', pole: 'Power pole' };
const scenarioNames = ['Normal supply', 'Thermal test (imposed load)', 'Pulsed load', 'Upstream outage', 'Empty grid', 'Sustained overload'];
let building = 'transformer';
let cooled = true;
let poleTier = 'LV';
let sample;
let coreAPI;
let paused = false;
let scenario = 0;
let history = [];
let accumulator = 0;
let sinceSample = 0;
let previousFrame;
let renderedBuilding;
const numbers = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 });
const decimals = new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 });
const format = (value, digits = 0) => (digits ? decimals : numbers).format(value);
const icon = name => `<svg aria-hidden="true"><use href="#${name}"/></svg>`;
const valuePlate = (value, unit, caption) => `<div class="value-plate"><strong>${value} <small>${unit}</small></strong><span>${caption}</span></div>`;
const statusModule = (status, warning = false) => `<div class="instrument status-module"><div class="status-lamp" aria-hidden="true"></div><div class="black-plate">${icon(warning ? 'warning' : 'check')}<strong id="operation-status" role="status">${status}</strong></div></div><div class="vent" aria-hidden="true"><i></i><i></i><i></i><i></i></div>`;
const meter = (percent, label, className = 'load-meter') => `<div class="${className}" role="meter" aria-label="${label}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.min(100, percent)}" aria-valuetext="${format(percent)} percent"><i style="${className === 'heat-meter' ? 'height' : 'width'}:${Math.min(100, percent)}%"></i></div>`;
const detailList = rows => `<dl>${rows.map(([label, value]) => `<div><dt>${label}</dt><dd>${value}</dd></div>`).join('')}</dl>`;
function breakerControl(disconnected, tripped = false) {
  return `<div class="breaker-module"><button id="breaker" class="breaker" aria-pressed="${disconnected}" aria-label="${tripped ? 'Reset transformer breaker' : `${disconnected ? 'Connect' : 'Disconnect'} ${names[building].toLowerCase()}`}"><span class="breaker-track" aria-hidden="true"><span class="breaker-arrow"></span><span class="breaker-handle"></span></span><span class="plate-label">${tripped ? 'RESET BREAKER' : disconnected ? 'CONNECT' : 'DISCONNECT'}</span></button></div>`;
}

function graph(label, tier, id) {
  const values = sample[id];
  const entries = history.length ? history : [sample];
  const scale = Math.max(1, ...entries.flatMap(entry => Object.values(entry[id]))) * 1.06;
  const start = sample.seconds - 60;
  const trace = key => entries.map((entry, index) => `${index ? 'L' : 'M'}${Math.max(0, (entry.seconds - start) / 60 * 690).toFixed(2)} ${(212 - entry[id][key] / scale * 206).toFixed(2)}`).join(' ');
  return `<article class="instrument circuit" data-grid="${id}"><h2 class="circuit-label"><span>${label}</span><b>${tier}</b></h2><div class="graph-module"><div class="plot"><svg class="power-graph" viewBox="0 0 690 218" role="img" aria-label="${label} grid. Last 60 seconds of real core history. Consumption ${format(values.consumption)} MW, production ${format(values.production)} MW, capacity ${format(values.capacity)} MW, maximum consumption ${format(values.maxConsumption)} MW."><path class="capacity" d="${trace('capacity')}"/><path class="production" d="${trace('production')}"/><path class="maximum" d="${trace('maxConsumption')}"/><path class="consumption" d="${trace('consumption')}"/></svg></div><dl class="graph-legend">${[['Consumption', 'consumption', 'consumption'], ['Production', 'production', 'production'], ['Capacity', 'capacity', 'capacity'], ['Max. Consumption', 'maxConsumption', 'maximum']].map(([label, key, style]) => `<div><dt><i class="${style}-key"></i>${label}</dt><dd class="${style}-text" data-value="${key}">${format(values[key])} MW</dd></div>`).join('')}</dl></div><span class="plate-label graph-label">${label.toUpperCase()} GRID</span></article>`;
}

// A mounted instrument keeps its nodes while readings and attributes change.
function updateInstrument(element, markup, rebuild) {
  const template = document.createElement('template');
  template.innerHTML = markup;
  if (rebuild) {
    element.replaceChildren(template.content);
    return;
  }
  function updateNode(current, next) {
    if (current.nodeType === Node.TEXT_NODE) {
      if (current.nodeValue !== next.nodeValue) current.nodeValue = next.nodeValue;
      return;
    }
    for (const attribute of [...current.attributes]) {
      if (!next.hasAttribute(attribute.name)) current.removeAttribute(attribute.name);
    }
    for (const attribute of next.attributes) {
      if (current.getAttribute(attribute.name) !== attribute.value) current.setAttribute(attribute.name, attribute.value);
    }
    updateChildren(current, next);
  }
  function updateChildren(current, next) {
    const children = [...current.childNodes];
    [...next.childNodes].forEach((child, index) => {
      if (!children[index]) current.append(child.cloneNode(true));
      else updateNode(children[index], child);
    });
    for (let index = next.childNodes.length; index < children.length; index++) children[index].remove();
  }
  updateChildren(element, template.content);
}

function renderBuilding() {
  if (!sample) return;
  const rebuild = renderedBuilding !== building;
  const transformerDisconnected = !sample.connectionRequested;
  const bankDisconnected = !sample.bufferConnected;
  const tripped = sample.thermalStatus === 'tripped';
  const thermalWarning = sample.thermalStatus === 'warning';
  const disconnected = building === 'capacitor' ? bankDisconnected : transformerDisconnected || tripped;
  let controls;
  let instruments;
  let condition;
  let details;
  let warning = false;
  menu.classList.toggle('isolated', disconnected && ['transformer', 'capacitor'].includes(building));
  menu.classList.toggle('cooling-lost', !cooled && building === 'cryo');
  menu.classList.toggle('tripped', tripped && building === 'transformer');
  menu.dataset.building = building;
  $('#building-name').textContent = names[building];
  document.title = `${names[building]} - Power building menus`;
  $('#building-picker span').textContent = names[building];
  $('.technical summary').textContent = `${names[building]} details`;
  $('.close').setAttribute('aria-label', `Close ${names[building].toLowerCase()} menu`);
  if (building === 'transformer') {
    const emptyGrid = sample.scenario === 4;
    warning = thermalWarning || tripped || sample.saturated || (!sample.upstreamAvailable && !emptyGrid);
    const status = tripped ? 'BREAKER TRIPPED' : transformerDisconnected ? 'DISCONNECTED' : emptyGrid ? 'NO LOAD' : !sample.upstreamAvailable ? 'UPSTREAM LOST' : thermalWarning ? 'HEAT WARNING' : sample.saturated ? 'AT CAPACITY' : 'OPERATIONAL';
    const heatLabel = tripped ? 'Tripped' : thermalWarning ? 'Warning' : 'Normal';
    controls = statusModule(status, warning) + `<section class="instrument transfer-module"><h2>Power transfer</h2><div class="transfer-path"><span>MV</span>${icon('arrow')}<span>LV</span></div>${valuePlate(format(sample.transfer), 'MW', `of ${format(sample.rating)} MW`)}${meter(sample.loadPercent, 'Transformer load')}<div class="rating-label">LOAD <span>${format(sample.loadPercent)}%</span></div></section><section class="instrument heat-module">${icon('heat')}<div><strong id="heat-status">${heatLabel}</strong><span>Transformer heat</span></div>${meter(sample.heatPercent, 'Heat relative to trip threshold', 'heat-meter')}</section>` + breakerControl(transformerDisconnected || tripped, tripped);
    instruments = graph('Input', 'MV', 'input') + graph('Output', 'LV', 'output');
    condition = tripped ? `The local breaker has tripped. ${sample.heat >= sample.tuning.warningHeat ? 'Wait for the transformer to cool, then reset it.' : 'The transformer has cooled. Reset the breaker to restore the feed.'}` : transformerDisconnected ? 'This transformer is disconnected. Connect it to restore the output feed.' : emptyGrid ? 'No connected load. The grid has no supply and no demand.' : !sample.upstreamAvailable ? 'Upstream supply is lost. Stored energy can carry the output only briefly.' : thermalWarning ? 'Transformer heat is high. Reduce the load and let it cool, or the breaker trips.' : sample.unservedMW > 0.01 ? `Connection at capacity. ${format(sample.unservedMW)} MW is unserved. Add another feed or reduce load. A buffer helps short peaks.` : sample.saturated ? 'Connection at capacity. The bank is covering the shortfall. Add another feed for sustained demand.' : 'Power is available. This transformer has capacity for more load.';
    details = detailList([['Input / output', 'MV / LV'], ['Requested demand', `${format(sample.requestedLoadMW)} MW`], ['Unserved demand', `${format(sample.unservedMW)} MW`], ['Heat / trip threshold', `${format(sample.heat, 1)} / ${format(sample.tuning.tripHeat, 1)}`], ['Thermal load', `${format(sample.thermalLoadRatio * 100, 1)}%${sample.diagnostic ? ' imposed test' : ' actual transfer'}`], ['Time to trip at this load', sample.timeToTrip === null ? 'No trip predicted' : `${format(sample.timeToTrip, 1)} s`], ['Transformer energy store', `${format(sample.escrowStoredMJ, 1)} MJ`], ['Transmission loss', `${format(sample.lossMW, 1)} MW`], ['Energy accounting residual', `${sample.energyResidualMJ.toExponential(2)} MJ`]]) + `<p>${sample.diagnostic ? 'Diagnostic only. Thermal load is externally imposed. The graph still shows conservative hard-capped link transport, not an end-to-end overload model.' : 'The current link caps delivered power at its rating. Saturation can leave demand unserved without causing a thermal trip. Transient overload capability is undecided.'}</p>`;
  } else if (building === 'capacitor') {
    const storedPercent = sample.bufferCapacityMJ > 0 ? sample.bufferStoredMJ / sample.bufferCapacityMJ * 100 : 0;
    const absorbed = sample.bufferAbsorbedMW;
    const delivered = sample.bufferDeliveredMW;
    const empty = sample.bufferStoredMJ < 0.01;
    const full = sample.bufferCapacityMJ - sample.bufferStoredMJ < 0.01;
    const status = bankDisconnected ? 'DISCONNECTED' : empty ? 'EMPTY' : delivered > 0.01 ? 'DISCHARGING' : absorbed > 0.01 ? 'CHARGING' : full ? 'FULL' : 'IDLE';
    warning = empty && !bankDisconnected;
    controls = statusModule(status, warning) + `<section class="instrument transfer-module"><h2>Stored energy</h2><div class="storage-emblem">${icon('storage')}</div>${valuePlate(format(sample.bufferStoredMJ / 3600, 1), 'MWh', `of ${format(sample.bufferCapacityMJ / 3600, 1)} MWh`)}${meter(storedPercent, 'Stored energy')}<div class="rating-label">CHARGE <span>${format(storedPercent)}%</span></div></section><section class="instrument heat-module">${icon('bolt')}<div><strong>Automatic</strong><span>Responds to grid balance</span></div></section>` + breakerControl(bankDisconnected);
    instruments = graph('Connected', 'LV', 'output') + `<article class="instrument storage-instrument"><h2>Energy storage</h2><div class="storage-gauge" role="meter" aria-label="Stored energy" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${storedPercent}"><div class="storage-fill" style="width:${storedPercent}%"></div><div class="storage-segments" aria-hidden="true"></div><strong>${format(storedPercent)}<small>%</small></strong></div><div class="storage-readings"><div><span>Charge rate</span><strong>${format(absorbed)} <small>MW</small></strong></div><div><span>Discharge rate</span><strong>${format(delivered)} <small>MW</small></strong></div></div><p>Stores surplus power. Supports the grid during short peaks.</p><span class="plate-label graph-label">CAPACITOR BANK</span></article>`;
    condition = bankDisconnected ? 'The bank is disconnected. Stored energy is held until it is connected.' : empty ? 'The bank is empty. Restore spare supply to recharge it. It cannot cover a sustained deficit.' : delivered > 0.01 ? 'The bank is supporting the grid. Stored energy is falling.' : absorbed > 0.01 ? 'The bank is charging from spare supply. It will help the next short peak.' : full ? 'The bank is full. It can cover short peaks, not a sustained supply deficit.' : 'The bank is idle. A surplus charges it and a deficit discharges it.';
    details = detailList([['Connected grid', 'LV'], ['Stored energy', `${format(sample.bufferStoredMJ, 1)} MJ`], ['Maximum charge', `${format(sample.tuning.maxChargeMW)} MW`], ['Maximum discharge', `${format(sample.tuning.maxDischargeMW)} MW`], ['Charge efficiency', `${format(sample.tuning.capacitorBank.chargeEfficiency * 100)}%`], ['Control', 'Automatic charge and discharge']]) + '<p>Extra storage lasts longer, but does not add generation. The bank delivers only energy it already holds.</p>';
  } else if (building === 'cryo') {
    warning = !cooled;
    controls = statusModule(cooled ? 'COOLED' : 'COOLING LOST', warning) + `<section class="instrument transfer-module"><h2>Line condition</h2><div class="storage-emblem snow-emblem">${icon('snow')}</div>${valuePlate(cooled ? 'Superconducting' : 'Not cooled', '', cooled ? 'Cooling available' : 'Restore cooling supply')}<div class="line-tier"><span class="plate-label">SC LINE</span><strong>${cooled ? 'Zero transmission loss' : 'Warm behavior not set'}</strong></div></section><section class="instrument heat-module">${icon('info')}<div><strong>${cooled ? 'No capacity cap' : 'Warm rules not set'}</strong><span>End transformers remain rated</span></div></section>`;
    instruments = `<article class="instrument supply-instrument"><h2>Cooling supply</h2><div class="supply-body"><div class="supply-slot">${icon('snow')}</div><div><strong>${cooled ? 'Supply available' : 'Supply missing'}</strong><p>Cooling keeps the connected line superconducting.</p><span class="recipe-note">Recipe and consumption rate not specified</span></div></div><div class="supply-flow"><span>Cooling input</span>${icon('arrow')}<span>SC line</span></div><span class="plate-label graph-label">CRYO STATION</span></article><article class="instrument line-instrument"><h2>Connected line</h2><div class="line-schematic" aria-label="Superconducting line between two rated transformers"><span class="transformer-glyph">MV<br><b>SC</b></span><div class="sc-line">${icon('snow')}<span>SC</span></div><span class="transformer-glyph">SC<br><b>LV</b></span></div><div class="line-readings"><div><span>Capacity</span><strong>${cooled ? 'Uncapped' : 'Not specified'}</strong></div><div><span>Loading</span><strong>N/A</strong></div><div><span>Transmission loss</span><strong>${cooled ? '0 MW' : 'Not specified'}</strong></div></div><p>Power is limited by the transformers at each end, not by cooling quantity.</p><span class="plate-label graph-label">LINE STATUS</span></article>`;
    condition = cooled ? 'The line is superconducting. Keep its cooling supply connected.' : 'Cooling is missing. Restore the supply. Warm-line loss and trip rules are not specified yet.';
    details = detailList([['Cooling state', 'Presentation concept only'], ['Cooling recipe', 'Not specified'], ['Warm capacity and loss', 'Not specified'], ['Warm trip behavior', 'Not specified']]) + '<p>The current core models only cooled, lossless, uncapped SC. The preview control changes the visual state, not a cooling simulation.</p>';
  } else {
    const capacity = sample.tuning.tierCapacitiesMW[poleTier];
    const percent = capacity === null ? null : sample.consumption / capacity * 100;
    controls = `<section class="instrument pole-connections"><h2>Connections</h2><div class="connection-sockets" aria-hidden="true"><i></i><i></i><i></i><i></i></div><strong>Grid connection</strong></section><section class="instrument transfer-module"><h2>Tier capacity preview</h2><div class="tier-plate">${poleTier}<span>Capacity metadata only</span></div>${valuePlate(capacity === null ? 'Uncapped' : format(capacity), capacity === null ? '' : 'MW', `${poleTier} capacity preview`)}<div${percent === null ? ' hidden' : ''}>${meter(percent ?? 0, 'Preview loading')}</div><div class="rating-label">PREVIEW LOADING <span>${percent === null ? 'N/A' : `${format(percent, 1)}%`}</span></div></section>`;
    instruments = graph('LV fixture', 'LV', 'output') + `<article class="instrument feeds-instrument"><h2>Feeding transformers</h2><div class="feed-row">${icon('bolt')}<div><strong>Transformer</strong><span>MV to LV - simulation fixture</span></div><b>${format(sample.transfer)} <small>MW</small></b><span class="feed-condition">${sample.thermalStatus === 'tripped' ? 'Tripped' : !sample.connectionRequested ? 'Disconnected' : sample.scenario === 4 ? 'No load' : !sample.upstreamAvailable ? 'Upstream lost' : 'Connected'}</span></div><span class="plate-label graph-label">LV FIXTURE FEED</span></article>`;
    condition = 'Capacity and loading are a tier preview. The graph and feeder show the fixed LV simulation.';
    details = detailList([['Surface', 'Vanilla pole menu mock'], ['Preview tier', poleTier], ['Preview capacity', capacity === null ? 'Uncapped' : `${format(capacity)} MW`], ['Preview loading', percent === null ? 'N/A' : `${format(percent, 1)}%`], ['Simulated circuit', 'Fixed LV fixture'], ['Feeding transformers', 'One simulated MV to LV feeder']]) + '<p>The outside tier control changes capacity metadata only. Preview loading compares the LV fixture consumption with the selected tier capacity. SC capacity is uncapped while cooled; its preview loading is N/A. The graph and feeder retain the LV loss model. Native integration reads tier and feeding transformers from the actual grid topology.</p>';
  }
  menu.classList.toggle('warning', warning);
  updateInstrument($('.operation-column'), controls, rebuild);
  updateInstrument($('.circuit-column'), instruments, rebuild);
  if ($('#condition').textContent !== condition) $('#condition').textContent = condition;
  updateInstrument($('#technical-content'), details + `<p class="provenance">Initial tuning - ${sample.tuning.source} - SHA-256 ${sample.tuning.sha256.slice(0, 12)}</p>`, rebuild);
  if (rebuild) {
    $('#cooling-preview')?.remove();
    $('#pole-tier')?.remove();
    if (building === 'cryo') {
      const button = document.createElement('button');
      button.id = 'cooling-preview';
      button.addEventListener('click', () => { cooled = !cooled; renderBuilding(); });
      $('.preview-toolbar').append(button);
    }
    if (building === 'pole') {
      const button = document.createElement('button');
      button.id = 'pole-tier';
      button.setAttribute('aria-label', 'Change capacity preview tier');
      button.addEventListener('click', () => {
        const tiers = ['LV', 'MV', 'HV', 'SC'];
        poleTier = tiers[(tiers.indexOf(poleTier) + 1) % tiers.length];
        renderBuilding();
      });
      $('.preview-toolbar').append(button);
    }
    renderedBuilding = building;
  }
  const coolingButton = $('#cooling-preview');
  if (coolingButton) {
    const label = `Concept: ${cooled ? 'cooled' : 'cooling lost'}`;
    if (coolingButton.textContent !== label) coolingButton.textContent = label;
  }
  const tierButton = $('#pole-tier');
  if (tierButton) {
    const label = `Capacity preview: ${poleTier}`;
    if (tierButton.textContent !== label) tierButton.textContent = label;
  }
  $('#preview-status').textContent = `${paused ? 'Paused' : 'Live core'} - ${format(sample.seconds, 1)} s`;
  $('#runtime-note').textContent = sample.diagnostic ? `Thermal test: ${format(sample.imposedThermalRatio * 100, 1)}% imposed load. Not end-to-end link overload.` : building === 'cryo' ? 'Cooling concept only. Real core is running independently. No game connection.' : 'Real C++ core simulation. No game connection.';
}

function takeSnapshot() {
  sample = JSON.parse(coreAPI.snapshot());
  if (sample.error) throw new Error(sample.error);
  history.push(sample);
  while (history.length > 1 && history[1].seconds < sample.seconds - 60) history.shift();
}
function advanceSimulation(seconds) {
  coreAPI.step(seconds);
  takeSnapshot();
  renderBuilding();
}
function resetScenario() {
  coreAPI.reset(scenario);
  coreAPI.step(0.05);
  history = [];
  accumulator = 0;
  sinceSample = 0;
  takeSnapshot();
  renderBuilding();
}
function frame(timestamp) {
  const delta = previousFrame === undefined ? 0 : Math.min(0.25, (timestamp - previousFrame) / 1000);
  previousFrame = timestamp;
  if (!paused) {
    accumulator += delta;
    while (accumulator >= 0.05) {
      coreAPI.step(0.05);
      accumulator -= 0.05;
      sinceSample += 0.05;
    }
    if (sinceSample >= 0.25 - 1e-9) {
      sinceSample %= 0.25;
      takeSnapshot();
      if (!menu.hidden) renderBuilding();
    }
  }
  requestAnimationFrame(frame);
}
function closeMenu() {
  menu.hidden = true;
  $('#reopen').hidden = false;
  $('#reopen').focus();
}
function closePickers() {
  document.querySelectorAll('.picker-options').forEach(element => { element.hidden = true; });
  document.querySelectorAll('.preview-picker > button').forEach(element => element.setAttribute('aria-expanded', 'false'));
}
$('.close').addEventListener('click', closeMenu);
$('#reopen').addEventListener('click', () => { renderBuilding(); menu.hidden = false; $('#reopen').hidden = true; $('.close').focus(); });
document.querySelectorAll('.preview-picker > button').forEach(button => button.addEventListener('click', () => {
  const options = document.getElementById(button.getAttribute('aria-controls'));
  const opening = options.hidden;
  closePickers();
  options.hidden = !opening;
  button.setAttribute('aria-expanded', String(opening));
  if (opening) options.querySelector('button').focus();
}));
$('#building-options').addEventListener('click', event => {
  const button = event.target.closest('[data-building]');
  if (!button) return;
  building = button.dataset.building;
  closePickers();
  if (sample) menu.hidden = false;
  $('#reopen').hidden = true;
  $('.technical').open = false;
  renderBuilding();
  $('#building-picker').focus();
});
$('#scenario-options').addEventListener('click', event => {
  const button = event.target.closest('[data-scenario]');
  if (!button || !coreAPI) return;
  scenario = Number(button.dataset.scenario);
  $('#scenario-picker span').textContent = scenarioNames[scenario];
  closePickers();
  resetScenario();
  $('#scenario-picker').focus();
});
$('#pause').addEventListener('click', () => {
  paused = !paused;
  $('#pause').textContent = paused ? 'Resume' : 'Pause';
  renderBuilding();
});
$('#restart').addEventListener('click', resetScenario);
menu.addEventListener('click', event => {
  if (!event.target.closest('#breaker') || !coreAPI) return;
  if (building === 'capacitor') coreAPI.setBufferConnected(sample.bufferConnected ? 0 : 1);
  else if (sample.thermalStatus === 'tripped') {
    if (!coreAPI.resetBreaker()) {
      $('#condition').textContent = 'The transformer is still too hot. Wait for it to cool, then reset the breaker.';
      return;
    }
  } else coreAPI.setConnected(sample.connectionRequested ? 0 : 1);
  advanceSimulation(0.05);
  $('#breaker').focus();
});
document.addEventListener('click', event => { if (!event.target.closest('.preview-picker')) closePickers(); });
document.addEventListener('keydown', event => {
  const openPicker = [...document.querySelectorAll('.picker-options')].find(element => !element.hidden);
  if (event.key === 'Escape') {
    if (openPicker) { const button = document.querySelector(`[aria-controls="${openPicker.id}"]`); closePickers(); button.focus(); }
    else if (!menu.hidden) closeMenu();
    return;
  }
  if (!['ArrowDown', 'ArrowUp'].includes(event.key)) return;
  const container = openPicker || menu;
  if (container.hidden) return;
  const focusable = [...container.querySelectorAll('button, summary')].filter(element => !element.disabled);
  const index = focusable.indexOf(document.activeElement);
  if (index < 0) return;
  event.preventDefault();
  focusable[(index + (event.key === 'ArrowDown' ? 1 : focusable.length - 1)) % focusable.length].focus();
});

(async function initialize() {
  try {
    if (typeof EnhancedPowerCore !== 'function') throw new Error('WASM loader is missing. Build the UI with nix develop .#ui -c make ui.');
    const module = await EnhancedPowerCore();
    coreAPI = {
      reset: module.cwrap('ui_reset', null, ['number']),
      step: module.cwrap('ui_step', null, ['number']),
      snapshot: module.cwrap('ui_snapshot', 'string', []),
      setConnected: module.cwrap('ui_set_connected', null, ['number']),
      setBufferConnected: module.cwrap('ui_set_buffer_connected', null, ['number']),
      resetBreaker: module.cwrap('ui_reset_breaker', 'number', [])
    };
    resetScenario();
    menu.hidden = false;
    $('.close').focus();
    $('#pause').disabled = false;
    $('#restart').disabled = false;
    requestAnimationFrame(frame);
  } catch (error) {
    $('#preview-status').textContent = `Core unavailable: ${error.message}`;
    $('#runtime-note').textContent = 'No authored fallback data is displayed.';
    console.error(error);
  }
})();
