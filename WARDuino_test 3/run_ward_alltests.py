#!/usr/bin/env python3
# run_tests.py - 运行WASM测试并生成安全报告（WARDuino版本）

import os
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

class WARDuinoTestRunner:
    def __init__(self, wdcli_path, test_dir="ward_tests", timeout=3):
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
    
    def find_wasm_files(self):
        """递归查找所有WASM文件"""
        wasm_files = []
        for root, dirs, files in os.walk(self.test_dir):
            # 跳过report目录
            if "report" in root:
                continue
                
            for file in files:
                if file.endswith(".wasm"):
                    wasm_files.append(Path(root) / file)
        return wasm_files
    
    def run_warduino_test(self, wasm_file, entry_point="_start", use_no_debug=True):
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
            # 构建命令
            cmd = [str(self.wdcli_path)]
            cmd.append(str(wasm_file))
            
            if use_no_debug:
                cmd.append("--no-debug")
            
            cmd.extend(["--invoke", entry_point])
            
            
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
        elif returncode == -11:
            return "SEGFAULT", "段错误 - 安全机制可能生效"
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
        
        # 查找所有WASM文件
        wasm_files = self.find_wasm_files()
        print(f"找到 {len(wasm_files)} 个WASM文件")
        
        if not wasm_files:
            print("❌ 未找到任何WASM文件")
            return False
        
        # 为每个WASM文件定义测试配置
        test_configs = []
        for wasm_file in wasm_files:
            # 对每个文件尝试不同的入口点和参数组合
            test_configs.extend([
                (wasm_file, "_start", True),
                (wasm_file, "_start", False),
                (wasm_file, "warduino_main", True),
                (wasm_file, "warduino_main", False),
                (wasm_file, "main", True),
                (wasm_file, "main", False),
            ])
        
        print(f"测试配置数量: {len(test_configs)}")
        
        for wasm_file, entry_point, use_no_debug in test_configs:
            # 创建唯一的测试名称
            rel_path = wasm_file.relative_to(self.test_dir)
            test_name = f"{rel_path.stem}_{entry_point}_{'nodebug' if use_no_debug else 'debug'}"
            
            print(f"测试: {test_name}")
            print(f"文件: {wasm_file}")
            print(f"参数: 入口点={entry_point}, no-debug={use_no_debug}")
            
            if not wasm_file.exists():
                print(f"❌ 文件不存在: {wasm_file}")
                self.test_results[test_name] = {
                    "status": "FILE_NOT_FOUND",
                    "details": f"文件不存在: {wasm_file}",
                    "timestamp": datetime.now().isoformat()
                }
                continue
            
            file_size = wasm_file.stat().st_size
            print(f"大小: {file_size} bytes")
            
            # 运行测试
            result = self.run_warduino_test(wasm_file, entry_point, use_no_debug)
            
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
                "entry_point": entry_point,
                "use_no_debug": use_no_debug,
                "command": result.get("command", ""),
                "file_path": str(wasm_file)
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
            time.sleep(0.05)  # 短暂延迟
        
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
        
        # 按文件路径分组结果
        files_summary = {}
        for test_name, result in self.test_results.items():
            file_path = result.get("file_path", "unknown")
            if file_path not in files_summary:
                files_summary[file_path] = {
                    "total_configs": 0,
                    "successful_configs": 0,
                    "best_result": "UNKNOWN",
                    "results": []
                }
            
            files_summary[file_path]["total_configs"] += 1
            files_summary[file_path]["results"].append({
                "test_name": test_name,
                "status": result["status"],
                "entry_point": result.get("entry_point", ""),
                "use_no_debug": result.get("use_no_debug", False)
            })
            
            # 更新最佳结果
            if result["status"] == "COMPLETED":
                files_summary[file_path]["successful_configs"] += 1
                if files_summary[file_path]["best_result"] != "COMPLETED":
                    files_summary[file_path]["best_result"] = "COMPLETED"
            elif result["status"] in ["TRAPPED", "SEGFAULT"] and files_summary[file_path]["best_result"] not in ["COMPLETED"]:
                files_summary[file_path]["best_result"] = "SECURITY_TRIGGERED"
        
        report = {
            "platform": "WARDuino",
            "timestamp": datetime.now().isoformat(),
            "wdcli_path": str(self.wdcli_path),
            "timeout": self.timeout,
            "test_environment": {
                "test_directory": str(self.test_dir),
                "report_directory": str(self.report_dir),
                "total_tests": total,
                "total_files": len(files_summary)
            },
            "results": self.test_results,
            "files_summary": files_summary,
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
        files_summary = report['files_summary']
        
        print("=" * 60)
        print("WARDuino安全测试详细总结")
        print("=" * 60)
        
        print(f"📊 总体统计:")
        print(f"   总计测试配置: {summary['total_tests']}")
        print(f"   测试文件数量: {len(files_summary)}")
        print(f"   ✅ 安全机制触发: {summary['security_mechanisms_triggered']}")
        print(f"   ⚠️  正常完成: {summary['completed_normally']}")
        print(f"   ⏱️  超时: {summary['timeouts']}")
        print(f"   ❌ 失败: {summary['failed_tests']}")
        print(f"   ❓ 其他: {summary['other_results']}")
        
        print(f"\n🛡️  安全效果:")
        print(f"   检测率: {effectiveness['detection_rate']}%")
        print(f"   有效测试: {effectiveness['successful_tests']}")
        
        print(f"\n📋 文件结果摘要:")
        for file_path, file_info in files_summary.items():
            success_rate = round(file_info["successful_configs"] / file_info["total_configs"] * 100, 1)
            print(f"   {Path(file_path).name}: {file_info['best_result']} ({success_rate}% 配置成功)")
        
        print(f"\n📋 详细结果 (前20个):")
        count = 0
        for test_name, result in report['results'].items():
            if count >= 20:
                print(f"   ... 还有 {len(report['results']) - 20} 个结果未显示")
                break
                
            if result["status"] in ["TRAPPED", "ERROR", "SEGFAULT", "EXCEPTION", "BOUNDS_ERROR", 
                                   "MEMORY_ACCESS_ERROR", "DIVISION_BY_ZERO", "INTEGER_OVERFLOW", "NULL_POINTER"]:
                icon = "✅"
            elif result["status"] == "COMPLETED":
                icon = "⚠️"
            elif result["status"] in ["TIMEOUT", "FILE_NOT_FOUND", "FILE_ERROR", "INVALID_WASM"]:
                icon = "❌"
            else:
                icon = "❓"
            
            print(f"   {icon} {test_name}: {result['status']}")
            count += 1

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
    runner = WARDuinoTestRunner(wdcli_path=wdcli_path, timeout=3)
    
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
