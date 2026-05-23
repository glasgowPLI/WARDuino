// 内存对齐错误测试
void test_Memory_Alignment() {{
    unsigned char data[10];
    volatile unsigned int* int_ptr;
    
    // 未对齐的指针访问
    int_ptr = (unsigned int*)(data + 1);
    *int_ptr = 0x12345678;
}}

void _start() {{
    test_Memory_Alignment();
}}
