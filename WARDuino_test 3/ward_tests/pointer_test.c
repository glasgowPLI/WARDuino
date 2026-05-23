void _start() {
    int data[8];
    int *ptr = data;
    
    // 正常指针运算
    ptr = ptr + 4;
    *ptr = 100;
    
    // 危险指针运算
    ptr = ptr + 10;  // 越界
    *ptr = 200;
}
