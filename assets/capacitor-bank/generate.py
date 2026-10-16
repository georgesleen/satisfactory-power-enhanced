#!/usr/bin/env python3
"""Generate the EP-C4 fast-buffer capacitor rack and its charge-state previews."""
import math
from pathlib import Path
import sys

import bpy

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'common'))
import epkit

VIEWS = {
    'hero': ((7, -9, 6.1), (0, 0, 1.55)),
    'service': ((-5.5, 9.8, 5.8), (0, 0, 1.55)),
    'orthographic': ((6, -8, 5.3), (0, 0, 1.65)),
}
MODULE_POSITIONS = (-1.35, -0.58, 0.19, 0.96)
CAN_ROWS = (-0.35, 0.55)
LIGHT_SEGMENTS = 5
FRAMES_PER_SECOND = 12
LAST_FRAME = 60
CHARGE_COLOR = (0.12, 0.72, 0.79, 1)
DARK_COLOR = (0.018, 0.035, 0.042, 1)
AMBER_COLOR = (1.0, 0.32, 0.015, 1)
COPPER_COLOR = (0.49, 0.27, 0.12, 1)
BUS_FLASH_COLOR = (1.0, 0.68, 0.25, 1)
arguments = epkit.parse_arguments(VIEWS, __doc__)
kit = epkit.Kit('EPC4_CapacitorBank')
palette = epkit.standard_palette()
box, cylinder, pipe, text, torus = kit.box, kit.cylinder, kit.pipe, kit.text, kit.torus
orange, graphite, tank, steel = palette.orange, palette.graphite, palette.tank, palette.steel
ceramic, copper, rubber, yellow = palette.ceramic, palette.copper, palette.rubber, palette.yellow
white, cyan = palette.white, palette.cyan
bus_surface = epkit.material('Bus | pulse copper', COPPER_COLOR[:3], 0.8, 0.25)
status_surface = epkit.material('Status | buffer state', (0.25, 0.8, 0.35), 0.1, 0.25, 2)


def bolt(location, direction=(0, -1, 0)):
    """Add a captive hex fastener."""
    return cylinder('Captive hex fastener', location, 0.03, 0.025, steel, 6, direction)


# The skid carries four removable twin-can cassettes.
for x in (-1.52, 1.52):
    box('Longitudinal skid beam', (x, 0, 0.24), (0.3, 3.55, 0.38), graphite, 0.055)
for y in (-1.55, 1.55):
    box('Skid crossmember', (0, y, 0.31), (3.6, 0.28, 0.28), graphite, 0.04)
    for x in (-1.6, 1.6):
        box('Anchor shoe', (x, y, 0.095), (0.58, 0.58, 0.19), graphite, 0.04)
        for offset in (-0.16, 0.16):
            cylinder('Foundation anchor', (x + offset, y, 0.203), 0.048, 0.035, steel, 6)
