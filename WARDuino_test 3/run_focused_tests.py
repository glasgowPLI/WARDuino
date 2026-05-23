#!/usr/bin/env python3
# run_focused_tests.py - 运行聚焦测试（只使用--no-debug配置）

import os
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

class FocusedWARDuinoTestRunner:
    def __init__(self, wdcli_path, test_dir="ward_tests", timeout=5):
        self.wdcli_path = Path(wdcli_path)
        self.test_dir = Path(test_dir)
        self.report_dir = self.test_dir / "report"
        self.timeout = timeout
        self.test_results = {}
        
        # 确保报告目录存在
        self.report_dir.mkdir(exist_ok=True)
    
    def find_wasm_files(self):
        """递归查找所有WASM文件"""
        wasm_files = []
        for root, dirs, files in os.walk(self.test_dir):
            if "report" in root:
                continue
            for file in files:
                if file.endswith(".wasm"):
                    wasm_files.append(Path(root) / file)
        return wasm_files
    
    def run_warduino_test(self, wasm_file, entry_point="_start", use_no_debug=True):
        """运行单个WASM测试"""
        try:
            cmd = [str(self.wdcli_path)]
            if use_no_debug:
                cmd.append("--no-debug")
            cmd.extend(["--invoke", entry_point])
            cmd.append(str(wasm_file))
            
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
                "command": " ".join(cmd)
            }
            
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": "执行超时",
                "returncode": -1,
                "timeout": True,
                "command": " ".join(cmd)
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "error": True,
                "command": " ".join(cmd)
            }
    
    def run_focused_tests(self):
        """运行聚焦测试 - 只使用--no-debug配置"""
        # 只使用--no-debug配置
        configs = [("_start", True)]
        
        wasm_files = self.find_wasm_files()
        print(f"找到 {len(wasm_files)} 个WASM文件")
        print(f"使用配置: --no-debug, 入口点: _start")
        print("=" * 60)
        
        total_tests = 0
        security_triggered = 0
        
        for wasm_file in wasm_files:
            for entry_point, use_no_debug in configs:
                total_tests += 1
                rel_path = wasm_file.relative_to(self.test_dir)
                test_name = f"{rel_path.stem}"
                
                print(f"测试: {test_name}")
                
                result = self.run_warduino_test(wasm_file, entry_point, use_no_debug)
                
                # 显示返回码和输出
                returncode = result.get("returncode", 0)
                stdout_preview = result.get("stdout", "")[:200].replace('\n', ' ')
                stderr_preview = result.get("stderr", "")[:200].replace('\n', ' ')
                
                print(f"  返回码: {returncode}")
                if stdout_preview:
                    print(f"  输出: {stdout_preview}")
                if stderr_preview:
                    print(f"  错误: {stderr_preview}")
                
                # 简化分析：只关注是否触发安全机制
                status = self.simple_analyze(result)
                
                self.test_results[test_name] = {
                    "status": status,
                    "file_path": str(wasm_file),
                    "entry_point": entry_point,
                    "use_no_debug": use_no_debug,
                    "returncode": returncode,
                    "stdout": result.get("stdout", "")[:500],
                    "stderr": result.get("stderr", "")[:500],
                    "timestamp": datetime.now().isoformat(),
                    "command": result.get("command", "")
                }
                
                if status == "SECURITY_TRIGGERED":
                    security_triggered += 1
                    print("  ✅ 安全机制触发")
                elif status == "COMPLETED":
                    print("  ⚠️  正常完成")
                elif status == "TIMEOUT":
                    print("  ⏱️  超时")
                else:
                    print("  ❌ 其他结果")
                
                print()  # 空行分隔不同测试
        
        # 生成简要报告
        detection_rate = (security_triggered / total_tests) * 100 if total_tests > 0 else 0
        report = {
            "platform": "WARDuino",
            "timestamp": datetime.now().isoformat(),
            "configs_used": configs,
            "timeout_setting": self.timeout,
            "summary": {
                "total_tests": total_tests,
                "security_triggered": security_triggered,
                "detection_rate": round(detection_rate, 1)
            },
            "results": self.test_results
        }
        
        # 创建output目录
        output_dir = self.report_dir
        output_dir.mkdir(exist_ok=True)
        
        report_file = output_dir / f"focused_warduino_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w", encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print("=" * 60)
        print("📊 聚焦测试结果:")
        print(f"   总计测试: {total_tests}")
        print(f"   安全触发: {security_triggered}")
        print(f"   检测率: {detection_rate:.1f}%")
        print(f"   报告文件: {report_file}")
        
        return report
    
    def simple_analyze(self, result):
        """简化结果分析"""
        output = result["stdout"] + " " + result["stderr"]
        returncode = result["returncode"]
        output_lower = output.lower()
        
        if result.get("timeout"):
            return "TIMEOUT"
        elif returncode == -11:
            return "SECURITY_TRIGGERED"  # SEGFAULT
        elif "trap" in output_lower or "error" in output_lower or "exception" in output_lower:
            return "SECURITY_TRIGGERED"
        elif returncode == 0:
            return "COMPLETED"
        else:
            return "OTHER"

def main():
    wdcli_path = Path("~/WARDuino/build-emu/wdcli").expanduser()
    
    if not wdcli_path.exists():
        print("❌ WARDuino wdcli不存在")
        return
    
    runner = FocusedWARDuinoTestRunner(wdcli_path, timeout=5)
    
    # 运行聚焦测试
    print("开始WARDuino聚焦测试...")
    print("配置: 只使用 --no-debug 模式")
    print()
    runner.run_focused_tests()

if __name__ == "__main__":
    main()
