#!/usr/bin/env python3
"""
生成测试基准程序并编译为WASM模块
适应新的目录结构：/home/yuxin/WARDuino_test
"""

import os
import subprocess
import sys

class BenchmarkGenerator:
    def __init__(self):
        self.work_dir = "/home/yuxin/WARDuino_test"
        self.tests_dir = os.path.join(self.work_dir, "tests")
        self.ward_bin_dir = os.path.join(self.work_dir, "WARD_bin")
        
    def setup_directories(self):
        """创建必要的目录结构"""
        os.makedirs(self.tests_dir, exist_ok=True)
        os.makedirs(self.ward_bin_dir, exist_ok=True)
        print(f"工作目录: {self.work_dir}")
        print(f"测试程序目录: {self.tests_dir}")
        print(f"WARDuino二进制目录: {self.ward_bin_dir}")
    
    def check_compiler(self):
        """检查WASM编译器是否可用"""
        try:
            # 检查clang
            result = subprocess.run(["clang", "--version"], capture_output=True, text=True)
            if "clang" in result.stdout:
                print("✅ Clang编译器可用")
                return True
            else:
                print("❌ Clang编译器未找到")
                return False
        except FileNotFoundError:
            print("❌ Clang编译器未安装")
            return False
    
    def generate_memory_test(self):
        """生成内存访问测试程序"""
        memory_test_c = """
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
"""
        filename = os.path.join(self.tests_dir, "memory_test.c")
        with open(filename, "w") as f:
            f.write(memory_test_c)
        print(f"✅ 生成: {filename}")
        return filename
    
    def generate_stack_test(self):
        """生成栈操作测试程序"""
        stack_test_c = """
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
"""
        filename = os.path.join(self.tests_dir, "stack_test.c")
        with open(filename, "w") as f:
            f.write(stack_test_c)
        print(f"✅ 生成: {filename}")
        return filename
    
    def generate_control_test(self):
        """生成控制流测试程序"""
        control_test_c = """
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
"""
        filename = os.path.join(self.tests_dir, "control_test.c")
        with open(filename, "w") as f:
            f.write(control_test_c)
        print(f"✅ 生成: {filename}")
        return filename
    
    def generate_compute_test(self):
        """生成计算密集型测试程序"""
        compute_test_c = """
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

"""
        filename = os.path.join(self.tests_dir, "compute_test.c")
        with open(filename, "w") as f:
            f.write(compute_test_c)
        print(f"✅ 生成: {filename}")
        return filename
    
    def compile_to_wasm(self, c_file):
        """将C文件编译为WASM"""
        wasm_file = c_file.replace('.c', '.wasm')
        
        # 编译命令 - 适应WARDuino环境
        compile_cmd = [
            "clang",
            "--target=wasm32",
            "-O2",
            "-nostdlib",
            "-Wl,--no-entry",
            "-Wl,--export=main",
            "-Wl,--allow-undefined",
            "-Wl,--import-memory",
            "-o", wasm_file,
            c_file
        ]
        
        print(f"编译: {os.path.basename(c_file)} -> {os.path.basename(wasm_file)}")
        
        try:
            result = subprocess.run(compile_cmd, capture_output=True, text=True, cwd=self.tests_dir)
            if result.returncode == 0:
                print(f"✅ 成功编译: {os.path.basename(wasm_file)}")
                return wasm_file
            else:
                print(f"❌ 编译失败: {os.path.basename(c_file)}")
                print(f"错误: {result.stderr}")
                
                # 尝试简化编译命令
                print("尝试简化编译命令...")
                compile_cmd_simple = [
                    "clang",
                    "-O2",
                    "--target=wasm32",
                    "-nostdlib",
                    "-Wl,--no-entry",
                    "-Wl,--export=main",
                    "-o", wasm_file,
                    c_file
                ]
                result_simple = subprocess.run(compile_cmd_simple, capture_output=True, text=True, cwd=self.tests_dir)
                if result_simple.returncode == 0:
                    print(f"✅ 简化命令成功编译: {os.path.basename(wasm_file)}")
                    return wasm_file
                else:
                    print(f"❌ 简化命令也失败: {result_simple.stderr}")
                    return None
        except Exception as e:
            print(f"❌ 编译异常: {e}")
            return None
    
    def generate_all_benchmarks(self):
        """生成所有基准测试程序"""
        print("开始生成基准测试程序...")
        
        # 设置目录
        self.setup_directories()
        
        # 检查编译器
        if not self.check_compiler():
            print("请安装Clang编译器并配置WASM目标支持")
            print("Ubuntu/Debian: sudo apt-get install clang lld")
            return False
        
        # 生成测试程序
        test_files = [
            self.generate_memory_test(),
            self.generate_stack_test(), 
            self.generate_control_test(),
            self.generate_compute_test()
        ]
        
        # 编译为WASM
        wasm_files = []
        for c_file in test_files:
            wasm_file = self.compile_to_wasm(c_file)
            if wasm_file:
                wasm_files.append(wasm_file)
        
        print(f"\n🎯 生成完成!")
        print(f"生成的WASM文件: {len(wasm_files)}个")
        for wasm_file in wasm_files:
            print(f"  - {os.path.basename(wasm_file)}")
        
        return True

def main():
    """主函数"""
    generator = BenchmarkGenerator()
    success = generator.generate_all_benchmarks()
    
    if success:
        print("\n下一步: 运行 build_warduino_configs.sh 编译WARDuino，然后运行 run_benchmarks.py")
        sys.exit(0)
    else:
        print("\n生成基准测试程序失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
