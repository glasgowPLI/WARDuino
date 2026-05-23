#!/usr/bin/env python3
# run_tests.py - 运行WASM测试并生成安全报告（wasmtime版本）

import os
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

class wasmtimeTestRunner:
    def __init__(self, wasmtime_path, bin_dir="WARD_bin", timeout=10):
        self.wasmtime_path = Path(wasmtime_path)
        self.bin_dir = Path(bin_dir)
        self.timeout = timeout
        self.test_results = {}
        
        # 加载测试清单
        self.manifest = self.load_manifest()
    
    def load_manifest(self):
        """加载测试清单"""
        manifest_file = self.bin_dir / "test_manifest.json"
        if not manifest_file.exists():
            raise FileNotFoundError(f"测试清单文件不存在: {manifest_file}")
        
        with open(manifest_file, 'r') as f:
            return json.load(f)
    
    def check_wasmtime(self):
        """检查wasmtime是否可用"""
        if not self.wasmtime_path.exists():
            return False, f"wasmtime不存在: {self.wasmtime_path}"
        
        try:
            # 尝试运行wasmtime --version或--help
            result = subprocess.run(
                [str(self.wasmtime_path), "--version"],
                capture_output=True, 
                text=True, 
                timeout=2
            )
            
            if result.returncode == 0 or "wasmtime" in result.stdout.lower() or "wasmtime" in result.stderr.lower():
                return True, "wasmtime可用"
            else:
                # 尝试运行空文件测试
                test_wasm = self.bin_dir / "test_dummy.wasm"
                if not test_wasm.exists():
                    # 创建最小测试文件
                    with open(test_wasm, 'wb') as f:
                        f.write(b'\x00asm\x01\x00\x00\x00')
                
                result = subprocess.run(
                    [str(self.wasmtime_path), str(test_wasm)],
                    capture_output=True, 
                    text=True, 
                    timeout=2
                )
                return True, "wasmtime可用"
                
        except subprocess.TimeoutExpired:
            return True, "wasmtime运行但超时（可能正常）"
        except Exception as e:
            return False, f"wasmtime执行错误: {e}"
    
    def run_wasmtime_test(self, wasm_file):
        """运行单个WASM测试"""
        if not os.path.exists(wasm_file):
            return {
                "stdout": "",
                "stderr": f"文件不存在: {wasm_file}",
                "returncode": -1,
                "file_error": True
            }
        
        file_size = os.path.getsize(wasm_file)
        if file_size < 10:
            return {
                "stdout": "",
                "stderr": f"文件太小({file_size} bytes)，可能无效",
                "returncode": -1,
                "file_error": True
            }
        
        try:
            # 运行wasmtime，捕获所有输出
            result = subprocess.run(
                [str(self.wasmtime_path), str(wasm_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": "执行超时",
                "returncode": -1,
                "timeout": True
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "error": True
            }
    
    def analyze_result(self, test_name, result):
        """分析测试结果"""
        output = result["stdout"] + " " + result["stderr"]
        returncode = result["returncode"]
        
        # 关键字匹配（不区分大小写）
        output_lower = output.lower()
        
        if result.get("file_error"):
            return "FILE_ERROR", result["stderr"]
        elif result.get("timeout"):
            return "TIMEOUT", "执行超时"
        elif result.get("error"):
            return "RUNTIME_ERROR", f"运行时错误: {result['stderr']}"
        elif "trap" in output_lower:
            return "TRAPPED", "WASM陷阱触发 - 安全机制生效"
        elif "error" in output_lower:
            return "ERROR", "检测到错误"
        elif "segfault" in output_lower or "segmentation" in output_lower:
            return "SEGFAULT", "分段错误"
        elif "exception" in output_lower:
            return "EXCEPTION", "异常发生"
        elif "panic" in output_lower:
            return "PANIC", "系统恐慌"
        elif "abort" in output_lower:
            return "ABORT", "程序中止"
        elif "invalid" in output_lower and "wasm" in output_lower:
            return "INVALID_WASM", "无效的WASM文件"
        elif "out of bounds" in output_lower or "bounds" in output_lower:
            return "BOUNDS_ERROR", "边界检查错误"
        elif "memory access" in output_lower:
            return "MEMORY_ACCESS_ERROR", "内存访问错误"
        elif returncode == 0:
            return "COMPLETED", "正常完成（可能安全机制未生效）"
        elif returncode != 0:
            return "NON_ZERO_EXIT", f"非零退出码: {returncode}"
        else:
            return "UNKNOWN", "无法确定结果"
    
    def run_test_suite(self):
        """运行所有测试"""
        print("开始wasmtime安全测试...")
        print(f"wasmtime路径: {self.wasmtime_path}")
        print(f"超时设置: {self.timeout}秒")
        print(f"测试数量: {len(self.manifest['tests'])}")
        print("=" * 60)
        
        # 检查wasmtime
        wasmtime_ok, wasmtime_msg = self.check_wasmtime()
        if not wasmtime_ok:
            print(f"❌ {wasmtime_msg}")
            return False
        print(f"✅ {wasmtime_msg}")
        print()
        
        for test_name, test_info in self.manifest['tests'].items():
            print(f"测试: {test_name}")
            print(f"描述: {test_info['description']}")
            
            if not test_info['compilation_success']:
                print("❌ 跳过: 编译失败")
                self.test_results[test_name] = {
                    "status": "COMPILE_FAILED",
                    "details": "WASM编译失败",
                    "timestamp": datetime.now().isoformat()
                }
                continue
            
            wasm_file = test_info['wasm_file']
            file_size = test_info.get('file_size', 0)
            print(f"文件: {wasm_file} ({file_size} bytes)")
            
            # 运行测试
            result = self.run_wasmtime_test(wasm_file)
            
            # 分析结果
            status, details = self.analyze_result(test_name, result)
            
            # 记录结果
            test_result = {
                "status": status,
                "details": details,
                "returncode": result.get("returncode", 0),
                "stdout": result.get("stdout", "")[:300],  # 限制输出长度
                "stderr": result.get("stderr", "")[:300],
                "timestamp": datetime.now().isoformat(),
                "file_size": file_size
            }
            
            self.test_results[test_name] = test_result
            
            # 显示结果
            if status in ["TRAPPED", "ERROR", "SEGFAULT", "EXCEPTION", "BOUNDS_ERROR", "MEMORY_ACCESS_ERROR"]:
                status_icon = "✅"
                result_type = "安全机制生效"
            elif status == "COMPLETED":
                status_icon = "⚠️"
                result_type = "可能漏洞未检测"
            else:
                status_icon = "❌"
                result_type = "测试异常"
            
            print(f"{status_icon} 结果: {status} - {details} ({result_type})")
            
            # 显示部分输出（如果有）
            if result.get('stdout'):
                output_preview = result['stdout'].replace('\n', ' ').strip()
                if output_preview:
                    print(f"   输出: {output_preview[:100]}...")
            if result.get('stderr') and not result.get('file_error'):
                error_preview = result['stderr'].replace('\n', ' ').strip()
                if error_preview:
                    print(f"   错误: {error_preview[:100]}...")
            
            print()
            time.sleep(0.5)  # 测试间延迟
        
        return True
    
    def generate_report(self):
        """生成详细测试报告"""
        # 统计结果
        total = len(self.test_results)
        trapped = sum(1 for r in self.test_results.values() if r["status"] == "TRAPPED")
        errors = sum(1 for r in self.test_results.values() if r["status"] in ["ERROR", "SEGFAULT", "EXCEPTION", "BOUNDS_ERROR", "MEMORY_ACCESS_ERROR"])
        completed = sum(1 for r in self.test_results.values() if r["status"] == "COMPLETED")
        timeouts = sum(1 for r in self.test_results.values() if r["status"] == "TIMEOUT")
        failed = sum(1 for r in self.test_results.values() if r["status"] in ["COMPILE_FAILED", "FILE_ERROR", "INVALID_WASM"])
        other = total - (trapped + errors + completed + timeouts + failed)
        
        report = {
            "platform": "wasmtime",
            "timestamp": datetime.now().isoformat(),
            "wasmtime_path": str(self.wasmtime_path),
            "timeout": self.timeout,
            "test_environment": {
                "manifest_generated": self.manifest['generated_at'],
                "total_tests": total
            },
            "results": self.test_results,
            "summary": {
                "total_tests": total,
                "security_mechanisms_triggered": trapped + errors,
                "trapped": trapped,
                "errors": errors,
                "completed_normally": completed,
                "timeouts": timeouts,
                "failed_tests": failed,
                "other_results": other
            },
            "security_effectiveness": {
                "detection_rate": round((trapped + errors) / total * 100, 2) if total > 0 else 0,
                "successful_tests": total - failed
            }
        }
        
        # 保存报告
        report_file = f"wasmtime_security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w", encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report, report_file
    
    def print_detailed_summary(self, report):
        """打印详细总结"""
        summary = report['summary']
        effectiveness = report['security_effectiveness']
        
        print("=" * 60)
        print("wasmtime安全测试详细总结")
        print("=" * 60)
        
        print(f"📊 测试统计:")
        print(f"   总计测试: {summary['total_tests']}")
        print(f"   ✅ 安全机制触发: {summary['security_mechanisms_triggered']}")
        print(f"   ⚠️  正常完成: {summary['completed_normally']}")
        print(f"   ⏱️  超时: {summary['timeouts']}")
        print(f"   ❌ 失败: {summary['failed_tests']}")
        print(f"   ❓ 其他: {summary['other_results']}")
        
        print(f"\n🛡️  安全效果:")
        print(f"   检测率: {effectiveness['detection_rate']}%")
        print(f"   有效测试: {effectiveness['successful_tests']}")
        
        print(f"\n📋 详细结果:")
        for test_name, result in report['results'].items():
            if result["status"] in ["TRAPPED", "ERROR", "SEGFAULT", "EXCEPTION", "BOUNDS_ERROR", "MEMORY_ACCESS_ERROR"]:
                icon = "✅"
            elif result["status"] == "COMPLETED":
                icon = "⚠️"
            elif result["status"] in ["TIMEOUT", "COMPILE_FAILED", "FILE_ERROR", "INVALID_WASM"]:
                icon = "❌"
            else:
                icon = "❓"
            
            print(f"   {icon} {test_name}: {result['status']} - {result['details']}")

def find_wasmtime():
    """查找wasmtime可执行文件"""
    possible_paths = [
               "../wasmtime-secure/wasmtime",
               "/opt/wasmtime-secure/wasmtime"
    ]
    
    for path in possible_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
    
    return None

def main():
    print("wasmtime安全测试框架")
    print("=" * 40)
    
    # 查找wasmtime
    wasmtime_path = find_wasmtime()
    print(wasmtime_path)
    if not wasmtime_path:
        print("❌ 未找到wasmtime可执行文件")
        print("请确保wasmtime已编译且在以下路径之一:")
        print(" - ../wasmtime/build/wasmtime")
        print(" - ../wasmtime/wasmtime")
        print(" - 当前目录的wasmtime")
        print(" - /usr/local/bin/wasmtime")
        return
    
    print(f"✅ 找到wasmtime: {wasmtime_path}")
    
    if not os.path.exists("WARD_bin"):
        print("❌ WARD_bin目录不存在")
        print("请先运行 generate_tests.py 生成测试文件")
        return
    
    # 创建测试运行器
    runner = wasmtimeTestRunner(wasmtime_path=wasmtime_path, timeout=10)
    
    try:
        # 运行测试
        success = runner.run_test_suite()
        
        if success:
            # 生成报告
            report, report_file = runner.generate_report()
            
            # 显示总结
            runner.print_detailed_summary(report)
            print(f"\n📄 详细报告已保存: {report_file}")
        else:
            print("测试运行失败")
            
    except Exception as e:
        print(f"测试过程中发生错误: {e}")

if __name__ == "__main__":
    main()
