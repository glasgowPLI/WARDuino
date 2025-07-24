#define NULL 0

/**************
 * Memory Allocator
 */
#define CELL_SIZE 64

typedef union {
  char bytes[CELL_SIZE];
  void *ptr;
} Cell;

#define POOL_SIZE_IN_PAGES 2000
#define PAGE_SIZE (1 << 12)

char mem[POOL_SIZE_IN_PAGES * PAGE_SIZE];

void *pool = NULL;
Cell *freelist = NULL;

void init_mem_pool() {
  void *p = &mem[0];
  unsigned int pool_size = POOL_SIZE_IN_PAGES * PAGE_SIZE;
  Cell *cell = (Cell *)p;
  while ((char *)cell < ((char *)p + pool_size - CELL_SIZE)) {
    cell->ptr = cell + 1;
    cell++;
  }
  cell->ptr = NULL;
  freelist = (Cell *)p;
  pool = p;
}

void *my_malloc(unsigned int num_bytes) {
  if (freelist == NULL) return NULL;
  void *p = (void *)freelist;
  freelist = freelist->ptr;
  return p;
}

void my_free(void *ptr) {
  Cell *empty = (Cell *)ptr;
  empty->ptr = freelist;
  freelist = empty;
}

/**************
 * Integer-Based N-Body
 */
#define NUM_BODIES 3
#define STEPS 1000

typedef struct {
  int x[3];  // position scaled by 1000
  int v[3];  // velocity
  int mass;
} Body;

void zero_velocity(Body *bodies[NUM_BODIES]) {
  for (int k = 0; k < 3; ++k)
    for (int i = 1; i < NUM_BODIES; ++i)
      bodies[0]->v[k] -= (bodies[i]->v[k] * bodies[i]->mass) / bodies[0]->mass;
}

void advance(Body *bodies[NUM_BODIES]) {
  for (int i = 0; i < NUM_BODIES; ++i) {
    for (int j = i + 1; j < NUM_BODIES; ++j) {
      int dx = bodies[i]->x[0] - bodies[j]->x[0];
      int dy = bodies[i]->x[1] - bodies[j]->x[1];
      int dz = bodies[i]->x[2] - bodies[j]->x[2];
      int dist = dx * dx + dy * dy + dz * dz + 1;

      int f = 1000 / dist;  // fake inverse-square law
      for (int k = 0; k < 3; ++k) {
        int dv = (bodies[j]->x[k] - bodies[i]->x[k]) * f;
        bodies[i]->v[k] += dv * bodies[j]->mass / 10000;
        bodies[j]->v[k] -= dv * bodies[i]->mass / 10000;
      }
    }
  }

  for (int i = 0; i < NUM_BODIES; ++i)
    for (int k = 0; k < 3; ++k)
      bodies[i]->x[k] += bodies[i]->v[k];
}

void print_state(Body *bodies[NUM_BODIES]) {
  for (int i = 0; i < NUM_BODIES; ++i) {
    print_string("Body "); print_int(i); print_string(": ");
    for (int k = 0; k < 3; ++k) {
      print_int(bodies[i]->x[k]); print_string(" ");
    }
    print_string("\n");
  }
}

/**************
 * Benchmark Entrypoint
 */
void start() {
  print_string("1\n");
  init_mem_pool();
  print_string("2\n");

  Body *bodies[NUM_BODIES];
  for (int i = 0; i < NUM_BODIES; ++i) {
    bodies[i] = (Body *)my_malloc(sizeof(Body));
  }

  // Simplified initial conditions (scaled by 1000)
  *bodies[0] = (Body){{0, 0, 0}, {0, 0, 0}, 10000};
  *bodies[1] = (Body){{1000, 0, 0}, {0, 2, 0}, 1};
  *bodies[2] = (Body){{-1000, 0, 0}, {0, -2, 0}, 1};

  zero_velocity(bodies);
  for (int i = 0; i < STEPS; ++i)
    advance(bodies);

  print_state(bodies);
}
