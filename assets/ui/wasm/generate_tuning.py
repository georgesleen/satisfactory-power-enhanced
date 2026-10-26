#!/usr/bin/env python3
"""Generate the browser adapter's constants from the balance input."""

import hashlib
import json
from pathlib import Path
import sys

source, destination = map(Path, sys.argv[1:])
payload = source.read_bytes()
tuning = json.loads(payload)
tiers = {tier["name"]: tier for tier in tuning["tiers"]}
transformers = {item["name"]: item for item in tuning["transformers"]}
values = {
    "Rating": transformers["district"]["ratingMegawatts"],
    "TierCapacity": tiers["LV"]["capacityMegawatts"],
    "ReferenceDistance": tiers["LV"]["referenceDistanceMeters"],
    "ReferenceLoss": tiers["LV"]["referenceLossFraction"],
    "TimeConstant": tuning["thermal"]["timeConstantSeconds"],
    "WarningHeat": tuning["thermal"]["warningHeat"],
    "TripHeat": tuning["thermal"]["tripHeat"],
    "BufferCapacity": tuning["capacitorBank"]["capacityMegajoules"],
    "MaxCharge": tuning["capacitorBank"]["maxChargeMegawatts"],
    "MaxDischarge": tuning["capacitorBank"]["maxDischargeMegawatts"],
    "ChargeEfficiency": tuning["capacitorBank"]["chargeEfficiency"],
    "Setpoint": tuning["capacitorBank"]["setpointFraction"],
    "Comfort": tuning["acceptance"]["comfortLoadFraction"],
    "StepSeconds": tuning["simulation"]["stepSeconds"],
}
provenance = {
    "source": str(source),
    "status": tuning["status"],
    "sha256": hashlib.sha256(payload).hexdigest(),
    "stepSeconds": values["StepSeconds"],
    "maxChargeMW": values["MaxCharge"],
    "maxDischargeMW": values["MaxDischarge"],
    "warningHeat": values["WarningHeat"],
    "tripHeat": values["TripHeat"],
    "timeConstantSeconds": values["TimeConstant"],
    "tierCapacitiesMW": {name: tier["capacityMegawatts"] for name, tier in tiers.items()},
    "tiers": tuning["tiers"],
    "transformers": tuning["transformers"],
    "capacitorBank": tuning["capacitorBank"],
    "acceptance": tuning["acceptance"],
    "simulation": tuning["simulation"],
    "transformer": "district",
    "lossTier": "LV",
    "distance": "LV reference distance",
    "linkEfficiency": 1,
    "escrow": "one tuning step at transformer rating",
    "coolingModel": None,
}
lines = ["#pragma once", "namespace UiTuning", "{"]
lines.extend(f"inline constexpr double {key} = {value!r};" for key, value in values.items())
lines.append('inline constexpr char Provenance[] = R"tuning(' + json.dumps(provenance, separators=(",", ":")) + ')tuning";')
lines.append("}")
text = "\n".join(lines) + "\n"
destination.parent.mkdir(parents=True, exist_ok=True)
if not destination.exists() or destination.read_text() != text:
    destination.write_text(text)
