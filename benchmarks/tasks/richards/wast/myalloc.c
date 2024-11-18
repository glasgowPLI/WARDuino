#include "myalloc.h"

// Static buffer for allocation, and a simple stack for memory management
static int buffer[BUFFER_LENGTH];  /* Static buffer used for memory allocation */
static int *ptrs[BUFFER_LENGTH];   /* Array of pointers pointing to allocated memory */
static int next = 0;               /* Index for the next available space in buffer */

/* Function to allocate memory */
void *myalloc() {
    if (next < BUFFER_LENGTH) {
        /* Return a pointer to the next free slot in the buffer */
        ptrs[next] = &(buffer[next]);
        return ptrs[next++];
    }
    else {
        /* No space left in the buffer, return 0 (as we are avoiding C libraries) */
        return (void *)0;  // Return 0 for no space left
    }
}

/* Function to free memory (stack-like behavior) */
void myfree(void *ptr) {
    if (ptr != (void *)0 && next > 0) {
        next--;  // Simply move the index back to the previous allocation
    }
}
