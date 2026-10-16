"""Checks observed balance gates without repeating simulation core formulas."""

import subprocess
import sys
from pathlib import Path

root = Path(__file__).parent
report = subprocess.check_output([
    sys.argv[1], "--tuning", str(root / "tuning.json"), str(root / "scenarios")], text=True)
scenarios = {}
for line in report.splitlines():
    if line.startswith("SCENARIO "):
        scenario = line.split()[1]
        scenarios[scenario] = []
    elif line.startswith("  "):
        scenarios[scenario].append(line.strip())


def fields(line):
    return dict(word.split("=", 1) for word in line.split() if "=" in word)


def row(scenario, prefix):
    return fields(next(line for line in scenarios[scenario] if line.startswith(prefix)))


factories = [name for name, lines in scenarios.items() if any(line.startswith("LOAD ") for line in lines)]
assert factories, "report contains no factory comfort checks"
for name in factories:
    assert row(name, "LOAD ")["comfortable"] == "yes", name
    assert row(name, "LOCAL_CHECK ")["acceptable"] == "yes", name
    pole = row(name, "LOSS pole-branch proxy=LoadWeightedFeedDistance ")
    daisy = row(name, "LOSS daisy-chain proxy=LoadWeightedFeedDistance ")
    assert abs(float(pole["LVPercent"]) - float(daisy["LVPercent"])) < 0.2, name

outpost = "10-outpost.json"
local = row(outpost, "LOSS local proxy=LoadWeightedFeedDistance ")
remote = row(outpost, "LOSS remote-unsplit proxy=LoadWeightedFeedDistance ")
mv = row(outpost, "SPLIT tier=MV proxy=LoadWeightedFeedDistance ")
hv = row(outpost, "SPLIT tier=HV proxy=LoadWeightedFeedDistance ")
assert float(remote["LVPercent"]) > float(local["LVPercent"]) * 5
assert float(remote["LVPercent"]) > float(mv["totalLossPercent"]) > float(hv["totalLossPercent"])
plant = row("12-central-plant.json", "PLANT ")
assert float(plant["LVpeakPercent"]) > 100 > float(plant["MVpeakPercent"])
regional = row("13-regional-plant.json", "LOSS aggregate proxy=LoadWeightedFeedDistance ")
assert float(regional["LVPercent"]) > float(regional["MVPercent"]) * 5

pulses = {}
for line in scenarios["11-pulsed-district.json"]:
    if not line.startswith("PULSE "):
        continue
    pulse = fields(line)
    case = line.split()[1]
    if case == "synchronized":
        case += "-buffered" if int(pulse["banks"]) > 0 else "-unbuffered"
    assert case not in pulses, f"duplicate pulse case: {case}"
    pulses[case] = pulse

unbuffered = pulses["synchronized-unbuffered"]
assert unbuffered["warningSeconds"] != "none" and unbuffered["tripSeconds"] != "none"
assert float(unbuffered["warningSeconds"]) < float(unbuffered["tripSeconds"])
for case in (
    "synchronized-buffered", "staggered", "extra-headroom",
    "vanilla-storage-bank", "minimum-capacitor", "minimum-vanilla-storage",
):
    pulse = pulses[case]
    assert pulse["tripSeconds"] == "none" and float(pulse["unservedMJ"]) == 0, case
energy_tolerance_mj = 0.001
sustained = pulses["sustained-peak"]
assert abs(float(sustained["minimumMJ"])) <= energy_tolerance_mj
assert sustained["tripSeconds"] != "none"
assert pulses["vanilla-storage-one"]["tripSeconds"] != "none"
for pulse in pulses.values():
    assert abs(float(pulse["energyResidualMJ"])) <= energy_tolerance_mj, pulse
for case in ("minimum-capacitor", "minimum-vanilla-storage"):
    pulse = pulses[case]
    assert float(pulse["maximumFeedMW"]) <= float(pulse["ratingMW"]), pulse
    assert float(pulse["tailEnergyChangeMJ"]) >= -energy_tolerance_mj, pulse
assert int(pulses["minimum-capacitor"]["banks"]) < int(pulses["minimum-vanilla-storage"]["banks"])
print("Balance gates pass: factory comfort, distance, collection capacity, pulse trips, and buffer accounting.")
