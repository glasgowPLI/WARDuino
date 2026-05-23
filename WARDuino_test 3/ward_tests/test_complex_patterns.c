// 复杂内存访问模式测试
void _start() {
    // 测试1: 结构体访问
    struct Data {
        int id;
        char name[8];
        float value;
    };
    
    struct Data items[3];
    
    // 正常结构体访问
    items[0].id = 1;
    
    // 结构体越界
    items[3].id = 4;  // 数组越界
    
    // 测试2: 指针算术
    int array[10];
    int *ptr = array;
    
    // 正常指针算术
    *(ptr + 5) = 50;
    
    // 危险指针算术
    *(ptr + 15) = 150;  // 越界
    
    // 测试3: 函数指针（间接调用）
    void (*func_ptr)() = 0;
    func_ptr();  // 调用空函数指针
    
    // 测试4: 递归栈消耗
    volatile char buffer[256];  // 大栈分配
    buffer[0] = 0;  // 防止优化
}
