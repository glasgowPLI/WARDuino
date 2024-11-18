#ifndef MYALLOC_H
#define MYALLOC_H

#define BUFFER_LENGTH 100  // Define the size of the static buffer

// Function to allocate memory from a fixed-size buffer
void *myalloc();

// Function to free memory (simple stack-based free)
void myfree(void *ptr);

#endif  // MYALLOC_H
