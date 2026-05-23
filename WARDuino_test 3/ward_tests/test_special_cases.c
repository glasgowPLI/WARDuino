// 特殊内存情况测试
void _start() {
    // 测试1: 零长度数组访问
    char empty[0];
    empty[0] = 1;  // 零长度数组访问
    
    // 测试2: 单字节缓冲区
    char single[1];
    single[0] = 'A';  // 正常
    single[1] = 'B';  // 溢出
    
    // 测试3: 大数组边界
    char large[1000];
    large[0] = 'S';    // 正常
    large[999] = 'E';  // 正常（边界）
    large[1000] = 'X'; // 溢出
    
    // 测试4: 负索引
    int data[5];
    int index = -1;
    data[index] = 123;  // 负索引访问
    
    // 测试5: 极大索引
    data[1000000] = 456;  // 极大索引
}
