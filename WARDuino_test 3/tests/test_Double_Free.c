
// 安全测试: Double_Free
// 生成时间: 2025-09-23T12:25:25.130497

// 简单的输出函数替代品
void print_str(const char* str) {
    // 在WASM环境中，这可能会被替换为适当的导入
}

// 测试函数声明
void test_Double_Free();

int main() {
    print_str("TEST_START:Double_Free");
    test_Double_Free();
    print_str("TEST_END:Double_Free");
    return 0;
}

// 测试函数实现

#include <stdlib.h>

void test_Double_Free() {
    // 双重释放测试
    void *ptr = malloc(100);
    if (ptr) {
        free(ptr);
        free(ptr);
    }
}

