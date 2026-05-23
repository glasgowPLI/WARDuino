// 基础内存访问测试
void _start() {
    // 测试1: 正常栈访问
    char stack_buf[16];
    for (int i = 0; i < 16; i++) {
        stack_buf[i] = i;
    }
    
    // 测试2: 栈缓冲区溢出
    stack_buf[20] = 0xFF;  // 溢出
    
    // 测试3: 栈下溢
    stack_buf[-1] = 0xAA;  // 下溢
}
