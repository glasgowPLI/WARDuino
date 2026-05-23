#!/usr/bin/env python3
import os
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

class WarduinoTestRunner:
    def __init__(self, warduino_path, bin_dir="WARD_bin", timeout=15, debug=False):
        self.warduino_path = Path(warduino_path)
        self.bin_dir = Path(bin_dir)
        self.timeout = timeout
        self.debug = debug
        self.test_results = {}
        
    def load_manifest(self):
        """加载测试清单"""
        manifest_file = self.bin_dir / "test_manifest.json"
        if not manifest_file.exists():
            raise FileNotFoundError(f"测试清单文件不存在: {manifest_file}")
        
        with open(manifest_file, 'r') as f:
            return json.load(f)
    
    def check_warduino(self):
        """检查WARDuino是否可用"""
        if not self.warduino_path.exists():
            return False, f"WARDuino不存在: {self.warduino_path}"
        
        try:
            # 测试WARDuino基本功能
            test_wasm = self.bin_dir / "test_simple.wasm"
            if not test_wasm.exists():
                # 创建一个简单的测试WASM
                self.create_simple_test()
            
            result = subprocess.run(
                [str(self.warduino_path), str(test_wasm),"--no-debug","--invoke","_start"],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0 or "error" not in result.stderr.lower():
                return True, "WARDuino可用"
            return False, f"WARDuino验证失败: {result.stderr}"
        except Exception as e:
            return False, f"WARDuino执行错误: {e}"
    
    def create_simple_test(self):
        """创建一个简单的测试WASM来验证WARDuino"""
        simple_c = """
void simple_test() {
    volatile int x = 42;
}

void _start() {
    simple_test();
}
"""
        simple_file = self.bin_dir / "test_simple.c"
        with open(simple_file, 'w') as f:
            f.write(simple_c)
        
        # 编译简单测试
        cmd = [
            "clang", "--target=wasm32-unknown-unknown", "-O1", "-nostdlib",
            "-Wl,--no-entry", "-Wl,--export-all", "-Wl,--allow-undefined",
            "-o", str(self.bin_dir / "test_simple.wasm"), str(simple_file)
        ]
        subprocess.run(cmd, capture_output=True)
    
    def run_warduino_test(self, wasm_file, test_name):
        """使用WARDuino运行测试，增加调试选项"""
        if not wasm_file.exists():
            return {
                "stdout": "",
                "stderr": f"文件不存在: {wasm_file}",
                "returncode": -1,
                "file_error": True
            }
        
        try:
            # 尝试不同的WARDuino运行选项
            base_cmd = [str(self.warduino_path)]
            
            base_cmd.append(str(wasm_file))
            # 添加调试选项
            if self.debug:
                base_cmd.extend(["--no-debug","--invoke","_start"])
            
            
            
            print(f"   执行命令: {' '.join(base_cmd)}")
            
            result = subprocess.run(
                base_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "args": base_cmd
            }
            
        except subprocess.TimeoutExpired:
            if self.debug:
                print(f"   超时详情: 测试 {test_name} 在 {self.timeout} 秒后超时")
            return {
                "stdout": "",
                "stderr": f"执行超时 ({self.timeout}秒)",
                "returncode": -1,
                "timeout": True
            }
        except Exception as e:
            if self.debug:
                print(f"   异常详情: {e}")
            return {
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "error": True
            }
    
    def analyze_warduino_result(self, test_name, result):
        """分析WARDuino测试结果，特别处理超时情况"""
        output = result["stdout"] + " " + result["stderr"]
        returncode = result["returncode"]
        output_lower = output.lower()
        
        # 检查文件错误
        if result.get("file_error"):
            return "FILE_ERROR", result["stderr"]
        elif result.get("timeout"):
            # 分析超时原因
            if test_name == "Infinite_Loop":
                return "TIMEOUT_EXPECTED", "无限循环测试正常超时"
            elif test_name == "Stack_Overflow":
                return "STACK_OVERFLOW_TIMEOUT", "栈溢出可能导致超时"
            else:
                return "TIMEOUT", f"执行超时，可能由于资源限制"
        elif result.get("error"):
            return "RUNTIME_ERROR", f"运行时错误: {result['stderr']}"
        
        # WARDuino特定错误模式
        warduino_errors = {
            "out of bounds": "BOUNDS_ERROR",
            "memory access": "MEMORY_ACCESS", 
            "segmentation fault": "SEGFAULT",
            "trap": "TRAP",
            "exception": "EXCEPTION",
            "error": "ERROR",
            "panic": "PANIC",
            "timeout": "EXECUTION_TIMEOUT"
        }
        
        for pattern, error_type in warduino_errors.items():
            if pattern in output_lower:
                return error_type, f"检测到{pattern}"
        
        # 分析返回码
        if returncode == 0:
            if "error" in output_lower or "exception" in output_lower:
                return "SILENT_ERROR", "退出码为0但输出包含错误"
            return "COMPLETED", "正常完成"
        else:
            return "NON_ZERO_EXIT", f"非零退出码: {returncode}"
    
    def run_test_suite(self):
        """运行所有测试，增加超时诊断"""
        print("开始WARDuino安全测试...")
        print(f"WARDuino路径: {self.warduino_path}")
        print(f"超时设置: {self.timeout}秒")
        print(f"调试模式: {self.debug}")
        print("=" * 60)
        
        # 检查WARDuino
        warduino_ok, warduino_msg = self.check_warduino()
        if not warduino_ok:
            print(f"❌ {warduino_msg}")
            return False
        print(f"✅ {warduino_msg}")
        
        # 加载清单
        manifest = self.load_manifest()
        
        # 先测试一个简单程序
        print("🧪 测试简单WASM程序...")
        simple_result = self.run_warduino_test(
            self.bin_dir / "test_simple.wasm", "SIMPLE_TEST"
        )
        if simple_result.get("timeout"):
            print("⚠️  简单测试也超时，可能是WARDuino配置问题")
        else:
            print("✅ 简单测试通过")
        
        print("\n" + "=" * 60)
        
        for test_name, test_info in manifest['tests'].items():
            print(f"\n测试: {test_name}")
            print(f"描述: {test_info['description']}")
            
            if not test_info['compilation_success']:
                print("❌ 跳过: 编译失败")
                self.test_results[test_name] = {
                    "status": "COMPILE_FAILED",
                    "details": "WASM编译失败",
                    "timestamp": datetime.now().isoformat()
                }
                continue
            
            wasm_file = Path(test_info['wasm_file'])
            print(f"文件: {wasm_file} ({test_info.get('file_size', 0)} bytes)")
            
            # 根据测试类型调整超时
            test_timeout = self.timeout
            if test_name in ["Infinite_Loop", "Stack_Overflow"]:
                test_timeout = min(5, self.timeout)  # 更短的超时用于检测性测试
            
            # 运行测试
            original_timeout = self.timeout
            self.timeout = test_timeout
            result = self.run_warduino_test(wasm_file, test_name)
            self.timeout = original_timeout
            
            # 分析结果
            status, details = self.analyze_warduino_result(test_name, result)
            
            # 记录结果
            test_result = {
                "status": status,
                "details": details,
                "returncode": result.get("returncode", 0),
                "stdout": result.get("stdout", "")[:500],
                "stderr": result.get("stderr", "")[:500],
                "timestamp": datetime.now().isoformat(),
                "file_size": test_info.get('file_size', 0),
                "timeout_used": test_timeout
            }
            
            self.test_results[test_name] = test_result
            
            # 显示结果
            if status in ["BOUNDS_ERROR", "MEMORY_ACCESS", "TRAP", "SEGFAULT", "TIMEOUT_EXPECTED"]:
                status_icon = "✅"
                result_type = "安全机制生效或符合预期"
            elif "TIMEOUT" in status:
                status_icon = "⏱️"
                result_type = "执行超时"
            elif status == "COMPLETED":
                status_icon = "⚠️" 
                result_type = "正常完成（可能需要检查）"
            elif status == "SILENT_ERROR":
                status_icon = "🔍"
                result_type = "静默错误"
            else:
                status_icon = "❓"
                result_type = "需要分析"
            
            print(f"{status_icon} 结果: {status} - {details}")
            print(f"   类型: {result_type}")
            print(f"   使用超时: {test_timeout}秒")
            
            if result.get('stderr'):
                error_preview = result['stderr'].replace('\n', ' ').strip()[:150]
                if error_preview:
                    print(f"   错误: {error_preview}...")
        
        return True
    
    def generate_report(self):
        """生成测试报告"""
        total = len(self.test_results)
        
        # 分类统计超时情况
        timeouts = sum(1 for r in self.test_results.values() if "TIMEOUT" in r["status"])
        expected_timeouts = sum(1 for r in self.test_results.values() if r["status"] == "TIMEOUT_EXPECTED")
        unexpected_timeouts = timeouts - expected_timeouts
        
        security_triggered = sum(1 for r in self.test_results.values() 
                               if r["status"] in ["BOUNDS_ERROR", "MEMORY_ACCESS", "TRAP", "SEGFAULT"])
        
        report = {
            "platform": "WARDuino",
            "timestamp": datetime.now().isoformat(),
            "warduino_path": str(self.warduino_path),
            "timeout_setting": self.timeout,
            "debug_mode": self.debug,
            "results": self.test_results,
            "summary": {
                "total_tests": total,
                "timeouts": timeouts,
                "expected_timeouts": expected_timeouts,
                "unexpected_timeouts": unexpected_timeouts,
                "security_mechanisms_triggered": security_triggered,
                "timeout_rate": round(timeouts / total * 100, 2) if total > 0 else 0
            },
            "diagnosis": {
                "all_timeouts": timeouts == total,
                "simple_test_works": Path(self.bin_dir / "test_simple.wasm").exists()
            }
        }
        
        # 保存报告
        report_file = f"./output/warduino_security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w", encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report, report_file
    
    def print_diagnostic_summary(self, report):
        """打印诊断总结"""
        summary = report['summary']
        diagnosis = report['diagnosis']
        
        print("\n" + "=" * 60)
        print("WARDuino测试诊断总结")
        print("=" * 60)
        
        print(f"📊 测试统计:")
        print(f"   总计测试: {summary['total_tests']}")
        print(f"   ⏱️  总超时: {summary['timeouts']}")
        print(f"   ✅ 预期超时: {summary['expected_timeouts']}")
        print(f"   ❓ 意外超时: {summary['unexpected_timeouts']}")
        print(f"   🛡️  安全机制触发: {summary['security_mechanisms_triggered']}")
        print(f"   📈 超时率: {summary['timeout_rate']}%")
        
        print(f"\n🔍 诊断信息:")
        if diagnosis['all_timeouts']:
            print("   ❗ 所有测试都超时，表明WARDuino配置可能有问题")
            print("   可能原因:")
            print("   • WARDuino内存限制过小")
            print("   • 需要特定的编译选项")
            print("   • 入口函数不兼容")
            print("   • WARDuino版本问题")
        
        if summary['unexpected_timeouts'] > 0:
            print(f"   ⚠️  有 {summary['unexpected_timeouts']} 个意外超时")
        
        print(f"\n💡 建议:")
        print("   1. 检查WARDuino版本和配置")
        print("   2. 尝试使用调试模式运行")
        print("   3. 调整编译选项")
        print("   4. 检查WASM文件是否兼容")

def main():
    print("WARDuino安全测试框架（诊断版）")
    print("=" * 50)
    
    # WARDuino路径
    warduino_path = Path("../WARDuino-safe/build-baseline/wdcli")
    if not warduino_path.exists():
        print(f"❌ WARDuino未找到: {warduino_path}")
        print("请确保WARDuino已正确编译")
        return
    
    print(f"✅ 找到WARDuino: {warduino_path}")
    
    # 使用调试模式
    debug_mode = True
    
    # 创建测试运行器（增加超时时间）
    runner = WarduinoTestRunner(
        warduino_path=warduino_path, 
        timeout=20,  # 增加超时时间
        debug=debug_mode
    )
    
    try:
        # 运行测试
        success = runner.run_test_suite()
        
        if success:
            # 生成报告
            report, report_file = runner.generate_report()
            runner.print_diagnostic_summary(report)
            print(f"\n📄 诊断报告已保存: {report_file}")
            
    except Exception as e:
        print(f"测试错误: {e}")

if __name__ == "__main__":
    main()
