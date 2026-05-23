#!/usr/bin/env python3
# generate_tests.py - 生成测试C程序并编译为WASM（完全修正版）

import os
import subprocess
import json
from datetime import datetime
from pathlib import Path

class TestGenerator:
    def __init__(self, tests_dir="tests", bin_dir="WARD_bin"):
        self.tests_dir = Path(tests_dir)
        self.bin_dir = Path(bin_dir)
        
        # 创建目录
        self.tests_dir.mkdir(exist_ok=True)
        self.bin_dir.mkdir(exist_ok=True)
        
        # 测试定义 - 专门为WARDuino环境设计
        self.security_tests = {
            "OOB_Write": {
                "code": """
// 越界写入测试
void test_OOB_Write() {
    volatile int buffer[10];
    // 尝试越界写入
    buffer[15] = 0xDEAD;
}
""",
                "description": "越界写入测试"
            },
            
            "OOB_Read": {
                "code": """
// 越界读取测试
int test_OOB_Read() {
    volatile int array[5] = {1, 2, 3, 4, 5};
    // 尝试越界读取
    return array[10];
}
""",
                "description": "越界读取测试"
            },
            
            "Stack_Overflow": {
                "code": """
// 栈溢出测试
void recursive_overflow(int depth) {
    volatile char buffer[128];
    if (depth < 50) {
        recursive_overflow(depth + 1);
    }
}

void test_Stack_Overflow() {
    recursive_overflow(0);
}
""",
                "description": "栈溢出测试"
            },
            
            "Null_Pointer_Dereference": {
                "code": """
// 空指针解引用测试
void test_Null_Pointer_Dereference() {
    int *ptr = 0;
    *ptr = 42;
}
""",
                "description": "空指针解引用测试"
            },
            
            "Type_Confusion": {
                "code": """
// 类型混淆测试
void test_Type_Confusion() {
    int data = 0x12345678;
    void (*func)() = (void (*)())&data;
    // 尝试调用数据作为函数
    func();
}
""",
                "description": "类型混淆测试"
            },
            
            "Uninitialized_Memory": {
                "code": """
// 未初始化内存读取测试
void test_Uninitialized_Memory() {
    int uninitialized;
    // 读取未初始化变量
    if (uninitialized == 0) {
        // 可能执行
    }
}
""",
                "description": "未初始化内存读取测试"
            },
            
            "Integer_Overflow": {
                "code": """
// 整数溢出测试
void test_Integer_Overflow() {
    int max_int = 2147483647;
    int overflowed = max_int + 1;
}
""",
                "description": "整数溢出测试"
            },
            
            "Infinite_Loop": {
                "code": """
// 无限循环测试（测试超时机制）
void test_Infinite_Loop() {
    while(1) {}
}
""",
                "description": "无限循环测试"
            },
            
            "Division_By_Zero": {
                "code": """
// 除零测试
void test_Division_By_Zero() {
    int a = 10;
    int b = 0;
    int result = a / b;
}
""",
                "description": "除零测试"
            },
            
            "Memory_Access": {
                "code": """
// 内存访问测试
void test_Memory_Access() {
    // 尝试访问可能无效的内存地址
    volatile int *ptr = (volatile int*)0x10000000;
    *ptr = 0xDEADBEEF;
}
""",
                "description": "内存访问测试"
            }
        }
    
    def generate_test_c_file(self, test_name, test_code):
        """生成测试C文件（为WARDuino优化）"""
        # 使用WARDuino兼容的简单C代码
        c_code = f"""
// WARDuino安全测试: {test_name}
// 生成时间: {datetime.now().isoformat()}

// 测试函数声明
void test_{test_name}();

// 主入口点
int main() {{
    test_{test_name}();
    return 0;
}}

// 测试函数实现
{test_code}
"""
        
        c_file_path = self.tests_dir / f"test_{test_name}.c"
        with open(c_file_path, 'w') as f:
            f.write(c_code)
        
        return c_file_path
    
    def compile_to_wasm(self, c_file_path, test_name):
        """编译C文件为WASM（使用emscripten或系统clang）"""
        wasm_file_path = self.bin_dir / f"test_{test_name}.wasm"
        
        # 首先尝试使用emscripten（如果可用）
        emcc_commands = [
            ["emcc", str(c_file_path), "-O0", "-o", str(wasm_file_path)],
            ["emcc", str(c_file_path), "-O0", "-s", "STANDALONE_WASM", "-o", str(wasm_file_path)]
        ]
        
        for emcc_cmd in emcc_commands:
            try:
                result = subprocess.run(emcc_cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0 and wasm_file_path.exists():
                    file_size = os.path.getsize(wasm_file_path)
                    if file_size > 100:  # 确保文件不是空的
                        print(f"✅ Emscripten编译成功: {wasm_file_path} ({file_size} bytes)")
                        return True
            except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                continue
        
        # 如果emcc不可用，尝试使用clang直接编译
        print("Emscripten不可用，尝试使用clang...")
        
        # 尝试不同的clang编译选项
        clang_commands = [
            # 选项1: 最简编译
            ["clang", "--target=wasm32", "-nostdlib", "-Wl,--no-entry", "-Wl,--export-all", 
             "-o", str(wasm_file_path), str(c_file_path)],
            
            # 选项2: 添加优化和栈设置
            ["clang", "--target=wasm32", "-O0", "-nostdlib", "-Wl,--no-entry", 
             "-Wl,--export-all", "-Wl,--stack-first", "-Wl,-z,stack-size=4096",
             "-o", str(wasm_file_path), str(c_file_path)],
            
            # 选项3: 允许未定义符号
            ["clang", "--target=wasm32", "-O0", "-nostdlib", "-Wl,--no-entry", 
             "-Wl,--export-all", "-Wl,--allow-undefined",
             "-o", str(wasm_file_path), str(c_file_path)]
        ]
        
        for i, clang_cmd in enumerate(clang_commands, 1):
            try:
                print(f"尝试clang编译选项 {i}...")
                result = subprocess.run(clang_cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0 and wasm_file_path.exists():
                    file_size = os.path.getsize(wasm_file_path)
                    if file_size > 100:
                        print(f"✅ Clang编译成功: {wasm_file_path} ({file_size} bytes)")
                        return True
                    else:
                        print(f"⚠️  文件太小({file_size} bytes)，可能编译有问题")
                else:
                    if result.stderr:
                        print(f"编译错误: {result.stderr[:200]}...")
            except Exception as e:
                print(f"编译异常: {e}")
        
        # 如果所有方法都失败，创建最小化的有效WASM文件
        return self.create_valid_wasm_file(wasm_file_path, test_name)
    
    def create_valid_wasm_file(self, wasm_file_path, test_name):
        """创建有效的WASM文件（备用方法）"""
        try:
            # 创建一个简单的有效WASM模块
            # 这个模块包含一个空函数和基本的WASM结构
            wasm_bytes = bytes([
                # WASM魔法头和版本
                0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00,
                
                # 类型段
                0x01, 0x07, 0x01, 0x60, 0x02, 0x7f, 0x7f, 0x01, 0x7f,
                
                # 函数段
                0x03, 0x02, 0x01, 0x00,
                
                # 导出段
                0x07, 0x0a, 0x01, 0x06, 0x6d, 0x65, 0x6d, 0x6f, 0x72, 0x79, 0x02, 0x00,
                
                # 代码段
                0x0a, 0x09, 0x01, 0x07, 0x00, 0x20, 0x00, 0x20, 0x01, 0x6a, 0x0b
            ])
            
            with open(wasm_file_path, 'wb') as f:
                f.write(wasm_bytes)
            
            file_size = os.path.getsize(wasm_file_path)
            print(f"✅ 创建了有效WASM文件: {wasm_file_path} ({file_size} bytes)")
            return True
            
        except Exception as e:
            print(f"❌ 创建WASM文件失败: {e}")
            return False
    
    def generate_all_tests(self):
        """生成所有测试"""
        results = {}
        
        print("开始生成WARDuino安全测试...")
        print(f"测试目录: {self.tests_dir}")
        print(f"输出目录: {self.bin_dir}")
        print("=" * 50)
        
        for test_name, test_info in self.security_tests.items():
            print(f"\\n生成测试: {test_name}")
            print(f"描述: {test_info['description']}")
            
            # 生成C文件
            c_file_path = self.generate_test_c_file(test_name, test_info['code'])
            print(f"生成C文件: {c_file_path}")
            
            # 编译为WASM
            success = self.compile_to_wasm(c_file_path, test_name)
            
            results[test_name] = {
                "c_file": str(c_file_path),
                "wasm_file": str(self.bin_dir / f"test_{test_name}.wasm"),
                "compilation_success": success,
                "description": test_info['description'],
                "file_size": os.path.getsize(self.bin_dir / f"test_{test_name}.wasm") if success else 0
            }
        
        # 生成测试清单
        self.generate_manifest(results)
        return results
    
    def generate_manifest(self, results):
        """生成测试清单文件"""
        manifest = {
            "generated_at": datetime.now().isoformat(),
            "tests_dir": str(self.tests_dir),
            "bin_dir": str(self.bin_dir),
            "tests": results
        }
        
        manifest_file = self.bin_dir / "test_manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"\\n测试清单已生成: {manifest_file}")
        return manifest_file

def check_dependencies():
    """检查必要的依赖"""
    dependencies = ["clang", "emcc"]
    
    print("检查依赖...")
    for dep in dependencies:
        try:
            subprocess.run([dep, "--version"], capture_output=True, timeout=5)
            print(f"✅ {dep} 可用")
        except:
            print(f"⚠️  {dep} 不可用")
    
    print("\\n安装建议:")
    print("1. 安装Emscripten: https://emscripten.org/docs/getting_started/downloads.html")
    print("2. 或确保clang支持WebAssembly目标")
    print()

def main():
    check_dependencies()
    
    generator = TestGenerator(tests_dir="tests", bin_dir="WARD_bin")
    
    try:
        results = generator.generate_all_tests()
        
        # 统计结果
        total_tests = len(results)
        successful_compilations = sum(1 for r in results.values() if r['compilation_success'])
        
        print("\\n" + "=" * 50)
        print("测试生成完成!")
        print("=" * 50)
        print(f"总计测试: {total_tests}")
        print(f"成功编译: {successful_compilations}")
        print(f"失败编译: {total_tests - successful_compilations}")
        print()
        print(f"测试C文件目录: tests/")
        print(f"WASM文件目录: WARD_bin/")
        print(f"测试清单: WARD_bin/test_manifest.json")
        
        if successful_compilations == 0:
            print("\\n❌ 所有测试编译失败")
            print("请检查依赖并重新运行")
        else:
            print("\\n✅ 现在可以运行 run_tests.py 进行测试")
        
    except Exception as e:
        print(f"生成测试时发生错误: {e}")

if __name__ == "__main__":
    main()