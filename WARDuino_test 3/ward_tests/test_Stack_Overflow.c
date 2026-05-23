// 栈溢出测试
void recursive_function(int depth) {{
    unsigned char stack_buffer[256];
    if (depth > 0) {{
        recursive_function(depth - 1);
    }}
}}

void test_Stack_Overflow() {{
    recursive_function(100);
}}

void _start() {{
    test_Stack_Overflow();
}}
