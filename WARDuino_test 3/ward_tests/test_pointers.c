// 指针操作测试
void _start() {
    int data[8];
    int *ptr;
    
    // 测试1: 正常指针操作
    ptr = &data[0];
    *ptr = 100;
    
    // 测试2: 指针越界
    ptr = &data[8];  // 越界
    *ptr = 200;
    
    // 测试3: 空指针解引用
    int *null_ptr = 0;
    *null_ptr = 300;  // 应该被检测
    
    // 测试4: 野指针
    int *wild_ptr = (int*)0x12345678;
    *wild_ptr = 400;  // 应该被检测
}
