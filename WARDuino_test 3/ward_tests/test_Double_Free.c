// 安全测试: Double_Free
// 生成时间: 2025-09-23T12:25:25.130497

#include <stdint.h>

// 外部打印函数声明
extern void print_int(int val);
extern void print_string(const char* str, int len);

// 模拟堆分配
#define HEAP_SIZE 100
static char heap_memory[HEAP_SIZE];
static int heap_allocated = 0;

char* simulated_malloc(int size) {
    if (!heap_allocated && size <= HEAP_SIZE) {
        heap_allocated = 1;
        return heap_memory;
    }
    return 0;
}

void simulated_free(char* ptr) {
    if (ptr == heap_memory) {
        heap_allocated = 0;
    }
}

// 测试函数声明
void test_Double_Free();

void _start() {
    print_string("TEST_START:Double_Free", 22);
    test_Double_Free();
    print_string("TEST_END:Double_Free", 20);
}

// 测试函数实现
void test_Double_Free() {
    // 双重释放测试
    char *ptr = simulated_malloc(100);
    if (ptr) {
        simulated_free(ptr);
        simulated_free(ptr); // 双重释放 - 测试内存安全
    }
}
