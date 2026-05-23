// 内存访问错误测试
void test_Memory_Access() {{
    volatile int* ptr = (volatile int*)0x1000;
    volatile int value = *ptr; // 访问可能无效的内存地址
}}

void _start() {{
    test_Memory_Access();
}}
