#pragma once

#include "Layout.h"

namespace EnhancedPower::Balance
{

/// Prints transformer heat, trip timing, and buffer energy accounting for a pulse study.
void PrintPulseStudy(const Factory& Factory, const PulseStudy& Study, const Tuning& Tuning);

} // namespace EnhancedPower::Balance
