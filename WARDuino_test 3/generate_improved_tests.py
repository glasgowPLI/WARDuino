#!/usr/bin/env python3
# generate_improved_tests.py - 生成改进的测试用例

import os
from pathlib import Path

def create_improved_oob_test():
    """创建改进的越界访问测试"""
    code = '''#include <stdint.h>

// 更激进的越界访问测试
void _start() {
    volatile char buffer[8];
    
    // 初始化缓冲区
    for (int i = 0; i < 8; i++) {
        buffer[i] = i;
    }
    
    // 更激进的越界读取 - 访问更远的内存
    volatile char value;
    for (int i = 8; i < 64; i++) {
        value = buffer[i]; // 越界读取
    }
    
    // 更激进的越界写入
    for (int i = 8; i < 64; i++) {
        buffer[i] = 0xFF; // 越界写入
    }
}
'''
    
    with open("ward_tests/improved_oob_test.c", "w") as f:
        f.write(code)
    print("✅ 创建 improved_oob_test.c")

def create_improved_heap_test():
    """创建改进的堆溢出测试"""
    code = '''#include <stdint.h>

#define LARGE_SIZE 1024

// 改进的堆溢出模拟测试
static char heap_area[LARGE_SIZE];
static int heap_used = 0;

void* sim_malloc(int size) {
    if (!heap_used && size <= LARGE_SIZE) {
        heap_used = 1;
        return heap_area;
    }
    return 0;
}

void sim_free(void* ptr) {
    if (ptr == heap_area) {
        heap_used = 0;
    }
}

void _start() {
    // 分配内存
    char* ptr = sim_malloc(16);
    if (ptr) {
        // 大规模越界写入
        for (int i = 16; i < LARGE_SIZE + 100; i++) {
            ptr[i] = 0xAA; // 堆溢出
        }
        
        sim_free(ptr);
        
        // 双重释放
        sim_free(ptr);
    }
}
'''
    
    with open("ward_tests/improved_heap_test.c", "w") as f:
        f.write(code)
    print("✅ 创建 improved_heap_test.c")

def create_improved_stack_test():
    """创建改进的栈溢出测试"""
    code = '''#include <stdint.h>

// 深度递归导致栈溢出
void recursive_func(int depth, char large_buffer[1024]) {
    // 使用大栈帧
    char local_buffer[512];
    
    // 填充缓冲区
    for (int i = 0; i < 512; i++) {
        local_buffer[i] = depth + i;
    }
    
    if (depth > 0) {
        recursive_func(depth - 1, large_buffer);
    }
}

void _start() {
    char main_buffer[1024];
    // 深度递归，使用大栈帧
    recursive_func(50, main_buffer);
}
'''
    
    with open("ward_tests/improved_stack_test.c", "w") as f:
        f.write(code)
    print("✅ 创建 improved_stack_test.c")

def create_improved_arithmetic_test():
    """创建改进的算术异常测试"""
    code = '''#include <stdint.h>

void _start() {
    volatile int a, b, result;
    volatile float f1, f2, fresult;
    
    // 除零测试
    a = 10;
    b = 0;
    result = a / b; // 整数除零
    
    // 浮点除零
    f1 = 10.0f;
    f2 = 0.0f;
    fresult = f1 / f2; // 浮点除零
    
    // 整数溢出
    volatile int max_int = 2147483647;
    volatile int min_int = -2147483648;
    
    result = max_int + 1; // 上溢
    result = min_int - 1; // 下溢
    
    // 大数乘法溢出
    result = max_int * 2;
}
'''
    
    with open("ward_tests/improved_arithmetic_test.c", "w") as f:
        f.write(code)
    print("✅ 创建 improved_arithmetic_test.c")

def compile_improved_tests():
    """编译改进的测试用例"""
    improved_tests = [
        "improved_oob_test.c",
        "improved_heap_test.c", 
        "improved_stack_test.c",
        "improved_arithmetic_test.c"
    ]
    
    for test_file in improved_tests:
        wasm_file = test_file.replace('.c', '.wasm')
        cmd = f"clang --target=wasm32 -nostdlib -Wl,--no-entry -Wl,--export-all -Wl,--allow-undefined -o ward_tests/{wasm_file} ward_tests/{test_file}"
        print(f"编译: {test_file} -> {wasm_file}")
        os.system(cmd)

def main():
    print("生成改进的测试用例...")
    
    # 确保目录存在
    Path("ward_tests").mkdir(exist_ok=True)
    
    # 创建改进的测试用例
    create_improved_oob_test()
    create_improved_heap_test()
    create_improved_stack_test()
    create_improved_arithmetic_test()
    
    print("\n编译改进的测试用例...")
    compile_improved_tests()
    
    print("\n🎉 改进的测试用例生成完成!")
    print("接下来可以运行:")
    print("1. python3 run_focused_tests.py - 运行聚焦测试")
    print("2. python3 analyze_results.py - 分析结果")

if __name__ == "__main__":
    main()
