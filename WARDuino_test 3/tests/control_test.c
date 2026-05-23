
#include <stdint.h>

// 多个函数用于测试控制流
int func_a(int x) { return x + 1; }
int func_b(int x) { return x * 2; }
int func_c(int x) { return x - 3; }
int func_d(int x) { return x / 2; }
int func_e(int x) { return x ^ 0x55; }

typedef int (*func_ptr_t)(int);

func_ptr_t func_table[] = {
    func_a, func_b, func_c, func_d, func_e
};

#define FUNC_COUNT (sizeof(func_table) / sizeof(func_table[0]))

// 嵌套函数调用
int nested_call_1(int x) {
    return x * 3 + 1;
}

int nested_call_2(int x) {
    return nested_call_1(x) + 5;
}

int nested_call_3(int x) {
    return nested_call_2(x) * 2;
}

int main() {
    int result = 0;
    
    // 条件分支
    for (int i = 0; i < 10000; i++) {
        if (i % 2 == 0) {
            result += i * 2;
        } else {
            result += i / 2;
        }
        
        if (i % 3 == 0) {
            result -= i;
        } else if (i % 3 == 1) {
            result += i * 3;
        } else {
            result += i;
        }
    }
    
    // 循环控制
    for (int i = 0; i < 5000; i++) {
        for (int j = 0; j < 10; j++) {
            if (j == 5) continue;
            result += i * j;
            if (result > 1000000) break;
        }
    }
    
    // 函数调用
    for (int i = 0; i < 2000; i++) {
        result += func_a(i);
        result += func_b(i + 1);
    }
    
    // 间接调用
    for (int i = 0; i < 3000; i++) {
        func_ptr_t func = func_table[i % FUNC_COUNT];
        result += func(i);
    }
    
    // 嵌套调用
    for (int i = 0; i < 1500; i++) {
        result += nested_call_3(i);
    }
    
    return result;
}
