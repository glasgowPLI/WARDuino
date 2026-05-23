// memory_safety_improved.c - 改进的WARDuino内存安全测试
// 完全不依赖标准库，专门测试WARDuino的内存保护能力

// 简单类型定义
typedef unsigned int uint32_t;
typedef int int32_t;

// 手动实现基本内存操作，避免库依赖
void* my_memset(void* ptr, int value, uint32_t num) {
    unsigned char* p = ptr;
    while (num--) {
        *p++ = (unsigned char)value;
    }
    return ptr;
}

void* my_memcpy(void* dest, const void* src, uint32_t num) {
    unsigned char* d = dest;
    const unsigned char* s = src;
    while (num--) {
        *d++ = *s++;
    }
    return dest;
}

// 测试用例1: 栈缓冲区溢出
int test_stack_overflow() {
    char buffer[8];
    
    // 正常写入
    for (int i = 0; i < 8; i++) {
        buffer[i] = (char)i;
    }
    
    // 故意溢出 - 应该被WARDuino检测到
    buffer[15] = 0xFF; // 越界写入
    
    return 1; // 如果返回这里，说明溢出未被检测
}

// 测试用例2: 使用未初始化内存
int test_uninitialized_read() {
    int buffer[4];
    int sum = 0;
    
    // 读取未初始化内存
    for (int i = 0; i < 4; i++) {
        sum += buffer[i];
    }
    
    return sum; // 返回值取决于未初始化内存内容
}

// 测试用例3: 空指针解引用
int test_null_dereference() {
    int* null_ptr = 0;
    *null_ptr = 42; // 应该导致崩溃或错误
    return 1;
}

// 测试用例4: 堆内存违规（使用静态数组模拟堆）
static char heap_memory[256];
static uint32_t heap_pointer = 0;

void* my_malloc(uint32_t size) {
    if (heap_pointer + size > sizeof(heap_memory)) {
        return 0;
    }
    void* ptr = &heap_memory[heap_pointer];
    heap_pointer += size;
    return ptr;
}

int test_heap_violation() {
    char* ptr1 = my_malloc(16);
    char* ptr2 = my_malloc(16);
    
    if (!ptr1 || !ptr2) return 0;
    
    // 初始化
    my_memset(ptr1, 0x11, 16);
    my_memset(ptr2, 0x22, 16);
    
    // 堆溢出：从ptr1写入到ptr2的空间
    for (int i = 16; i < 32; i++) {
        ptr1[i] = 0xFF;
    }
    
    // 检查ptr2是否被破坏
    for (int i = 0; i < 16; i++) {
        if (ptr2[i] != 0x22) {
            return 0; // 内存被破坏
        }
    }
    
    return 1; // 如果没有被检测到，返回1
}

// 测试用例5: 多次释放
int test_double_free() {
    char* ptr = my_malloc(8);
    if (!ptr) return 0;
    
    // 模拟多次释放 - 在简单分配器中不做实际释放
    // 这个测试主要验证WARDuino是否能检测重复操作
    
    return 1;
}

// 测试用例6: 栈下溢
int test_stack_underflow() {
    char buffer[8];
    
    // 栈下溢 - 写入buffer之前的地址
    buffer[-1] = 0xAA;
    
    return 1;
}

// 主测试函数
int main() {
    int results = 0;
    int test_count = 0;
    int passed_count = 0;
    
    // 每个测试都应该被WARDuino拦截
    // 如果测试"通过"（返回1），意味着WARDuino没有检测到违规
    
    // 测试1: 栈溢出
    test_count++;
    if (test_stack_overflow() == 1) {
        results |= 1;
        passed_count++;
    }
    
    // 测试2: 未初始化读取
    test_count++;
    if (test_uninitialized_read() != 0) { // 非零表示可能读取了垃圾值
        results |= 2;
        passed_count++;
    }
    
    // 测试3: 空指针解引用
    test_count++;
    // 这个测试可能不会返回，如果返回说明没有被拦截
    if (test_null_dereference() == 1) {
        results |= 4;
        passed_count++;
    }
    
    // 测试4: 堆违规
    test_count++;
    if (test_heap_violation() == 1) {
        results |= 8;
        passed_count++;
    }
    
    // 测试5: 多次释放
    test_count++;
    if (test_double_free() == 1) {
        results |= 16;
        passed_count++;
    }
    
    // 测试6: 栈下溢
    test_count++;
    if (test_stack_underflow() == 1) {
        results |= 32;
        passed_count++;
    }
    
    // 理想情况下，passed_count应该为0（所有违规都被检测到）
    // 如果passed_count > 0，说明有些违规没有被WARDuino检测到
    
    return passed_count; // 返回未被检测到的违规数量
}

// 入口点
void _start() {
    main();
}
