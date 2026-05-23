#!/usr/bin/env python3
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
        """编译单个测试文件"""
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
        """更新测试清单"""
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
        """编译所有测试"""
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
