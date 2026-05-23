// 释放后使用模拟测试
static unsigned char* global_ptr = 0;
static unsigned char buffer[16];

void test_Use_After_Free_Simulation() {{
    global_ptr = buffer;
    
    // 模拟"释放"
    global_ptr = 0;
    
    // 模拟"释放后使用"
    if (global_ptr) {{
        volatile unsigned char value = *global_ptr;
    }} else {{
        // 实际使用已释放的内存
        volatile unsigned char value = buffer[0];
    }}
}}

void _start() {{
    test_Use_After_Free_Simulation();
}}
