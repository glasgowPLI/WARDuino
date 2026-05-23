
#include <stdint.h>

#define ARRAY_SIZE 5000

static int32_t data_array[ARRAY_SIZE];

int main() {
    // 初始化数组
    for (int i = 0; i < ARRAY_SIZE; i++) {
        data_array[i] = i * 3;
    }
    
    // 各种内存访问模式
    int32_t result = 0;
    
    // 顺序访问
    for (int i = 0; i < ARRAY_SIZE; i++) {
        result += data_array[i];
    }
    
    // 随机访问模式
    for (int i = 0; i < ARRAY_SIZE; i++) {
        int index = (i * 7) % ARRAY_SIZE;
        result += data_array[index];
    }
    
    // 边界访问
    for (int i = 0; i < 1000; i++) {
        result += data_array[i];
        if (i < ARRAY_SIZE - 1) {
            result += data_array[ARRAY_SIZE - 1 - i];
        }
    }
    
    return result;
}
