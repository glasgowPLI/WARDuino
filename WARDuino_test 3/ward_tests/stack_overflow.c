// 栈溢出测试（深度递归）
void recursive_function(int depth) {
    unsigned char stack_buffer[256]; // 每个调用分配大缓冲区
    if (depth > 0) {
        recursive_function(depth - 1);
    }
}

void _start() {
    // 深度递归导致栈溢出
    recursive_function(100);
}
