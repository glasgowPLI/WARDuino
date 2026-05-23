// 动态内存模式测试（使用静态数组模拟堆）
#define HEAP_SIZE 1024
static unsigned char heap[HEAP_SIZE];
static unsigned int heap_ptr = 0;

void* my_malloc(int size) {
    if (heap_ptr + size > HEAP_SIZE) return 0;
    void* ptr = &heap[heap_ptr];
    heap_ptr += size;
    return ptr;
}

void _start() {
    // 测试1: 正常分配和使用
    char* buf1 = my_malloc(32);
    for (int i = 0; i < 32; i++) {
        buf1[i] = i;
    }
    
    // 测试2: 堆溢出
    char* buf2 = my_malloc(16);
    for (int i = 0; i < 32; i++) {  // 故意溢出
        buf2[i] = 0xAA;
    }
    
    // 测试3: 使用已分配但未初始化的内存
    char* buf3 = my_malloc(64);
    char sum = 0;
    for (int i = 0; i < 64; i++) {
        sum += buf3[i];  // 读取未初始化内存
    }
    
    // 测试4: 分配过多内存（模拟内存耗尽）
    while (my_malloc(128) != 0) {
        // 持续分配直到失败
    }
}
