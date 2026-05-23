// 内存越界读取测试
#define BUF_SIZE 8

void _start() {
    unsigned char buffer[BUF_SIZE];
    
    // 初始化
    for (int i = 0; i < BUF_SIZE; i++) {
        buffer[i] = i;
    }
    
    // 越界读取
    volatile unsigned char value;
    for (int i = BUF_SIZE; i < BUF_SIZE + 3; i++) {
        value = buffer[i]; // 越界读取
    }
}
