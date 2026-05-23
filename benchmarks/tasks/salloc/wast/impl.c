#define MEMORY_POOL_SIZE (1024 * 1024) // 1 MB
#define NUM_ELEMENTS 100000           // Number of elements to process
#define ITERATIONS 1000               // Number of iterations for benchmarking

__attribute__((import_module("env"), import_name("print_int"))) void print_int(int);

// Static memory pool to simulate linear memory
static char memory_pool[MEMORY_POOL_SIZE];

// Simulated memory allocation
static int current_offset = 0;

void *my_malloc(int size) {
    if (current_offset + size > MEMORY_POOL_SIZE) return 0;
    void *allocated_memory = &memory_pool[current_offset];
    current_offset += size;
    return allocated_memory;
}


//int bench(void) {
//  int i, j;
//  int total = 0;
//  int iterations = 10;  // Number of times to allocate BUFFER_LENGTH elements

// Benchmark function
void bench() {
    // Allocate two large arrays
    int *array1 = (int *)my_malloc(NUM_ELEMENTS * sizeof(int));
    int *array2 = (int *)my_malloc(NUM_ELEMENTS * sizeof(int));


    if (!array1 || !array2) {
        print_int(-1); // Indicate memory allocation failure
        return;
    }

    // Initialize arrays
    for (int i = 0; i < NUM_ELEMENTS; i++) {
        array1[i] = i;          // Store operation
        array2[i] = NUM_ELEMENTS - i; // Store operation
    }

    // Perform load and store operations repeatedly
    for (int iter = 0; iter < ITERATIONS; iter++) {
        for (int i = 0; i < NUM_ELEMENTS; i++) {
            array1[i] += array2[i]; // Load and store
        }
    }

    // Compute and output the sum of array1
    int sum = 0;
    for (int i = 0; i < NUM_ELEMENTS; i++) {
        sum += array1[i]; // Load operation
    }

    print_int(sum); // Print the result
}
  
