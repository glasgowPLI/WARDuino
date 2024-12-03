#define NULL (void *)0
#define BUFFER_LENGTH 100
#define ITERATIONS 1000  // Number of iterations per benchmark run
#define ALLOCATIONS_PER_ITERATION 100  // Number of allocations per iteration
#define NUM_BENCHMARK_RUNS 1  // Total number of benchmark runs

// Pre-allocated buffer for custom memory allocation
int salloc_buffer[BUFFER_LENGTH * ALLOCATIONS_PER_ITERATION];
int salloc_index = 0;  // Keep track of the next available slot

// Custom salloc function to simulate dynamic memory allocation
int* salloc() {
    if (salloc_index < BUFFER_LENGTH * ALLOCATIONS_PER_ITERATION) {
        return &salloc_buffer[salloc_index++];
    } else {
        return NULL;  // No space left
    }
}

__attribute__((import_module("env"), import_name("print_int"))) void print_int(int);

// Bench function to run the benchmark
int bench() {
    int *buffer[ALLOCATIONS_PER_ITERATION];  // Array to hold pointers
    int i, j;
    int total = 0;

    // Loop for benchmark run
    for (int k = 0; k < NUM_BENCHMARK_RUNS; k++) {
        // Iterate for a number of times for allocations
        for (j = 0; j < ITERATIONS; j++) {
            // Allocate memory for each slot using salloc
            for (i = 0; i < ALLOCATIONS_PER_ITERATION; i++) {
                buffer[i] = salloc();  // Replace malloc with salloc

                if (buffer[i] == NULL) {
                    print_int(-1);  // Indicate memory allocation failure
                    return -1;  // Exit early if allocation fails
                }

                *buffer[i] = i;  // Assign a value to the allocated memory
            }

            // Perform simple operation on the allocated memory (sum)
            for (i = 0; i < ALLOCATIONS_PER_ITERATION; i++) {
                total += *buffer[i];
            }
        }
    }

    print_int(total);  // Print the result after benchmark is complete
    return total;  // Return the total sum after all allocations
}
