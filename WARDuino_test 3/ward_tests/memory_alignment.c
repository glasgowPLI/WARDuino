#include <stdint.h>

// 定义缺失的常量
#define BUF_SIZE 64
#define SMALL_BUF_SIZE 16

// 定义缺失的全局变量
static unsigned char global_buffer[BUF_SIZE];
static unsigned char another_global[SMALL_BUF_SIZE];

// 自定义内存操作函数
void* my_memcpy(void* dest, const void* src, unsigned int n) {
    unsigned char* d = (unsigned char*)dest;
    const unsigned char* s = (const unsigned char*)src;
    
    for (unsigned int i = 0; i < n; i++) {
        d[i] = s[i];
    }
    return dest;
}

void* my_memset(void* s, int c, unsigned int n) {
    unsigned char* p = (unsigned char*)s;
    
    for (unsigned int i = 0; i < n; i++) {
        p[i] = (unsigned char)c;
    }
    return s;
}

int my_memcmp(const void* s1, const void* s2, unsigned int n) {
    const unsigned char* p1 = (const unsigned char*)s1;
    const unsigned char* p2 = (const unsigned char*)s2;
    
    for (unsigned int i = 0; i < n; i++) {
        if (p1[i] != p2[i]) {
            return (int)p1[i] - (int)p2[i];
        }
    }
    return 0;
}

// 简化的内存安全测试函数
void run_memory_safety_tests(void) {
    // 基础内存操作测试
    my_memset(global_buffer, 0xAA, BUF_SIZE);
    my_memset(another_global, 0xBB, SMALL_BUF_SIZE);
    
    // 内存复制测试
    unsigned char temp[SMALL_BUF_SIZE];
    my_memcpy(temp, another_global, SMALL_BUF_SIZE);
}

// 使用_start作为入口点
void _start() {
    unsigned char data[10];
    volatile unsigned int* int_ptr;
    
    // 运行基础测试
    run_memory_safety_tests();
    
    // 未对齐的指针访问 - 测试内存对齐错误
    int_ptr = (unsigned int*)(data + 1);  // 故意不对齐
    *int_ptr = 0x12345678;  // 可能的内存对齐错误
}
