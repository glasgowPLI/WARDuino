# Define directories
# TASKS_DIR := catalan fac fib gcd primes tak tak-mem
TASKS_DIR := salloc
WASM_TARGET := --target=wasm32
CFLAGS := -Oz -flto -nostdlib
LDFLAGS := -Wl,--export-all -Wl,--no-entry -Wl,--strip-all -Wl,--lto-O3

# Default OUTPUT_DIR
OUTPUT_DIR := wasm-cheri

CLANG := ~/wasi-sdk-dlmalloc/build/wasi-sdk-20.11gf3b43c703f1a+m/bin/clang

# Ensure the output directory exists
$(OUTPUT_DIR):
	mkdir -p $(OUTPUT_DIR)

# Compile rule for each task, looking in wast subdirectories
$(OUTPUT_DIR)/%.wasm: %/wast/impl.c | $(OUTPUT_DIR)
	@echo "$(CLANG) $(WASM_TARGET) $(CFLAGS) $(LDFLAGS) $< -o $@"
	$(CLANG) $(WASM_TARGET) $(CFLAGS) $(LDFLAGS) $< -o $@

# Build all wasm files
all: $(addprefix $(OUTPUT_DIR)/, $(addsuffix .wasm, $(TASKS_DIR)))

# Clean the output directory
clean:
	rm -f $(OUTPUT_DIR)/*.wasm
