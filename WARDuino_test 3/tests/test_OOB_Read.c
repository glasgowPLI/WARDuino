// 内存越界读取测试
#define BUF_SIZE 8

void test_OOB_Read() {{
    unsigned char buffer[BUF_SIZE];
    
    // 初始化缓冲区
    for (int i = 0; i < BUF_SIZE; i++) {{
        buffer[i] = i + 1;
    }}
    
    // 越界读取
    volatile unsigned char value;
    for (int i = BUF_SIZE; i < BUF_SIZE + 3; i++) {{
        if (i < sizeof(buffer)) {{ // 安全检查，但条件永远不会为真，用于测试
            value = buffer[i];
        }} else {{
            value = buffer[i]; // 实际越界读取
        }}
    }}
}}

void _start() {{
    test_OOB_Read();
}}
