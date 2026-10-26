# Invoked from the repository root by make ui.
UI_DIR ?= build/ui
UI_OBJECT_DIR ?= build/ui-wasm
EMXX ?= em++
PYTHON ?= python3
TUNING ?= tools/balance/tuning.json
UI_CORE := Source/EnhancedPowerCore
UI_PRIMITIVES := Thermal FastBuffer TransformerLink Loss
UI_OBJECTS := $(addprefix $(UI_OBJECT_DIR)/,$(addsuffix .o,$(UI_PRIMITIVES))) $(UI_OBJECT_DIR)/bridge.o
UI_HEADERS := $(wildcard $(UI_CORE)/Public/EnhancedPowerCore/*.h)
UI_FLAGS := -std=c++20 -O2 -Wall -Wextra -Werror -fno-exceptions -I$(UI_CORE)/Public -I$(UI_OBJECT_DIR)

.PHONY: all
all: $(UI_DIR)/wasm/core.js $(UI_DIR)/wasm/core.wasm

$(UI_OBJECT_DIR)/tuning.h: FORCE
	$(PYTHON) -B assets/ui/wasm/generate_tuning.py $(TUNING) $@

.PHONY: FORCE
FORCE:

$(UI_OBJECT_DIR)/%.o: $(UI_CORE)/Private/%.cpp $(UI_HEADERS)
	mkdir -p $(UI_OBJECT_DIR)
	$(EMXX) $(UI_FLAGS) -MMD -MP -c $< -o $@

$(UI_OBJECT_DIR)/bridge.o: assets/ui/wasm/bridge.cpp $(UI_OBJECT_DIR)/tuning.h $(UI_HEADERS)
	$(EMXX) $(UI_FLAGS) -MMD -MP -c $< -o $@

$(UI_DIR)/wasm/core.js $(UI_DIR)/wasm/core.wasm &: $(UI_OBJECTS)
	mkdir -p $(UI_DIR)/wasm
	$(EMXX) $(UI_FLAGS) $(UI_OBJECTS) --no-entry -sMODULARIZE=1 -sEXPORT_NAME=EnhancedPowerCore \
	  -sENVIRONMENT=web,node -sALLOW_MEMORY_GROWTH=0 -sFILESYSTEM=0 \
	  -sEXPORTED_FUNCTIONS='["_ui_reset","_ui_step","_ui_snapshot","_ui_set_connected","_ui_set_buffer_connected","_ui_reset_breaker"]' \
	  -sEXPORTED_RUNTIME_METHODS='["cwrap"]' -o $(UI_DIR)/wasm/core.js

-include $(UI_OBJECTS:.o=.d)
