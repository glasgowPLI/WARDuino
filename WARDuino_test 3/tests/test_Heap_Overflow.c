
// 安全测试: Heap_Overflow
// 生成时间: 2025-09-23T12:25:21.067973

// 简单的输出函数替代品
void print_str(const char* str) {
    // 在WASM环境中，这可能会被替换为适当的导入
}

// 测试函数声明
void test_Heap_Overflow();

int main() {
    print_str("TEST_START:Heap_Overflow");
    test_Heap_Overflow();
    print_str("TEST_END:Heap_Overflow");
    return 0;
}

// 测试函数实现

#include <stdlib.h>

void test_Heap_Overflow() {
    // 堆溢出测试
    char *ptr = (char*)malloc(10);
    if (ptr) {
        ptr[15] = 'A';
        free(ptr);
    }
}

