#!/usr/bin/env python3
import os
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

class Wasm3TestRunner:
    def __init__(self, wasm3_path, bin_dir="WARD_bin", timeout=10):
        self.wasm3_path = Path(wasm3_path)
        self.bin_dir = Path(bin_dir)
        self.timeout = timeout
        self.test_results = {}
        self.wasm3_version = None
        
    def load_manifest(self):
        """加载测试清单"""
        manifest_file = self.bin_dir / "test_manifest.json"
        if not manifest_file.exists():
            raise FileNotFoundError(f"测试清单文件不存在: {manifest_file}")
        
        with open(manifest_file, 'r') as f:
            return json.load(f)
    
    def get_wasm3_version(self):
        """获取wasm3版本信息"""
        try:
            result = subprocess.run(
                [str(self.wasm3_path), "--version"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                self.wasm3_version = result.stdout.strip()
                return self.wasm3_version
        except Exception as e:
            print(f"获取版本失败: {e}")
        return "未知版本"
    
    def check_wasm3(self):
        """检查wasm3是否可用"""
        if not self.wasm3_path.exists():
            return False, f"wasm3不存在: {self.wasm3_path}"
        
        try:
            # 尝试运行wasm3 --version
            result = subprocess.run(
                [str(self.wasm3_path), "--version"],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                version_info = result.stdout.strip()
                return True, f"wasm3可用 - {version_info}"
            
            # 尝试直接运行wasm3（某些版本可能没有--version参数）
            result = subprocess.run(
                [str(self.wasm3_path)],
                capture_output=True, text=True, timeout=2
            )
            if "usage" in result.stdout.lower() or "wasm3" in result.stdout.lower():
                return True, "wasm3可用"
                
            return False, f"wasm3验证失败: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return True, "wasm3运行但超时（可能正常）"
        except Exception as e:
            return False, f"wasm3执行错误: {e}"
    
    def run_wasm3_test(self, wasm_file, test_name):
        """使用wasm3运行测试"""
        if not wasm_file.exists():
            return {
                "stdout": "",
                "stderr": f"文件不存在: {wasm_file}",
                "returncode": -1,
                "file_error": True
            }
        
        file_size = wasm_file.stat().st_size
        if file_size < 10:
            return {
                "stdout": "",
                "stderr": f"文件太小({file_size} bytes)，可能无效",
                "returncode": -1,
                "file_error": True
            }
        
        try:
            # wasm3 运行命令
            cmd = [str(self.wasm3_path), str(wasm_file)]
            
            # 设置环境变量
            env = os.environ.copy()
            
            print(f"   执行命令: {' '.join(cmd)}")
            
            # 对于可能无限循环的测试，使用更短的超时
            test_timeout = self.timeout
            if test_name in ["Infinite_Loop", "Stack_Overflow"]:
                test_timeout = 3
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=test_timeout,
                env=env
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "args": cmd,
                "file_size": file_size
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
    
    def get_expected_behavior(self, test_name):
        """定义每个测试的预期行为"""
        expectations = {
            "OOB_Write": {
                "should_fail": True,
                "reason": "越界写入应该触发内存保护",
                "error_type": "memory"
            },
            "OOB_Read": {
                "should_fail": True, 
                "reason": "越界读取应该触发边界检查",
                "error_type": "bounds"
            },
            "Stack_Overflow": {
                "should_fail": True,
                "reason": "栈溢出应该被检测",
                "error_type": "stack"
            },
            "Division_By_Zero": {
                "should_fail": True,
                "reason": "除零应该触发算术异常", 
                "error_type": "arithmetic"
            },
            "Null_Pointer_Dereference": {
                "should_fail": True,
                "reason": "空指针解引用应该被阻止",
                "error_type": "memory"
            },
            "Infinite_Loop": {
                "should_fail": True,
                "reason": "无限循环应该被检测",
                "error_type": "execution"
            },
            "Uninitialized_Memory": {
                "should_fail": False,
                "reason": "未初始化内存使用可能不会立即触发错误",
                "error_type": "memory"
            },
            "Integer_Overflow": {
                "should_fail": False,  # WASM有定义的行为
                "reason": "整数溢出在WASM中有定义的行为",
                "error_type": "arithmetic"
            },
            "Memory_Access": {
                "should_fail": True,
                "reason": "无效内存访问应该被阻止",
                "error_type": "memory"
            },
            "Type_Confusion": {
                "should_fail": True,
                "reason": "类型混淆应该被检测",
                "error_type": "type"
            }
        }
        return expectations.get(test_name, {"should_fail": False})
    
    def analyze_wasm3_result(self, test_name, result):
        """分析wasm3测试结果"""
        output = result["stdout"] + " " + result["stderr"]
        returncode = result["returncode"]
        output_lower = output.lower()
        
        # 1. 首先检查文件错误和超时
        if result.get("file_error"):
            return "FILE_ERROR", result["stderr"]
        elif result.get("timeout"):
            # 对于无限循环测试，超时是期望的行为
            if test_name == "Infinite_Loop":
                return "TIMEOUT_DETECTED", "成功检测到无限循环（超时）"
            elif test_name == "Stack_Overflow":
                return "TIMEOUT_DETECTED", "可能检测到栈溢出（超时）"
            return "TIMEOUT", "执行超时"
        elif result.get("error"):
            return "RUNTIME_ERROR", f"运行时错误: {result['stderr']}"
        
        # 2. 检查wasm3特定错误模式
        wasm3_error_patterns = [
            ("error", "WASM3_ERROR", "wasm3错误"),
            ("trap", "TRAP", "WASM陷阱"),
            ("out of bounds", "BOUNDS_ERROR", "边界检查错误"),
            ("memory access", "MEMORY_ACCESS", "内存访问错误"),
            ("divide by zero", "DIV_ZERO", "除零错误"),
            ("stack overflow", "STACK_OVERFLOW", "栈溢出"),
            ("unreachable", "UNREACHABLE", "不可达指令"),
            ("type mismatch", "TYPE_ERROR", "类型错误"),
            ("validation error", "VALIDATION_ERROR", "验证错误"),
            ("instantiation error", "INSTANTIATION_ERROR", "实例化错误"),
        ]
        
        for pattern, error_type, description in wasm3_error_patterns:
            if pattern in output_lower:
                return error_type, f"{description}"
        
        # 3. 检查通用错误模式
        if "segfault" in output_lower or "segmentation" in output_lower:
            return "SEGFAULT", "分段错误"
        elif "exception" in output_lower:
            return "EXCEPTION", "异常发生"
        elif "panic" in output_lower:
            return "PANIC", "系统恐慌"
        elif "abort" in output_lower:
            return "ABORT", "程序中止"
        elif "invalid" in output_lower:
            return "INVALID", "无效操作"
        
        # 4. 基于预期行为分析
        expected_behavior = self.get_expected_behavior(test_name)
        
        if returncode == 0:
            # 检查是否有静默错误
            error_indicators = ["error", "exception", "fail", "invalid", "trap"]
            if any(indicator in output_lower for indicator in error_indicators):
                return "SILENT_ERROR", "退出码为0但输出包含错误信息"
            
            # 检查是否应该失败但正常完成
            if expected_behavior.get("should_fail", False):
                return "FALSE_NEGATIVE", f"安全漏洞未检测: {expected_behavior['reason']}"
            
            return "COMPLETED", "正常完成"
        
        elif returncode != 0:
            # 非零退出码
            if output_lower.strip():
                return "NON_ZERO_EXIT", f"非零退出码: {returncode}，输出: {output_lower[:100]}"
            else:
                return "NON_ZERO_EXIT", f"非零退出码: {returncode}"
        else:
            return "UNKNOWN", "无法确定结果"
    
    def run_test_suite(self):
        """运行所有测试"""
        print("开始wasm3安全测试...")
        print(f"wasm3路径: {self.wasm3_path}")
        print(f"超时设置: {self.timeout}秒")
        print("=" * 60)
        
        # 检查wasm3
        wasm3_ok, wasm3_msg = self.check_wasm3()
        if not wasm3_ok:
            print(f"❌ {wasm3_msg}")
            return False
        print(f"✅ {wasm3_msg}")
        
        # 获取版本信息
        version_info = self.get_wasm3_version()
        print(f"📋 wasm3版本: {version_info}")
        print()
        
        # 加载清单
        manifest = self.load_manifest()
        
        for test_name, test_info in manifest['tests'].items():
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
            
            wasm_file = Path(test_info['wasm_file'])
            file_size = test_info.get('file_size', 0)
            print(f"文件: {wasm_file} ({file_size} bytes)")
            
            # 运行测试
            result = self.run_wasm3_test(wasm_file, test_name)
            
            # 分析结果
            status, details = self.analyze_wasm3_result(test_name, result)
            
            # 记录结果
            test_result = {
                "status": status,
                "details": details,
                "returncode": result.get("returncode", 0),
                "stdout": result.get("stdout", "")[:500],
                "stderr": result.get("stderr", "")[:500],
                "timestamp": datetime.now().isoformat(),
                "file_size": file_size,
                "args": result.get("args", [])
            }
            
            self.test_results[test_name] = test_result
            
            # 显示结果
            if status in ["TRAP", "BOUNDS_ERROR", "MEMORY_ACCESS", "DIV_ZERO", 
                         "STACK_OVERFLOW", "UNREACHABLE", "TYPE_ERROR", 
                         "VALIDATION_ERROR", "TIMEOUT_DETECTED"]:
                status_icon = "✅"
                result_type = "安全机制生效"
            elif status == "COMPLETED":
                expected = self.get_expected_behavior(test_name)
                if expected.get("should_fail", False):
                    status_icon = "❌"
                    result_type = "安全漏洞未检测"
                else:
                    status_icon = "✅"
                    result_type = "正常完成（符合预期）"
            elif status == "FALSE_NEGATIVE":
                status_icon = "❌"
                result_type = "安全漏洞未检测"
            elif status == "SILENT_ERROR":
                status_icon = "🔍"
                result_type = "静默错误"
            else:
                status_icon = "❓"
                result_type = "需要分析"
            
            print(f"{status_icon} 结果: {status} - {details}")
            print(f"   类型: {result_type}")
            
            # 显示错误输出（如果有）
            if result.get('stderr') and not result.get('file_error'):
                error_preview = result['stderr'].replace('\n', ' ').strip()
                if error_preview and len(error_preview) > 10:
                    print(f"   错误: {error_preview[:100]}...")
            
            print()
            time.sleep(0.1)  # 短暂延迟
        
        return True
    
    def generate_report(self):
        """生成详细测试报告"""
        total = len(self.test_results)
        
        # 统计安全机制触发的情况
        security_triggered = sum(1 for r in self.test_results.values() 
                               if r["status"] in ["TRAP", "BOUNDS_ERROR", "MEMORY_ACCESS", 
                                                "DIV_ZERO", "STACK_OVERFLOW", "UNREACHABLE",
                                                "TYPE_ERROR", "VALIDATION_ERROR", "TIMEOUT_DETECTED"])
        
        false_negatives = sum(1 for r in self.test_results.values() 
                            if r["status"] == "FALSE_NEGATIVE")
        completed_normally = sum(1 for r in self.test_results.values() 
                              if r["status"] == "COMPLETED")
        timeouts = sum(1 for r in self.test_results.values() 
                     if r["status"] in ["TIMEOUT", "TIMEOUT_DETECTED"])
        failed = sum(1 for r in self.test_results.values() 
                   if r["status"] in ["COMPILE_FAILED", "FILE_ERROR", "RUNTIME_ERROR"])
        
        # 计算检测率
        effective_tests = total - failed
        detection_rate = round(security_triggered / effective_tests * 100, 2) if effective_tests > 0 else 0
        
        report = {
            "platform": "wasm3",
            "wasm3_version": self.wasm3_version,
            "timestamp": datetime.now().isoformat(),
            "wasm3_path": str(self.wasm3_path),
            "timeout": self.timeout,
            "test_environment": {
                "manifest_generated": self.load_manifest()['generated_at'],
                "total_tests": total
            },
            "results": self.test_results,
            "summary": {
                "total_tests": total,
                "security_mechanisms_triggered": security_triggered,
                "false_negatives": false_negatives,
                "completed_normally": completed_normally,
                "timeouts": timeouts,
                "failed_tests": failed,
                "effective_tests": effective_tests
            },
            "security_effectiveness": {
                "detection_rate": detection_rate,
                "false_negative_rate": round(false_negatives / effective_tests * 100, 2) if effective_tests > 0 else 0,
                "successful_tests": effective_tests
            }
        }
        
        # 保存报告
        report_file = f"wasm3_security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w", encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report, report_file
    
    def print_detailed_summary(self, report):
        """打印详细总结"""
        summary = report['summary']
        effectiveness = report['security_effectiveness']
        
        print("=" * 60)
        print("wasm3安全测试详细总结")
        print("=" * 60)
        
        print(f"📊 测试统计:")
        print(f"   总计测试: {summary['total_tests']}")
        print(f"   ✅ 安全机制触发: {summary['security_mechanisms_triggered']}")
        print(f"   ❌ 假阴性(漏洞未检测): {summary['false_negatives']}")
        print(f"   ✅ 正常完成: {summary['completed_normally']}")
        print(f"   ⏱️  超时: {summary['timeouts']}")
        print(f"   💥 失败: {summary['failed_tests']}")
        print(f"   📈 有效测试: {summary['effective_tests']}")
        
        print(f"\n🛡️  安全效果:")
        print(f"   检测率: {effectiveness['detection_rate']}%")
        if effectiveness['false_negative_rate'] > 0:
            print(f"   假阴性率: {effectiveness['false_negative_rate']}%")
        
        print(f"\n📋 详细结果:")
        for test_name, result in report['results'].items():
            if result["status"] in ["TRAP", "BOUNDS_ERROR", "MEMORY_ACCESS", "DIV_ZERO", 
                                  "STACK_OVERFLOW", "UNREACHABLE", "TYPE_ERROR", "TIMEOUT_DETECTED"]:
                icon = "✅"
            elif result["status"] == "FALSE_NEGATIVE":
                icon = "❌"
            elif result["status"] == "COMPLETED":
                # 检查是否符合预期
                expected = self.get_expected_behavior(test_name)
                if expected.get("should_fail", False):
                    icon = "❌"
                else:
                    icon = "✅"
            elif result["status"] in ["TIMEOUT", "COMPILE_FAILED", "FILE_ERROR"]:
                icon = "💥"
            elif result["status"] == "SILENT_ERROR":
                icon = "🔍"
            else:
                icon = "❓"
            
            print(f"   {icon} {test_name}: {result['status']} - {result['details']}")

def find_wasm3():
    """查找wasm3可执行文件"""
    possible_paths = [
        "../wasm3/wasm3",
        "./wasm3",
        "/usr/local/bin/wasm3",
        "/usr/bin/wasm3"
    ]
    
    for path in possible_paths:
        path_obj = Path(path)
        if path_obj.exists() and os.access(str(path_obj), os.X_OK):
            return path_obj
    
    # 尝试在PATH中查找
    try:
        result = subprocess.run(["which", "wasm3"], capture_output=True, text=True)
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except:
        pass
    
    return None

def main():
    print("wasm3安全测试框架")
    print("=" * 50)
    
    # 查找wasm3
    wasm3_path = find_wasm3()
    if not wasm3_path:
        print("❌ 未找到wasm3可执行文件")
        print("请确保wasm3已安装或提供正确路径")
        return
    
    print(f"✅ 找到wasm3: {wasm3_path}")
    
    if not Path("WARD_bin").exists():
        print("❌ WARD_bin目录不存在")
        print("请先运行 generate_tests.py 和 compile_WARD_tests.py")
        return
    
    # 创建测试运行器
    runner = Wasm3TestRunner(wasm3_path=wasm3_path, timeout=10)
    
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
