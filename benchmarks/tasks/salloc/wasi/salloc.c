#define NULL (void *)0
#define BUFFER_LENGTH 100
// #ifdef __CHERI_PURE_CAPABILITY__
__attribute__((import_module("env"), import_name("print_int"))) void print_int(int);
// #endif

int buffer[BUFFER_LENGTH];  /* this is the large array we will split up */
int *ptrs[BUFFER_LENGTH];   /* this is an array of pointers into buffer */

int *allocate() {
  static int next = 0;
  if (next < BUFFER_LENGTH) {
    /* return a pointer to the next free slot in buffer */
    return &(buffer[next++]);
  }
  else {
    /* no space left in buffer, return NULL */
    return NULL;
  }
}

int bench(void) {
  int i;
  int iter_total = BUFFER_LENGTH;
  int total = 0;

  for (i = 0; i<iter_total; i++) {
    int *p = allocate();
    if (p) {
      *p = i;
      ptrs[i] = p;
    }
  }
  for (i=0; i<iter_total; i++) {
    // printf("%d %d %d\n", i, *ptrs[i], total);
    total += *ptrs[i];
  }
  // #ifdef __CHERI_PURE_CAPABILITY__
  print_int(total);
  // #endif
  return total;
}
