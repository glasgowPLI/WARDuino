// 除零错误测试
void test_Division_By_Zero() {{
    volatile int a = 10;
    volatile int b = 0;
    volatile int result = a / b; // 除零
}}

void _start() {{
    test_Division_By_Zero();
}}
