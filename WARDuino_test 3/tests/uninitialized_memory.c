// 未初始化内存使用测试
#define BUF_SIZE 16

void _start() {
    unsigned char buffer[BUF_SIZE];
    volatile unsigned char sum = 0;
    
    // 直接使用未初始化的内存
    for (int i = 0; i < BUF_SIZE; i++) {
        sum += buffer[i];
    }
}
