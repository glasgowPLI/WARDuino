#!/usr/bin/env python3
import os
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

class WarduinoTestRunner:
    def __init__(self, warduino_path, bin_dir="WARD_bin", timeout=10):
        self.warduino_path = Path(warduino_path)
        self.bin_dir = Path(bin_dir)
        self.timeout = timeout
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
            result = subprocess.run(
                [str(self.warduino_path), "--help"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 or "usage" in result.stdout.lower():
                return True, "WARDuino可用"
            return False, f"WARDuino验证失败: {result.stderr}"
        except Exception as e:
            return False, f"WARDuino执行错误: {e}"
    
    def run_warduino_test(self, wasm_file, test_name):
        """使用WARDuino运行测试"""
        if not wasm_file.exists():
            return {
                "stdout": "",
                "stderr": f"文件不存在: {wasm_file}",
                "returncode": -1,
                "file_error": True
            }
        
        try:
            cmd = [str(self.warduino_path), str(wasm_file)]
            
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
                "returncode": result.returncode,
                "args": cmd
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
    
    def analyze_warduino_result(self, test_name, result):
        """分析WARDuino测试结果"""
        output = result["stdout"] + " " + result["stderr"]
        returncode = result["returncode"]
        output_lower = output.lower()
        
        # 检查文件错误
        if result.get("file_error"):
            return "FILE_ERROR", result["stderr"]
        elif result.get("timeout"):
            return "TIMEOUT", "执行超时"
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
            "panic": "PANIC"
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
        """运行所有测试"""
        print("开始WARDuino安全测试...")
        print(f"WARDuino路径: {self.warduino_path}")
        print("=" * 60)
        
        # 检查WARDuino
        warduino_ok, warduino_msg = self.check_warduino()
        if not warduino_ok:
            print(f"❌ {warduino_msg}")
            return False
        print(f"✅ {warduino_msg}")
        
        # 加载清单
        manifest = self.load_manifest()
        
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
            print(f"文件: {wasm_file}")
            
            # 运行测试
            result = self.run_warduino_test(wasm_file, test_name)
            
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
                "file_size": test_info.get('file_size', 0)
            }
            
            self.test_results[test_name] = test_result
            
            # 显示结果
            if status in ["BOUNDS_ERROR", "MEMORY_ACCESS", "TRAP", "SEGFAULT"]:
                status_icon = "✅"
                result_type = "安全机制生效"
            elif status == "COMPLETED":
                status_icon = "⚠️" 
                result_type = "正常完成（可能存在漏洞）"
            elif status == "SILENT_ERROR":
                status_icon = "🔍"
                result_type = "静默错误"
            else:
                status_icon = "❓"
                result_type = "需要分析"
            
            print(f"{status_icon} 结果: {status} - {details}")
            print(f"   类型: {result_type}")
            
            if result.get('stderr'):
                error_preview = result['stderr'].replace('\n', ' ').strip()[:100]
                if error_preview:
                    print(f"   错误: {error_preview}...")
        
        return True
    
    def generate_report(self):
        """生成测试报告"""
        total = len(self.test_results)
        security_triggered = sum(1 for r in self.test_results.values() 
                               if r["status"] in ["BOUNDS_ERROR", "MEMORY_ACCESS", "TRAP", "SEGFAULT"])
        
        report = {
            "platform": "WARDuino",
            "timestamp": datetime.now().isoformat(),
            "warduino_path": str(self.warduino_path),
            "results": self.test_results,
            "summary": {
                "total_tests": total,
                "security_mechanisms_triggered": security_triggered,
                "detection_rate": round(security_triggered / total * 100, 2) if total > 0 else 0
            }
        }
        
        # 保存报告
        report_file = f"warduino_security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w", encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report, report_file
    
    def print_summary(self, report):
        """打印总结"""
        summary = report['summary']
        
        print("\n" + "=" * 60)
        print("WARDuino安全测试总结")
        print("=" * 60)
        print(f"总计测试: {summary['total_tests']}")
        print(f"安全机制触发: {summary['security_mechanisms_triggered']}")
        print(f"检测率: {summary['detection_rate']}%")
        
        print(f"\n详细结果:")
        for test_name, result in report['results'].items():
            icon = "✅" if result["status"] in ["BOUNDS_ERROR", "MEMORY_ACCESS", "TRAP"] else "⚠️"
            print(f"  {icon} {test_name}: {result['status']}")

def main():
    print("WARDuino安全测试框架")
    print("=" * 50)
    
    # WARDuino路径
    warduino_path = Path("../WARDuino/build-emu/wdcli")
    if not warduino_path.exists():
        print(f"❌ WARDuino未找到: {warduino_path}")
        return
    
    print(f"✅ 找到WARDuino: {warduino_path}")
    
    # 创建测试运行器
    runner = WarduinoTestRunner(warduino_path=warduino_path, timeout=15)
    
    try:
        # 运行测试
        success = runner.run_test_suite()
        
        if success:
            # 生成报告
            report, report_file = runner.generate_report()
            runner.print_summary(report)
            print(f"\n📄 报告已保存: {report_file}")
            
    except Exception as e:
        print(f"测试错误: {e}")

if __name__ == "__main__":
    main()