box('Rack deck', (0, 0, 0.49), (3.55, 3.25, 0.14), steel, 0.05)
charge_lights = []
for module_index, x in enumerate(MODULE_POSITIONS):
    module_name = f'Module_{module_index + 1:02d}'
    box(module_name + '_Cradle', (x, 0.1, 0.68), (0.69, 1.88, 0.24), graphite, 0.04)
    for y in (-0.86, 1.05):
        box(module_name + '_FoldedPost', (x, y, 1.42), (0.23, 0.14, 1.56), orange, 0.035)
        for z in (0.78, 1.99):
            bolt((x, y + math.copysign(0.084, y), z), (0, y, 0))
    for can_index, y in enumerate(CAN_ROWS):
        prefix = module_name + f'_Can_{can_index + 1}'
        cylinder(prefix + '_FootSeal', (x, y, 0.83), 0.3, 0.09, rubber, 48)
        cylinder(prefix + '_CapacitorCan', (x, y, 1.51), 0.3, 1.29, tank, 48)
        cylinder(prefix + '_RolledBase', (x, y, 0.91), 0.315, 0.07, steel, 48)
        cylinder(prefix + '_RolledLid', (x, y, 2.16), 0.315, 0.09, steel, 48)
        cylinder(prefix + '_LidSeal', (x, y, 2.215), 0.22, 0.025, rubber)
        for z in (1.07, 1.94):
            cylinder(prefix + '_ClampBand', (x, y, z), 0.316, 0.1, orange, 48)
            box(prefix + '_ClampLatch', (x, y - 0.319, z), (0.17, 0.08, 0.14), steel, 0.015)
            bolt((x, y - 0.37, z))
        cylinder(prefix + '_PorcelainBushing', (x, y, 2.35), 0.075, 0.24, ceramic)
        for z in (2.29, 2.38):
            cylinder(prefix + '_PorcelainShed', (x, y, z), 0.12, 0.045, ceramic)
        cylinder(prefix + '_TerminalNut', (x, y, 2.5), 0.08, 0.09, bus_surface, 6)
        box(prefix + '_CaseBond', (x + 0.23, y, 2.23), (0.08, 0.1, 0.08), copper, 0.008)
    box(module_name + '_ChargeBezel', (x, -0.965, 1.52), (0.31, 0.09, 0.98), graphite, 0.025)
    for segment in range(LIGHT_SEGMENTS):
        surface = epkit.material(module_name + f'_ChargeSegment_{segment + 1}', CHARGE_COLOR[:3], 0.15, 0.3, 2)
        box(module_name + f'_Light_{segment + 1}', (x, -1.02, 1.17 + segment * 0.165), (0.19, 0.025, 0.1), surface, 0.012)
        charge_lights.append((module_index, segment, surface))
    text(module_name + '_Number', f'C{module_index + 1}', (x - 0.085, -1.012, 1.905), 0.12, white)
    pipe(module_name + '_SenseConduit', [(x, -0.85, 1.1), (x, -1.1, 0.78), (x, -1.15, 0.65)], 0.022, rubber)
    box(module_name + '_RearBondBar', (x, 0.1, 2.26), (0.08, 1.18, 0.035), copper, 0.006)

# Copper bus bars join the capacitor bushings to the LV converter.
for y in CAN_ROWS:
    box('Pulse bus bar', (0, y, 2.53), (3.32, 0.12, 0.075), bus_surface, 0.015)
    for x in MODULE_POSITIONS:
        cylinder('Bus terminal washer', (x, y, 2.58), 0.08, 0.035, steel, 6)
box('Bus cross link', (1.62, 0.1, 2.53), (0.12, 1.03, 0.075), bus_surface, 0.015)
for x in (-1.68, 1.62):
    box('Bus support foot', (x, 0.1, 2.0), (0.16, 1.4, 0.12), orange, 0.025)
    for y in CAN_ROWS:
        cylinder('Bus standoff', (x, y, 2.275), 0.1, 0.43, ceramic)
        for z in (2.13, 2.29):
            cylinder('Bus standoff shed', (x, y, z), 0.14, 0.045, ceramic)
    for y in (-0.66, 0.88):
        box('Bus support upright', (x, y, 1.255), (0.12, 0.12, 1.39), graphite, 0.018)

# A rear converter carries the single LV cable terminal and its service controls.
box('Converter cabinet gasket', (0, 1.34, 1.26), (3.25, 0.44, 1.32), rubber, 0.06)
box('Orange converter housing', (0, 1.4, 1.28), (3.17, 0.39, 1.28), orange, 0.055)
box('Converter service door', (0, 1.615, 1.26), (2.93, 0.055, 1.06), graphite, 0.04)
text('Rear service label', 'LV CONVERTER / ISOLATE BEFORE SERVICE', (1.28, 1.652, 1.65), 0.075, white, '+Y')
for x in (-1.37, 1.37):
    for z in (0.85, 1.61):
        bolt((x, 1.66, z), (0, 1, 0))
for index in range(16):
    box('Converter rear louver', (-1.22 + index * 0.16, 1.655, 1.23), (0.055, 0.035, 0.4), tank, 0.008)
for x in (-0.8, 0.8):
    pipe('Rear conduit', [(x, 1.2, 0.75), (x, 1.54, 0.65), (x, 1.5, 0.56)], 0.035, rubber)
