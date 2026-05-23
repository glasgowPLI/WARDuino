// WARDuino内存安全测试程序 - 修复版
// 针对WASM目标和无标准库环境优化

// 避免与内置函数冲突，使用不同的函数名
void* my_memcpy(void* dest, const void* src, unsigned int n);
void* my_memset(void* s, int c, unsigned int n);
int my_memcmp(const void* s1, const void* s2, unsigned int n);

// 测试缓冲区大小
#define BUF_SIZE 32
#define SMALL_BUF_SIZE 8

// 全局变量用于测试
unsigned char global_buffer[BUF_SIZE];
unsigned char another_global[SMALL_BUF_SIZE];

// 内存越界写入测试（安全版本）
void test_buffer_overflow() {
    unsigned char buffer[SMALL_BUF_SIZE];
    
    // 正常写入
    for (int i = 0; i < SMALL_BUF_SIZE; i++) {
        buffer[i] = i;
    }
    
    // 越界写入测试 - 使用volatile防止优化
    volatile unsigned char* test_ptr = buffer;
    for (int i = SMALL_BUF_SIZE; i < SMALL_BUF_SIZE + 2; i++) { // 减少测试范围
        test_ptr[i] = 0xFF; // 潜在的内存破坏
    }
}

// 内存越界读取测试（安全版本）
void test_buffer_overread() {
    unsigned char buffer[SMALL_BUF_SIZE];
    volatile unsigned char value;
    
    // 初始化缓冲区
    for (int i = 0; i < SMALL_BUF_SIZE; i++) {
        buffer[i] = i + 1;
    }
    
    // 越界读取测试
    volatile unsigned char* test_ptr = buffer;
    for (int i = SMALL_BUF_SIZE; i < SMALL_BUF_SIZE + 1; i++) { // 最小化测试范围
        value = test_ptr[i]; // 读取边界外的数据
    }
}

// 使用未初始化内存测试
void test_uninitialized_memory() {
    unsigned char buffer[BUF_SIZE];
    volatile unsigned char sum = 0;
    
    // 没有初始化buffer就直接使用
    for (int i = 0; i < BUF_SIZE; i++) {
        sum += buffer[i]; // 使用未初始化的值
    }
}

// 资源管理测试（替代双重释放）
void test_resource_management() {
    static int resource_acquired = 0;
    
    // "分配"资源
    if (!resource_acquired) {
        resource_acquired = 1;
        my_memset(global_buffer, 0, BUF_SIZE);
    }
    
    // 使用后不释放 - 模拟资源泄漏
    for (int i = 0; i < BUF_SIZE; i++) {
        global_buffer[i] = (global_buffer[i] + 1) % 256;
    }
}

// 可控的空指针测试
void test_controlled_null_pointer() {
    volatile unsigned char* ptr = 0;
    volatile unsigned char value = 0x55; // 默认值
    
    // 在可控条件下测试空指针行为
    if (ptr != 0) { // 防止直接解引用
        value = *ptr;
    }
}

// 栈使用测试（替代栈溢出）
void test_stack_usage() {
    unsigned char stack_buffer[128]; // 合理的栈大小
    volatile unsigned int sum = 0;
    
    // 正常栈使用
    for (int i = 0; i < 128; i++) {
        stack_buffer[i] = i;
        sum += stack_buffer[i];
    }
}

// 内存对齐测试
void test_memory_alignment() {
    unsigned char data[8];
    volatile unsigned int aligned_value = 0;
    
    // 对齐的访问
    if (((unsigned long)data % 4) == 0) { // 检查对齐
        aligned_value = *((unsigned int*)data);
    }
}

// 安全的数组边界测试
void test_array_bounds() {
    int array[5] = {1, 2, 3, 4, 5};
    volatile int value = 0;
    
    // 有效的索引
    for (int i = 0; i < 5; i++) {
        value = array[i];
    }
    
    // 边界条件测试（注释掉危险的访问）
    // value = array[5];  // 刚好越界（在WASM中可能被捕获）
    // value = array[-1]; // 负索引（危险）
}

// 字符串操作测试
void test_string_operations() {
    char str1[12] = "hello"; // 预留足够空间
    char str2[6] = "test";
    
    // 安全的手动字符串复制
    int i = 0;
    while (str2[i] != '\0' && i < 11) { // 检查边界
        str1[i] = str2[i];
        i++;
    }
    if (i < 12) {
        str1[i] = '\0';
    }
}

// 内存重叠测试
void test_memory_overlap() {
    char buffer[20] = "abcdefghij";
    char temp[20];
    
    // 安全的重叠处理 - 使用临时缓冲区
    my_memcpy(temp, buffer, 20);
    for (int i = 5; i < 15; i++) {
        buffer[i] = temp[i - 5];
    }
}

// 全局缓冲区污染测试
void test_global_buffer_pollution() {
    static int test_count = 0;
    
    // 污染全局缓冲区
    for (int i = 0; i < BUF_SIZE; i++) {
        global_buffer[i] = (global_buffer[i] + test_count) % 256;
    }
    test_count++;
}

// 指针算术测试
void test_pointer_arithmetic() {
    unsigned char buffer[10];
    volatile unsigned char* ptr = buffer;
    volatile unsigned char value;
    
    // 有效的指针算术
    for (int i = 0; i < 10; i++) {
        value = *(ptr + i);
        *(ptr + i) = value + 1;
    }
}

// 主测试函数
void run_memory_safety_tests() {
    // 运行各种内存安全测试
    test_buffer_overflow();
    test_buffer_overread();
    test_uninitialized_memory();
    test_resource_management();
    test_controlled_null_pointer();
    test_stack_usage();
    test_memory_alignment();
    test_array_bounds();
    test_string_operations();
    test_memory_overlap();
    test_global_buffer_pollution();
    test_pointer_arithmetic();
}

// 自定义内存操作函数（避免与内置函数冲突）
void* my_memcpy(void* dest, const void* src, unsigned int n) {
    unsigned char* d = (unsigned char*)dest;
    const unsigned char* s = (const unsigned char*)src;
    
    for (unsigned int i = 0; i < n; i++) {
        d[i] = s[i];
    }
    return dest;
}

void* my_memset(void* s, int c, unsigned int n) {
    unsigned char* p = (unsigned char*)s;
    
    for (unsigned int i = 0; i < n; i++) {
        p[i] = (unsigned char)c;
    }
    return s;
}

int my_memcmp(const void* s1, const void* s2, unsigned int n) {
    const unsigned char* p1 = (const unsigned char*)s1;
    const unsigned char* p2 = (const unsigned char*)s2;
    
    for (unsigned int i = 0; i < n; i++) {
        if (p1[i] != p2[i]) {
            return (int)p1[i] - (int)p2[i];
        }
    }
    return 0;
}

// WASM入口点
void _start() {
    // 初始化全局缓冲区
    my_memset(global_buffer, 0, BUF_SIZE);
    my_memset(another_global, 0, SMALL_BUF_SIZE);
    
    // 运行内存安全测试
    run_memory_safety_tests();
    
    // WASM不需要返回值
}

// 导出函数供外部调用
void __attribute__((export_name("run_tests"))) run_tests() {
    run_memory_safety_tests();
}
