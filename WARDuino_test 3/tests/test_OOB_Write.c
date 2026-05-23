// 内存越界写入测试
#define BUF_SIZE 8

void test_OOB_Write() {{
    unsigned char buffer[BUF_SIZE];
    
    // 正常写入
    for (int i = 0; i < BUF_SIZE; i++) {{
        buffer[i] = i;
    }}
    
    // 越界写入
    for (int i = BUF_SIZE; i < BUF_SIZE + 4; i++) {{
        buffer[i] = 0xFF; // 越界写入
    }}
}}

void _start() {{
    test_OOB_Write();
}}