terminal_x, terminal_y = 1.12, 1.3
cylinder('LV terminal flange', (terminal_x, terminal_y, 1.98), 0.25, 0.12, steel)
cylinder('LV orange turret', (terminal_x, terminal_y, 2.12), 0.18, 0.2, orange)
cylinder('LV porcelain core', (terminal_x, terminal_y, 2.42), 0.085, 0.45, ceramic)
for z in (2.28, 2.4, 2.52):
    cylinder('LV porcelain shed', (terminal_x, terminal_y, z), 0.155, 0.05, ceramic)
cylinder('LV contact crown', (terminal_x, terminal_y, 2.68), 0.09, 0.16, copper)
torus('LV attachment eye', (terminal_x, terminal_y, 2.83), 0.105, 0.032, steel, (math.pi / 2, 0, 0))
kit.socket('CableSocket_LV', (terminal_x, terminal_y, 2.83))
pipe('LV bus riser', [(1.62, 0.55, 2.53), (1.62, 1.3, 2.53), (1.12, 1.3, 2.67)], 0.045, bus_surface)
text('Terminal voltage label', 'LV', (terminal_x - 0.08, terminal_y - 0.19, 2.06), 0.11, white)

# A vented resistor unit provides a separate service bleed assembly.
box('Bleed resistor pan', (-0.55, 1.34, 1.985), (1.66, 0.49, 0.13), steel, 0.025)
for index in range(14):
    box('Bleed resistor fin', (-1.27 + index * 0.11, 1.34, 2.22), (0.045, 0.37, 0.36), graphite, 0.008)
for x in (-1.4, 0.28):
    box('Bleed orange end guard', (x, 1.34, 2.23), (0.1, 0.58, 0.48), orange, 0.025)
box('Bleed perforated guard rail', (-0.56, 1.34, 2.47), (1.74, 0.59, 0.07), orange, 0.018)
box('Bleed rear label plate', (-0.56, 1.6, 2.2), (1.58, 0.05, 0.16), graphite, 0.012)
text('Bleed service label', 'SERVICE BLEED', (0.16, 1.629, 2.165), 0.075, white, '+Y')
pipe('Bleed lead', [(-1.4, 0.55, 2.53), (-1.48, 0.95, 2.47), (-1.43, 1.34, 2.22)], 0.028, rubber)

# The front service bridge holds the state display and guarded contactor.
box('Front service bridge', (0, -1.28, 0.93), (3.23, 0.3, 0.54), orange, 0.045)
box('Control faceplate', (0, -1.45, 0.95), (1.71, 0.055, 0.42), graphite, 0.025)
box('Readout bezel', (-0.3, -1.49, 0.98), (0.93, 0.04, 0.25), steel, 0.02)
box('Readout glass', (-0.3, -1.515, 0.98), (0.84, 0.018, 0.18), rubber, 0.012)
readout_location = (-0.67, -1.533, 0.95)
readout = text('Display_IdleFull', 'READY 100%', readout_location, 0.085, cyan)
cylinder('Buffer state lamp', (0.36, -1.49, 0.98), 0.045, 0.035, status_surface, 24, (0, 1, 0))
text('Buffer class label', 'EP-C4', (-1.52, -1.433, 1.0), 0.12, rubber)
text('Buffer role label', 'FAST BUFFER', (-1.52, -1.433, 0.86), 0.065, rubber)
text('Energy units label', 'MW / MWh', (0.22, -1.481, 0.8), 0.07, white)
box('Discharge contactor backplate', (1.15, -1.46, 0.98), (0.52, 0.055, 0.25), graphite, 0.022)
for x in (1.01, 1.3):
    cylinder('Contactor ceramic mount', (x, -1.51, 0.98), 0.047, 0.08, ceramic, 24, (0, 1, 0))
contactor = kit.empty('Discharge_Contactor', (1.01, -1.57, 0.98))
arm = box('Discharge contactor arm', (0, 0, 0), (0.29, 0.045, 0.045), bus_surface, 0.009)
arm.parent = contactor
arm.location = (0.145, 0, 0)
for z in (0.8, 1.17):
    pipe('Contactor finger guard', [(0.88, -1.48, z), (0.88, -1.65, z), (1.45, -1.65, z), (1.45, -1.48, z)], 0.018, steel)
