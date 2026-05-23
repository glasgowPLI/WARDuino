// 内存越界写入测试
#define BUF_SIZE 8

void* my_memset(void* s, int c, unsigned int n) {
    unsigned char* p = (unsigned char*)s;
    for (unsigned int i = 0; i < n; i++) {
        p[i] = (unsigned char)c;
    }
    return s;
}

void _start() {
    unsigned char buffer[BUF_SIZE];
    
    // 正常写入
    my_memset(buffer, 0, BUF_SIZE);
    
    // 越界写入
    for (int i = BUF_SIZE; i < BUF_SIZE + 4; i++) {
        buffer[i] = 0xFF; // 越界写入
    }
}
