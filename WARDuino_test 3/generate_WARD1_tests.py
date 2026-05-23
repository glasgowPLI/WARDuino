#!/usr/bin/env python3
import os
import json
from pathlib import Path
from datetime import datetime

class TestGenerator:
    def __init__(self, test_dir="tests", bin_dir="WARD_bin"):
        self.test_dir = Path(test_dir)
        self.bin_dir = Path(bin_dir)
        self.test_dir.mkdir(exist_ok=True)
        self.bin_dir.mkdir(exist_ok=True)
        
        # 测试程序模板
        self.test_templates = {
            "OOB_Write": {
                "description": "内存越界写入测试",
                "code": """// 内存越界写入测试
#define BUF_SIZE 8

void test_OOB_Write() {{
    unsigned char buffer[BUF_SIZE];
    
    // 正常写入
    for (int i = 0; i < BUF_SIZE; i++) {{
        buffer[i] = i;
    }}
    
    // 越界写入
    for (int i = BUF_SIZE; i < BUF_SIZE + 4; i++) {{
        buffer[i] = 0xFF; // 越界写入
    }}
}}

void _start() {{
    test_OOB_Write();
}}
"""
            },
            
            "OOB_Read": {
                "description": "内存越界读取测试",
                "code": """// 内存越界读取测试
#define BUF_SIZE 8

void test_OOB_Read() {{
    unsigned char buffer[BUF_SIZE];
    
    // 初始化缓冲区
    for (int i = 0; i < BUF_SIZE; i++) {{
        buffer[i] = i + 1;
    }}
    
    // 越界读取
    volatile unsigned char value;
    for (int i = BUF_SIZE; i < BUF_SIZE + 3; i++) {{
        if (i < sizeof(buffer)) {{ // 安全检查，但条件永远不会为真，用于测试
            value = buffer[i];
        }} else {{
            value = buffer[i]; // 实际越界读取
        }}
    }}
}}

void _start() {{
    test_OOB_Read();
}}
"""
            },
            
            "Stack_Overflow": {
                "description": "栈溢出测试",
                "code": """// 栈溢出测试
void recursive_function(int depth) {{
    unsigned char stack_buffer[256];
    if (depth > 0) {{
        recursive_function(depth - 1);
    }}
}}

void test_Stack_Overflow() {{
    recursive_function(100);
}}

void _start() {{
    test_Stack_Overflow();
}}
"""
            },
            
            "Null_Pointer_Dereference": {
                "description": "空指针解引用测试",
                "code": """// 空指针解引用测试
void test_Null_Pointer_Dereference() {{
    volatile unsigned char* ptr = 0;
    volatile unsigned char value;
    
    value = *ptr; // 解引用空指针
}}

void _start() {{
    test_Null_Pointer_Dereference();
}}
"""
            },
            
            "Uninitialized_Memory": {
                "description": "未初始化内存使用测试",
                "code": """// 未初始化内存使用测试
#define BUF_SIZE 16

void test_Uninitialized_Memory() {{
    unsigned char buffer[BUF_SIZE];
    volatile unsigned char sum = 0;
    
    // 使用未初始化的内存
    for (int i = 0; i < BUF_SIZE; i++) {{
        sum += buffer[i];
    }}
}}

void _start() {{
    test_Uninitialized_Memory();
}}
"""
            },
            
            "Integer_Overflow": {
                "description": "整数溢出测试",
                "code": """// 整数溢出测试
void test_Integer_Overflow() {{
    int max_int = 2147483647;
    volatile int result = max_int + 1; // 整数溢出
}}

void _start() {{
    test_Integer_Overflow();
}}
"""
            },
            
            "Infinite_Loop": {
                "description": "无限循环测试",
                "code": """// 无限循环测试
void test_Infinite_Loop() {{
    while (1) {{
        // 无限循环
    }}
}}

void _start() {{
    test_Infinite_Loop();
}}
"""
            },
            
            "Division_By_Zero": {
                "description": "除零错误测试",
                "code": """// 除零错误测试
void test_Division_By_Zero() {{
    volatile int a = 10;
    volatile int b = 0;
    volatile int result = a / b; // 除零
}}

void _start() {{
    test_Division_By_Zero();
}}
"""
            },
            
            "Memory_Access": {
                "description": "内存访问错误测试",
                "code": """// 内存访问错误测试
void test_Memory_Access() {{
    volatile int* ptr = (volatile int*)0x1000;
    volatile int value = *ptr; // 访问可能无效的内存地址
}}

void _start() {{
    test_Memory_Access();
}}
"""
            },
            
            "Type_Confusion": {
                "description": "类型混淆测试",
                "code": """// 类型混淆测试
void test_Type_Confusion() {{
    float f = 3.14f;
    int* int_ptr = (int*)&f; // 类型混淆
    volatile int value = *int_ptr;
}}

void _start() {{
    test_Type_Confusion();
}}
"""
            },
            
            "Memory_Alignment": {
                "description": "内存对齐错误测试",
                "code": """// 内存对齐错误测试
void test_Memory_Alignment() {{
    unsigned char data[10];
    volatile unsigned int* int_ptr;
    
    // 未对齐的指针访问
    int_ptr = (unsigned int*)(data + 1);
    *int_ptr = 0x12345678;
}}

void _start() {{
    test_Memory_Alignment();
}}
"""
            },
            
            "Buffer_Underflow": {
                "description": "缓冲区下溢测试",
                "code": """// 缓冲区下溢测试
void test_Buffer_Underflow() {{
    unsigned char buffer[8];
    volatile unsigned char* ptr = buffer;
    volatile unsigned char value = 0;
    
    // 正常访问
    for (int i = 0; i < 8; i++) {{
        ptr[i] = i;
    }}
    
    // 尝试下溢访问
    for (int i = -2; i < 0; i++) {{
        if (i >= 0 && i < 8) {{
            value = ptr[i];
        }} else {{
            value = ptr[i]; // 实际下溢访问
        }}
    }}
}}

void _start() {{
    test_Buffer_Underflow();
}}
"""
            },
            
            "Double_Free_Simulation": {
                "description": "双重释放模拟测试",
                "code": """// 双重释放模拟测试
static int resource_acquired = 0;

void test_Double_Free_Simulation() {{
    // "分配"资源
    if (!resource_acquired) {{
        resource_acquired = 1;
    }}
    
    // "释放"资源
    resource_acquired = 0;
    
    // 再次"释放" - 模拟双重释放
    resource_acquired = 0; // 重复操作，可能造成状态不一致
}}

void _start() {{
    test_Double_Free_Simulation();
}}
"""
            },
            
            "Use_After_Free_Simulation": {
                "description": "释放后使用模拟测试",
                "code": """// 释放后使用模拟测试
static unsigned char* global_ptr = 0;
static unsigned char buffer[16];

void test_Use_After_Free_Simulation() {{
    global_ptr = buffer;
    
    // 模拟"释放"
    global_ptr = 0;
    
    // 模拟"释放后使用"
    if (global_ptr) {{
        volatile unsigned char value = *global_ptr;
    }} else {{
        // 实际使用已释放的内存
        volatile unsigned char value = buffer[0];
    }}
}}

void _start() {{
    test_Use_After_Free_Simulation();
}}
"""
            },
            
            "Format_String_Simulation": {
                "description": "格式化字符串漏洞模拟测试",
                "code": """// 格式化字符串漏洞模拟测试
void test_Format_String_Simulation() {{
    volatile char buffer[20] = "test";
    volatile char* format = buffer;
    
    // 模拟不安全的格式化字符串使用
    volatile int count = 0;
    while (*format) {{
        if (*format == '%') {{
            count++; // 模拟格式说明符处理
        }}
        format++;
    }}
}}

void _start() {{
    test_Format_String_Simulation();
}}
"""
            }
        }
    
    def generate_test_files(self):
        """生成所有测试文件"""
        print("开始生成测试程序...")
        print("=" * 50)
        
        generated_files = []
        
        for test_name, test_info in self.test_templates.items():
            filename = f"test_{test_name}.c"
            filepath = self.test_dir / filename
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(test_info["code"])
                
                generated_files.append(filename)
                print(f"✅ 生成: {filename} - {test_info['description']}")
                
            except Exception as e:
                print(f"❌ 生成失败 {filename}: {e}")
        
        return generated_files
    
    def generate_manifest(self):
        """生成测试清单文件"""
        manifest = {
            "generated_at": datetime.now().isoformat(),
            "tests": {}
        }
        
        for test_name, test_info in self.test_templates.items():
            c_file = f"tests/test_{test_name}.c"
            wasm_file = f"WARD_bin/test_{test_name}.wasm"
            
            manifest["tests"][test_name] = {
                "description": test_info["description"],
                "c_file": c_file,
                "wasm_file": wasm_file,
                "compilation_success": False,
                "file_size": 0
            }
        
        manifest_file = self.bin_dir / "test_manifest.json"
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 生成测试清单: {manifest_file}")
        return manifest_file
    
    def generate_compile_script(self):
        """生成编译脚本"""
        compile_script = """#!/usr/bin/env python3
import os
import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime

class TestCompiler:
    def __init__(self, clang_path="clang", bin_dir="WARD_bin", test_dir="tests"):
        self.clang_path = clang_path
        self.bin_dir = Path(bin_dir)
        self.test_dir = Path(test_dir)
        self.bin_dir.mkdir(exist_ok=True)
        
    def compile_test(self, c_file, wasm_file):
        \"\"\"编译单个测试文件\"\"\"
        cmd = [
            self.clang_path,
            "--target=wasm32-unknown-unknown",
            "-O1",
            "-nostdlib",
            "-Wl,--no-entry",
            "-Wl,--export-all",
            "-Wl,--allow-undefined",
            "-mbulk-memory",
            "-Wno-everything",
            "-o", str(wasm_file),
            str(c_file)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            success = result.returncode == 0 and wasm_file.exists()
            return success, result.stderr if not success else ""
        except Exception as e:
            return False, str(e)
    
    def update_manifest(self, manifest):
        \"\"\"更新测试清单\"\"\"
        for test_name, test_info in manifest["tests"].items():
            c_file = Path(test_info["c_file"])
            wasm_file = Path(test_info["wasm_file"])
            
            if c_file.exists():
                print(f"编译 {test_name}...")
                success, error = self.compile_test(c_file, wasm_file)
                
                manifest["tests"][test_name]["compilation_success"] = success
                if success:
                    file_size = wasm_file.stat().st_size if wasm_file.exists() else 0
                    manifest["tests"][test_name]["file_size"] = file_size
                    print(f"  ✅ 成功 - {file_size} bytes")
                else:
                    print(f"  ❌ 失败: {error}")
            else:
                print(f"  ❌ 源文件不存在: {c_file}")
                manifest["tests"][test_name]["compilation_success"] = False
        
        return manifest
    
    def compile_all(self):
        \"\"\"编译所有测试\"\"\"
        # 加载清单
        manifest_file = self.bin_dir / "test_manifest.json"
        if not manifest_file.exists():
            print("❌ 测试清单不存在")
            return False
            
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)
        
        print("开始编译测试程序...")
        print("=" * 50)
        
        # 更新清单
        manifest = self.update_manifest(manifest)
        manifest["generated_at"] = datetime.now().isoformat()
        
        # 保存更新的清单
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # 统计结果
        total = len(manifest["tests"])
        success = sum(1 for t in manifest["tests"].values() if t["compilation_success"])
        
        print("=" * 50)
        print(f"编译完成: {success}/{total} 成功")
        
        return success > 0

def main():
    compiler = TestCompiler()
    if compiler.compile_all():
        print("✅ 编译完成")
    else:
        print("❌ 编译失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""
        
        script_file = Path("compile_WARD_tests.py")
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(compile_script)
        
        # 设置执行权限
        script_file.chmod(0o755)
        print(f"✅ 生成编译脚本: {script_file}")
        return script_file
    
    def generate_all(self):
        """生成所有文件"""
        print("WARDuino内存安全测试程序生成器")
        print("=" * 60)
        
        # 生成测试文件
        generated_files = self.generate_test_files()
        print(f"\\n📁 共生成 {len(generated_files)} 个测试文件")
        
        # 生成清单文件
        self.generate_manifest()
        
        # 生成编译脚本
        self.generate_compile_script()
        
        print("\\n" + "=" * 60)
        print("✅ 所有文件生成完成！")
        print("\\n下一步操作：")
        print("1. 运行编译脚本: python3 compile_WARD_tests.py")
        print("2. 运行测试: python3 run_warduino_tests.py")
        print("\\n生成的测试类型：")
        for test_name in self.test_templates.keys():
            print(f"  • {test_name}")

def main():
    generator = TestGenerator()
    generator.generate_all()

if __name__ == "__main__":
    main()
