
#include <stdint.h>

#define ITERATIONS 10000

// 简单的平方根近似（仅用于测试，不是精确的）
float sqrtf_approx(float x) {
    if (x <= 0.0f) return 0.0f;
    float y = x;
    for (int i = 0; i < 10; i++) {
        y = (y + x / y) * 0.5f;
    }
    return y;
}

double sqrt_approx(double x) {
    if (x <= 0.0) return 0.0;
    double y = x;
    for (int i = 0; i < 10; i++) {
        y = (y + x / y) * 0.5;
    }
    return y;
}

// 各种计算操作
int main() {
    int result = 0;
    float f_result = 0.0f;
    double d_result = 0.0;
    
    // 整数运算
    for (int i = 0; i < ITERATIONS; i++) {
        result += i * i;
        result -= (i + 1) * (i - 1);
        result |= i & 0xFF;
        result ^= (i << 3) | (i >> 5);
    }
    
    // 浮点运算
    for (int i = 1; i < ITERATIONS; i++) {
        f_result += 1.0f / i;
        f_result *= 1.0001f;
        f_result = sqrtf_approx(f_result + 1.0f);  // 使用近似平方根
    }
    
    // 双精度运算
    for (int i = 1; i < ITERATIONS; i++) {
        d_result += 1.0 / i;
        d_result *= 1.0001;
        d_result = sqrt_approx(d_result + 1.0);  // 使用近似平方根
    }
    
    // 混合运算
    for (int i = 0; i < ITERATIONS; i++) {
        // 整数转浮点
        float temp_f = (float)result;
        // 浮点运算
        temp_f = temp_f * 1.5f + 0.5f;
        // 浮点转整数
        result = (int)temp_f;
        
        // 双精度运算
        d_result = d_result * 0.9999 + (double)i;
    }
    
    // 位运算
    for (int i = 0; i < ITERATIONS; i++) {
        result = (result << 3) | (result >> 29);
        result ^= 0xAAAAAAAA;
        result &= 0x7FFFFFFF;
    }
    
    return result + (int)f_result + (int)d_result;
}

