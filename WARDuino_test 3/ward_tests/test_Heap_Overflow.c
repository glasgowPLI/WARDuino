// 安全测试: Heap_Overflow
// 生成时间: 2025-09-23T12:25:21.067973

#include <stdint.h>

// 外部打印函数声明
extern void print_int(int val);
extern void print_string(const char* str, int len);

// 模拟堆分配 - 使用静态数组替代malloc
#define HEAP_SIZE 100
static char heap_memory[HEAP_SIZE];
static int heap_allocated = 0;

// 模拟malloc
char* simulated_malloc(int size) {
    if (!heap_allocated && size <= HEAP_SIZE) {
        heap_allocated = 1;
        return heap_memory;
    }
    return 0; // 分配失败
}

// 模拟free
void simulated_free(char* ptr) {
    if (ptr == heap_memory) {
        heap_allocated = 0;
    }
}

// 测试函数声明
void test_Heap_Overflow();

void _start() {
    print_string("TEST_START:Heap_Overflow", 23);
    test_Heap_Overflow();
    print_string("TEST_END:Heap_Overflow", 21);
}

// 测试函数实现
void test_Heap_Overflow() {
    // 堆溢出测试 - 使用模拟的堆分配
    char *ptr = simulated_malloc(10);
    if (ptr) {
        // 故意进行越界写入，模拟堆溢出
        ptr[15] = 'A'; // 写入超出分配大小的位置
        
        simulated_free(ptr);
    }
}
