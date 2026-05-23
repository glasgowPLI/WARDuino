// 缓冲区下溢测试
void test_Buffer_Underflow() {{
    unsigned char buffer[8];
    volatile unsigned char* ptr = buffer;
    volatile unsigned char value = 0;
    
    // 正常访问
    for (int i = 0; i < 8; i++) {{
        ptr[i] = i;
    }}
    
    // 尝试下溢访问
    for (int i = -2; i < 0; i++) {{
        if (i >= 0 && i < 8) {{
            value = ptr[i];
        }} else {{
            value = ptr[i]; // 实际下溢访问
        }}
    }}
}}

void _start() {{
    test_Buffer_Underflow();
}}
