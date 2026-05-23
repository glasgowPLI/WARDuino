// 整数溢出测试
void test_Integer_Overflow() {{
    int max_int = 2147483647;
    volatile int result = max_int + 1; // 整数溢出
}}

void _start() {{
    test_Integer_Overflow();
}}
