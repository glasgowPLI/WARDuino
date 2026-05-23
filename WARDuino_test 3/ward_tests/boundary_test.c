void _start() {
    char buf[10];
    // 边界情况测试
    buf[9] = 'A';   // 边界内 - 应该允许
    buf[10] = 'B';  // 边界上 - 应该检测
}
