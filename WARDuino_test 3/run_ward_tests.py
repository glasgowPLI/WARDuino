#!/usr/bin/env python3
# run_tests.py - 运行WASM测试并生成安全报告（WARDuino版本）

import os
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

class WARDuinoTestRunner:
    def __init__(self, wdcli_path, test_dir="ward_tests", timeout=5):
        self.wdcli_path = Path(wdcli_path)
        self.test_dir = Path(test_dir)
        self.report_dir = self.test_dir / "report"
        self.timeout = timeout
        self.test_results = {}
        
        # 确保报告目录存在
        self.report_dir.mkdir(exist_ok=True)
    
    def check_warduino(self):
        """检查WARDuino是否可用"""
        if not self.wdcli_path.exists():
            return False, f"WARDuino wdcli不存在: {self.wdcli_path}"
        
        try:
            # 尝试运行WARDuino --help
            result = subprocess.run(
                [str(self.wdcli_path), "--help"],
                capture_output=True, 
                text=True, 
                timeout=2
            )
            
            if result.returncode == 0 or "warduino" in result.stdout.lower() or "warduino" in result.stderr.lower():
                return True, "WARDuino可用"
            else:
                return False, f"WARDuino返回异常: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return True, "WARDuino运行但超时（可能正常）"
        except Exception as e:
            return False, f"WARDuino执行错误: {e}"
    
    def run_warduino_test(self, wasm_file, entry_point="_start"):
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
            # 运行WARDuino wdcli，使用--no-debug和--invoke参数
            cmd = [
                str(self.wdcli_path),
                
                str(wasm_file),
                "--no-debug",
                "--invoke", entry_point
            ]
            
            result = subprocess.run(
                cmd,
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
        elif "division by zero" in output_lower:
            return "DIVISION_BY_ZERO", "除零错误"
        elif "integer overflow" in output_lower:
            return "INTEGER_OVERFLOW", "整数溢出"
        elif "null pointer" in output_lower:
            return "NULL_POINTER", "空指针解引用"
        elif returncode == 0:
            return "COMPLETED", "正常完成"
        elif returncode != 0:
            return "NON_ZERO_EXIT", f"非零退出码: {returncode}"
        else:
            return "UNKNOWN", "无法确定结果"
    
    def run_test_suite(self):
        """运行所有测试"""
        print("开始WARDuino安全测试...")
        print(f"WARDuino路径: {self.wdcli_path}")
        print(f"测试目录: {self.test_dir}")
        print(f"报告目录: {self.report_dir}")
        print(f"超时设置: {self.timeout}秒")
        print("=" * 60)
        
        # 检查WARDuino
        warduino_ok, warduino_msg = self.check_warduino()
        if not warduino_ok:
            print(f"❌ {warduino_msg}")
            return False
        print(f"✅ {warduino_msg}")
        print()
        
        # 定义要测试的模块列表
        test_modules = [
            # 基础功能测试
            ("compute_test.wasm", "_start"),
            ("control_test.wasm", "_start"),
            ("memory_test.wasm", "_start"),
            
            # 内存安全测试
            ("oob_read.wasm", "_start"),
            ("oob_write.wasm", "_start"),
            ("stack_overflow.wasm", "_start"),
            
            # 其他安全测试
            ("test_Buffer_Underflow.wasm", "_start"),
            ("test_Division_By_Zero.wasm", "_start"),
            ("test_Double_Free.wasm", "_start"),
            ("test_Double_Free_Simulation.wasm", "_start"),
            ("test_Format_String_Simulation.wasm", "_start"),
            ("test_Heap_Overflow.wasm", "_start"),
            ("test_Infinite_Loop.wasm", "_start"),
            ("test_Integer_Overflow.wasm", "_start"),
            ("test_Memory_Access.wasm", "_start"),
            ("test_Memory_Alignment.wasm", "_start"),
            ("test_Null_Pointer_Dereference.wasm", "_start"),
            ("test_OOB_Read.wasm", "_start"),
            ("test_OOB_Write.wasm", "_start"),
        ]
        
        print(f"测试数量: {len(test_modules)}")
        
        for wasm_file, entry_point in test_modules:
            test_name = Path(wasm_file).stem
            wasm_path = self.test_dir / wasm_file
            
            print(f"测试: {test_name}")
            print(f"入口点: {entry_point}")
            
            if not wasm_path.exists():
                print(f"❌ 文件不存在: {wasm_path}")
                self.test_results[test_name] = {
                    "status": "FILE_NOT_FOUND",
                    "details": f"文件不存在: {wasm_path}",
                    "timestamp": datetime.now().isoformat()
                }
                continue
            
            file_size = wasm_path.stat().st_size
            print(f"文件: {wasm_path} ({file_size} bytes)")
            
            # 运行测试
            result = self.run_warduino_test(wasm_path, entry_point)
            
            # 分析结果
            status, details = self.analyze_result(test_name, result)
            
            # 记录结果
            test_result = {
                "status": status,
                "details": details,
                "returncode": result.get("returncode", 0),
                "stdout": result.get("stdout", "")[:500],
                "stderr": result.get("stderr", "")[:500],
                "timestamp": datetime.now().isoformat(),
                "file_size": file_size,
                "entry_point": entry_point
            }
            
            self.test_results[test_name] = test_result
            
            # 显示结果
            if status in ["TRAPPED", "ERROR", "SEGFAULT", "EXCEPTION", "BOUNDS_ERROR", 
                         "MEMORY_ACCESS_ERROR", "DIVISION_BY_ZERO", "INTEGER_OVERFLOW", "NULL_POINTER"]:
                status_icon = "✅"
                result_type = "安全机制生效"
            elif status == "COMPLETED":
                status_icon = "⚠️"
                result_type = "可能漏洞未检测"
            elif status == "TIMEOUT":
                status_icon = "⏱️"
                result_type = "执行超时"
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
            time.sleep(0.1)  # 短暂延迟
        
        return True
    
    def generate_report(self):
        """生成详细测试报告"""
        # 统计结果
        total = len(self.test_results)
        security_triggered = sum(1 for r in self.test_results.values() if r["status"] in [
            "TRAPPED", "ERROR", "SEGFAULT", "EXCEPTION", "BOUNDS_ERROR", 
            "MEMORY_ACCESS_ERROR", "DIVISION_BY_ZERO", "INTEGER_OVERFLOW", "NULL_POINTER"
        ])
        completed = sum(1 for r in self.test_results.values() if r["status"] == "COMPLETED")
        timeouts = sum(1 for r in self.test_results.values() if r["status"] == "TIMEOUT")
        failed = sum(1 for r in self.test_results.values() if r["status"] in ["FILE_NOT_FOUND", "FILE_ERROR", "INVALID_WASM"])
        other = total - (security_triggered + completed + timeouts + failed)
        
        report = {
            "platform": "WARDuino",
            "timestamp": datetime.now().isoformat(),
            "wdcli_path": str(self.wdcli_path),
            "timeout": self.timeout,
            "test_environment": {
                "test_directory": str(self.test_dir),
                "report_directory": str(self.report_dir),
                "total_tests": total
            },
            "results": self.test_results,
            "summary": {
                "total_tests": total,
                "security_mechanisms_triggered": security_triggered,
                "completed_normally": completed,
                "timeouts": timeouts,
                "failed_tests": failed,
                "other_results": other
            },
            "security_effectiveness": {
                "detection_rate": round(security_triggered / total * 100, 2) if total > 0 else 0,
                "successful_tests": total - failed
            }
        }
        
        # 保存报告到ward_tests/report目录
        report_file = self.report_dir / f"warduino_security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w", encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report, report_file
    
    def print_detailed_summary(self, report):
        """打印详细总结"""
        summary = report['summary']
        effectiveness = report['security_effectiveness']
        
        print("=" * 60)
        print("WARDuino安全测试详细总结")
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
            if result["status"] in ["TRAPPED", "ERROR", "SEGFAULT", "EXCEPTION", "BOUNDS_ERROR", 
                                   "MEMORY_ACCESS_ERROR", "DIVISION_BY_ZERO", "INTEGER_OVERFLOW", "NULL_POINTER"]:
                icon = "✅"
            elif result["status"] == "COMPLETED":
                icon = "⚠️"
            elif result["status"] in ["TIMEOUT", "FILE_NOT_FOUND", "FILE_ERROR", "INVALID_WASM"]:
                icon = "❌"
            else:
                icon = "❓"
            
            print(f"   {icon} {test_name}: {result['status']} - {result['details']}")

def find_warduino():
    """查找WARDuino wdcli可执行文件"""
    possible_paths = [
        "~/WARDuino/build-emu/wdcli",
        "../WARDuino/build-emu/wdcli",
        "wdcli",
        "/usr/local/bin/wdcli",
        "./wdcli"
    ]
    
    for path in possible_paths:
        expanded_path = Path(path).expanduser()
        if expanded_path.exists() and os.access(expanded_path, os.X_OK):
            return expanded_path
    
    return None

def main():
    print("WARDuino安全测试框架")
    print("=" * 40)
    
    # 查找WARDuino wdcli
    wdcli_path = find_warduino()
    if not wdcli_path:
        print("❌ 未找到WARDuino wdcli可执行文件")
        print("请确保WARDuino已编译且在以下路径之一:")
        print(" - ~/WARDuino/build-emu/wdcli")
        print(" - ../WARDuino/build-emu/wdcli")
        print(" - 当前目录的wdcli")
        print(" - /usr/local/bin/wdcli")
        return
    
    print(f"✅ 找到WARDuino wdcli: {wdcli_path}")
    
    if not os.path.exists("ward_tests"):
        print("❌ ward_tests目录不存在")
        print("请确保测试WASM文件在ward_tests目录中")
        return
    
    # 创建测试运行器
    runner = WARDuinoTestRunner(wdcli_path=wdcli_path, timeout=5)
    
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
