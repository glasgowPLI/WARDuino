
#include <stdint.h>

// 递归函数测试栈操作
int recursive_sum(int n, int depth) {
    if (n <= 0 || depth <= 0) {
        return 0;
    }
    
    int local_var1 = n * 2;
    int local_var2 = n + 5;
    int local_var3 = local_var1 * local_var2;
    
    return n + recursive_sum(n - 1, depth - 1) + local_var3;
}

// 大量局部变量操作
int stack_operations_test() {
    int var1 = 1, var2 = 2, var3 = 3, var4 = 4, var5 = 5;
    int var6 = 6, var7 = 7, var8 = 8, var9 = 9, var10 = 10;
    
    int sum = 0;
    for (int i = 0; i < 1000; i++) {
        var1 = var2 + var3;
        var2 = var3 * var4;
        var3 = var4 - var5;
        var4 = var5 / 2;
        var5 = var6 ^ var7;
        var6 = var7 | var8;
        var7 = var8 & var9;
        var8 = var9 << 1;
        var9 = var10 >> 1;
        var10 = var1 + i;
        
        sum += var1 + var2 + var3 + var4 + var5 + var6 + var7 + var8 + var9 + var10;
    }
    
    return sum;
}

int main() {
    int result = 0;
    
    // 递归调用测试栈深度
    result += recursive_sum(50, 20);
    
    // 栈变量操作测试
    result += stack_operations_test();
    
    return result;
}
