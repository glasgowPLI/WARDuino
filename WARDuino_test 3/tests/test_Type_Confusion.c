// 类型混淆测试
void test_Type_Confusion() {{
    float f = 3.14f;
    int* int_ptr = (int*)&f; // 类型混淆
    volatile int value = *int_ptr;
}}

void _start() {{
    test_Type_Confusion();
}}