box('Access tread', (0, -1.68, 0.57), (3.26, 0.46, 0.1), graphite, 0.025)
box('Warning threshold', (0, -1.917, 0.59), (3.16, 0.022, 0.12), yellow, 0.004)
for index in range(16):
    stripe = box('Threshold black slash', (-1.49 + index * 0.198, -1.932, 0.59), (0.085, 0.012, 0.122), rubber, 0.001)
    stripe.rotation_euler.y = -0.35
for index in range(19):
    box('Tread traction rib', (-1.47 + index * 0.163, -1.67, 0.63), (0.027, 0.29, 0.02), steel, 0.004)

kit.configure_render(arguments.samples, arguments.width)
kit.build_studio(steel)
if arguments.animate or arguments.render_animation:
    kit.set_timeline(FRAMES_PER_SECOND, LAST_FRAME, [('IDLE_FULL', 1), ('DISCHARGE_PULSE', 13), ('EMPTY', 33), ('RECHARGE', 43)])
    for module_index, segment, surface in charge_lights:
        drop_frame = 14 + module_index * 4 + (LIGHT_SEGMENTS - 1 - segment)
        refill_frame = 43 + module_index * 4 + segment
        epkit.key_emission(surface, [
            (1, CHARGE_COLOR, 2), (drop_frame - 1, CHARGE_COLOR, 2),
            (drop_frame, DARK_COLOR, 0), (refill_frame - 1, DARK_COLOR, 0),
            (refill_frame, CHARGE_COLOR, 2), (LAST_FRAME, CHARGE_COLOR, 2),
        ], surface.name + '_ChargeDischarge')
    flash_keys = [(1, COPPER_COLOR, 0), (12, COPPER_COLOR, 0)]
    for frame in (14, 18, 22, 26):
        flash_keys.extend([(frame - 1, COPPER_COLOR, 0), (frame, BUS_FLASH_COLOR, 4), (frame + 1, COPPER_COLOR, 0)])
    flash_keys.append((LAST_FRAME, COPPER_COLOR, 0))
    epkit.key_emission(bus_surface, flash_keys, 'Bus_DischargePulse')
    epkit.key_emission(status_surface, [
        (1, (0.25, 0.8, 0.35, 1), 2), (12, (0.25, 0.8, 0.35, 1), 2),
        (13, CHARGE_COLOR, 3), (32, CHARGE_COLOR, 3),
        (33, AMBER_COLOR, 2), (42, AMBER_COLOR, 2),
        (43, CHARGE_COLOR, 2), (59, CHARGE_COLOR, 2),
        (60, (0.25, 0.8, 0.35, 1), 2),
    ], 'Status_FullPulseEmptyRecharge')
    epkit.key_rotation(contactor, 1, [(1, -0.65), (12, -0.65), (14, 0), (30, 0), (33, -0.65), (42, -0.65), (44, 0), (58, 0), (60, -0.65)], 'Contactor_PulseRecharge')
    display_states = [
        (readout, 1, 12),
        (text('Display_Discharge', 'PEAK ASSIST', readout_location, 0.085, cyan), 13, 32),
        (text('Display_Empty', 'EMPTY', readout_location, 0.085, white), 33, 42),
        (text('Display_Recharge', 'CHARGING', readout_location, 0.085, cyan), 43, 59),
        (text('Display_Full', 'READY 100%', readout_location, 0.085, cyan), 60, 60),
    ]
    for obj, start, end in display_states:
        epkit.key_state_window(obj, start, end, (1, 12, 13, 32, 33, 42, 43, 59, 60), obj.name + '_StateVisibility')
    kit.scene.frame_set(1)
kit.export_metrics(ROOT / 'metrics.json', arguments.samples)
kit.render_stills(ROOT / 'renders', VIEWS, arguments.views, ROOT / 'capacitor-bank.blend')
if arguments.render_animation:
    kit.render_animation(ROOT / 'renders' / 'animation', VIEWS['hero'], arguments.animation_width, arguments.animation_samples)
print('ASSET_RENDER_COMPLETE', flush=True)
