// 空指针解引用测试
void test_Null_Pointer_Dereference() {{
    volatile unsigned char* ptr = 0;
    volatile unsigned char value;
    
    value = *ptr; // 解引用空指针
}}

void _start() {{
    test_Null_Pointer_Dereference();
}}
