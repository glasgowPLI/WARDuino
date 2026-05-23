#include <stdlib.h>
#include "esp_system.h"

// 测试1: 越界内存写
#define BUF_SIZE 10
volatile int buffer[BUF_SIZE];

void test_oob_write(void) {
    // 尝试写入边界之外的位置
    buffer[BUF_SIZE] = 0xDEAD; // 应被运行时捕获
}

// 测试2: 越界内存读
volatile int array[5] = {1, 2, 3, 4, 5};

int test_oob_read(void) {
    return array[10]; // 应触发陷阱或异常
}

// 测试3: 栈溢出检测
void recursive_overflow(int i) {
    volatile char buffer[256];
    buffer[0] = 'A'; // 防止优化
    if (i > 0) recursive_overflow(i+1);
}

void test_stack_overflow(void) {
    recursive_overflow(1);
}

// 测试4: 堆溢出检测
void test_heap_overflow(void) {
    char *a = malloc(10);
    if (a) {
        a[10] = 'x'; // 写入分配块尾部之外
        free(a);
    }
}

// 测试5: 释放后使用
void test_use_after_free(void) {
    int *x = malloc(sizeof(int));
    if (x) {
        free(x);
        *x = 42; // 使用已释放内存
    }
}

// 测试6: 控制流劫持测试
void (*volatile fp)(void);

void test_cfi_integrity(void) {
    fp = (void (*)(void))0xDEADBEEF; // 非法目标地址
    fp(); // 应被控制流完整性机制阻断
}

// 测试7: 类型混淆攻击尝试
int data = 0x12345678;

void test_type_confusion(void) {
    void (*func)(void) = (void (*)(void))&data;
    func(); // 应被类型安全机制阻止
}

// 测试8: 非法硬件访问
// 注意：需要根据ESP32的实际内存映射调整
#define ILLEGAL_REG (*(volatile unsigned int *)0x40000000)

void test_hw_access(void) {
    ILLEGAL_REG = 0xFF; // 应被权限管理或MMU隔离阻止
}

// 测试9: 权限提升尝试
void privileged_operation(void) {
    // 模拟特权操作 - 尝试访问系统寄存器
    // 在Wasm环境中这会触发安全异常
    asm volatile ("nop"); // 占位符
}

void test_privilege_escalation(void) {
    privileged_operation(); // 应被权限控制系统拒绝
}

// 测试10: 双重释放检测
void test_double_free(void) {
    void *ptr = malloc(100);
    if (ptr) {
        free(ptr);
        free(ptr); // 二次释放
    }
}
