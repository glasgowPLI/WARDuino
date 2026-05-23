## 头文件 (security_tests.h)

#ifndef SECURITY_TESTS_H
#define SECURITY_TESTS_H

// 测试函数声明
void test_oob_write(void);
int test_oob_read(void);
void test_stack_overflow(void);
void test_heap_overflow(void);
void test_use_after_free(void);
void test_cfi_integrity(void);
void test_type_confusion(void);
void test_hw_access(void);
void test_privilege_escalation(void);
void test_double_free(void);

// 测试结果结构
typedef struct {
    char test_name[32];
    char status[16];
    char error_message[64];
    uint32_t execution_time_ms;
    uint32_t memory_usage;
} test_result_t;

// 工具函数
uint32_t get_free_heap(void);
uint32_t get_time_ms(void);
void run_test(const char* name, void (*test_func)(void), const char* expected_behavior);
void generate_test_report(void);

#endif // SECURITY_TESTS_H

