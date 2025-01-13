# Define directories
TASKS_DIR := salloc
WASM_TARGET := --target=wasm32
CFLAGS := -Oz -flto -nostdlib
LDFLAGS := -Wl,--export-all -Wl,--no-entry -Wl,--strip-all -Wl,--lto-O3

# Determine system type and set OUTPUT_DIR
CLANG := ~/wasi-sdk-24.0-x86_64-linux/bin/clang

# Ensure the output directory exists
$(OUTPUT_DIR):
	mkdir -p $(OUTPUT_DIR)

# Compile rule for each task, looking in wast subdirectories and other source files
$(OUTPUT_DIR)/%.wasm: %/wast/impl.c ~/WARDuino/src/Primitives/emulated.cpp | $(OUTPUT_DIR)
	
	$(CLANG) $(WASM_TARGET) $(CFLAGS) $(LDFLAGS) $< ~/WARDuino/src/Primitives/emulated.cpp -o $@
	
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
