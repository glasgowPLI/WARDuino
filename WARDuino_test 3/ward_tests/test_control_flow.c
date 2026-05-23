// 控制流相关的内存测试
void _start() {
    int condition = 1;
    char buffer[10];
    
    // 测试1: 条件分支中的内存访问
    if (condition) {
        buffer[15] = 1;  // 条件性溢出
    } else {
        buffer[-1] = 2;  // 条件性下溢
    }
    
    // 测试2: 循环中的内存访问
    for (int i = 0; i < 20; i++) {
        buffer[i] = i;  // 循环中溢出
    }
    
    // 测试3: 嵌套作用域
    {
        char inner[5];
        inner[10] = 5;  // 内层作用域溢出
    }
    
    // 测试4: switch语句
    switch (condition) {
        case 1:
            buffer[20] = 10;  // case中的溢出
            break;
        default:
            buffer[-5] = 20;  // default中的下溢
    }
}
