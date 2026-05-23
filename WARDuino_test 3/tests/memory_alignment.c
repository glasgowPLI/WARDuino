// 自定义内存操作函数（避免与内置函数冲突）
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

// WASM入口点
void _start() {
    // 初始化全局缓冲区
    my_memset(global_buffer, 0, BUF_SIZE);
    my_memset(another_global, 0, SMALL_BUF_SIZE);
    
    // 运行内存安全测试
    run_memory_safety_tests();
    
    // WASM不需要返回值
}

// 导出函数供外部调用
void __attribute__((export_name("run_tests"))) run_tests() {
    run_memory_safety_tests();
}

// 内存对齐错误测试
void _start() {
    unsigned char data[10];
    volatile unsigned int* int_ptr;
    
    // 未对齐的指针访问
    int_ptr = (unsigned int*)(data + 1);
    *int_ptr = 0x12345678;
}
