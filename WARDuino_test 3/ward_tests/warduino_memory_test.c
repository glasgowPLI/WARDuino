// warduino_memory_test.c - 专门针对WARDuino的内存安全测试

// 完全避免任何标准库依赖

// 测试1: 简单的缓冲区溢出
int test1_simple_overflow() {
    char buf[8];
    
    // 正常访问
    buf[0] = 'A';
    buf[7] = 'B';
    
    // 溢出访问 - 应该被检测
    buf[8] = 'C';  // 刚好越界
    buf[15] = 'D'; // 明显越界
    
    return 1;
}

// 测试2: 未初始化内存读取
int test2_uninitialized_read() {
    int data[4];
    // 直接读取未初始化内存
    return data[0] + data[1] + data[2] + data[3];
}

// 测试3: 空指针访问
int test3_null_pointer() {
    int *ptr = 0;
    *ptr = 123;  // 应该导致立即错误
    return 1;
}

// 测试4: 栈下溢
int test4_stack_underflow() {
    char buf[8];
    buf[-1] = 'X';  // 栈下溢
    return 1;
}

// 测试5: 使用野指针
int test5_wild_pointer() {
    int *wild = (int*)0x12345678;
    *wild = 999;  // 野指针写入
    return 1;
}

// 测试6: 多级指针解引用
int test6_multiple_dereference() {
    int **ptr = 0;
    **ptr = 456;  // 多级空指针解引用
    return 1;
}

// 主测试运行器
int main() {
    int result = 0;
    
    // 每个测试都应该被WARDuino拦截
    // 如果测试返回，说明没有被正确拦截
    
    result |= test1_simple_overflow() << 0;
    // test3_null_pointer 可能不会返回
    result |= test4_stack_underflow() << 3;
    result |= test5_wild_pointer() << 4;
    // test6_multiple_dereference 可能不会返回
    
    // 如果程序能执行到这里，说明有些违规没有被检测到
    return result;
}

void _start() {
    main();
}
