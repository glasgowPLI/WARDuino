# Define directories
TASKS_DIR := salloc
WASM_TARGET := --target=wasm32
CFLAGS := -Oz -flto -nostdlib
LDFLAGS := -Wl,--export-all -Wl,--no-entry -Wl,--strip-all -Wl,--lto-O3

# Determine system type and set OUTPUT_DIR
CLANG := ~/wasi-sdk-dlmalloc/build/wasi-sdk-20.11gf3b43c703f1a+m/bin/clang

# Ensure the output directory exists
$(OUTPUT_DIR):
	mkdir -p $(OUTPUT_DIR)

# Compile rule for each task, looking in wast subdirectories and other source files
$(OUTPUT_DIR)/%.wasm: %/wast/impl.c ~/WARDuino/src/Primitives/emulated.cpp ~/WARDuino/src/Primitives/arduino.cpp | $(OUTPUT_DIR)
	
	@echo "Running: $(CLANG) $(WASM_TARGET) $(CFLAGS) $(LDFLAGS) $< -o $@"
	
	$(CLANG) $(WASM_TARGET) $(CFLAGS) $(LDFLAGS) $< ~/WARDuino/src/Primitives/arduino.cpp ~/WARDuino/src/Primitives/emulated.cpp -o $@
	
	@if [ -f $@ ]; then \
		echo "Successfully built: $@"; \
	else \
		echo "Error: Failed to create output file: $@"; \
		exit 1; \
	fi

# Build all wasm files
all: $(addprefix $(OUTPUT_DIR)/, $(addsuffix .wasm, $(TASKS_DIR)))

# Clean the output directory
clean:
	rm -f $(OUTPUT_DIR)/*.wasm
