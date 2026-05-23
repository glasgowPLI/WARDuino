//内存拷贝
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define SIZE (10 * 1024 * 1024) // 10MB

void memory_copy_test() {
    char *src = malloc(SIZE);
    char *dst = malloc(SIZE);
    
    // 初始化源数据
    for (size_t i = 0; i < SIZE; i++) {
        src[i] = (char)(i % 256);
    }
    
    clock_t start = clock();
    memcpy(dst, src, SIZE);
    clock_t end = clock();
    
    // 验证拷贝是否正确
    int correct = 1;
    for (size_t i = 0; i < SIZE; i++) {
        if (dst[i] != src[i]) {
            correct = 0;
            break;
        }
    }
    
    double time_taken = ((double)(end - start)) / CLOCKS_PER_SEC;
    printf("Memory copy %s, took %.4f seconds\n", 
           correct ? "correct" : "incorrect", time_taken);
    
    free(src);
    free(dst);
}

int main() {
    memory_copy_test();
    return 0;
}

