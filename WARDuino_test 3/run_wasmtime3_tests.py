#!/usr/bin/env python3
# run_wasmtime2_tests.py - 运行WASM测试并生成安全报告（wasmtime增强版本）

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
        self.wasmtime_version = None
        self.security_features = {}
        
        # 加载测试清单
        self.manifest = self.load_manifest()
    
    def load_manifest(self):
        """加载测试清单"""
        manifest_file = self.bin_dir / "test_manifest.json"
        if not manifest_file.exists():
            raise FileNotFoundError(f"测试清单文件不存在: {manifest_file}")
        
        with open(manifest_file, 'r') as f:
            return json.load(f)
    
    def get_wasmtime_version(self):
        """获取wasmtime版本信息"""
        try:
            result = subprocess.run(
                [str(self.wasmtime_path), "--version"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                version_line = result.stdout.strip()
                # 提取版本号
                import re
                match = re.search(r'wasmtime\s+([\d.]+)', version_line)
                if match:
                    self.wasmtime_version = match.group(1)
                return version_line
        except Exception as e:
            print(f"获取版本失败: {e}")
        return "未知版本"
    
    def check_wasmtime_configuration(self):
        """检测wasmtime的当前安全配置"""
        print("🔧 检查wasmtime安全配置...")
        version_info = self.get_wasmtime_version()
        print(f"   📋 {version_info}")
        
        try:
            # 检查run命令的帮助信息
            help_result = subprocess.run(
                [str(self.wasmtime_path), "run", "--help"],
                capture_output=True, text=True, timeout=10
            )
            
            help_output = help_result.stdout
            
            # 更精确地检查参数支持 - 使用更严格的匹配
            feature_checks = {
                "cache": any(line.strip().startswith("--cache") for line in help_output.split('\n')),
                "config": any(line.strip().startswith("--config") for line in help_output.split('\n')),
                "disable-logging": any("disable-logging" in line for line in help_output.split('\n')),
                "env": any(line.strip().startswith("--env") for line in help_output.split('\n')),
                "map-dir": any("map-dir" in line for line in help_output.split('\n')),
                "tcplisten": any("tcplisten" in line for line in help_output.split('\n')),
                "wasm-timeout": any("wasm-timeout" in line for line in help_output.split('\n')),
                "wasi": "WASI" in help_output,
            }
            
            for feature, supported in feature_checks.items():
                status = "✅" if supported else "❌"
                print(f"   {status} {feature}: {'支持' if supported else '不支持'}")
                self.security_features[feature] = supported
                
            # 检查基本运行功能
            print("   🔄 测试基本运行功能...")
            test_result = subprocess.run(
                [str(self.wasmtime_path), "run", "--help"],
                capture_output=True, text=True, timeout=5
            )
            if test_result.returncode == 0:
                print("   ✅ 基本运行功能正常")
            else:
                print("   ⚠️ 基本运行功能可能有问题")
                
        except Exception as e:
            print(f"   ❌ 配置检查失败: {e}")
            
        return self.security_features
    
    def check_wasmtime(self):
        """检查wasmtime是否可用"""
        if not self.wasmtime_path.exists():
            return False, f"wasmtime不存在: {self.wasmtime_path}"
        
        try:
            # 尝试运行wasmtime --version
            result = subprocess.run(
                [str(self.wasmtime_path), "--version"],
                capture_output=True, 
                text=True, 
                timeout=2
            )
            
            if result.returncode == 0 or "wasmtime" in result.stdout.lower():
                return True, "wasmtime可用"
            else:
                # 尝试使用run命令
                result = subprocess.run(
                    [str(self.wasmtime_path), "run", "--help"],
                    capture_output=True, 
                    text=True, 
                    timeout=2
                )
                if result.returncode == 0:
                    return True, "wasmtime可用（新版本语法）"
                return False, f"wasmtime验证失败: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return True, "wasmtime运行但超时（可能正常）"
        except Exception as e:
            return False, f"wasmtime执行错误: {e}"
    
    def get_security_flags(self, test_name):
        """获取适用于当前wasmtime版本的安全标志"""
        flags = []
        
        # 只使用确认支持的参数
        if self.security_features.get("disable-logging"):
            flags.append("--disable-logging")
        
        # 根据测试类型添加特定配置
        if test_name in ["Stack_Overflow", "Infinite_Loop"]:
            # 新版本wasmtime可能不支持--wasm-timeout，使用Python超时机制
            pass
            
        return flags
    
    def run_wasmtime_test(self, wasm_file, test_name):
        """使用兼容的wasmtime参数运行测试"""
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
            # 新版本wasmtime使用 'wasmtime run' 语法
            wasmtime_args = [
                str(self.wasmtime_path),
                "run",
            ]
            
            # 添加安全标志（只使用确认支持的参数）
            security_flags = self.get_security_flags(test_name)
            wasmtime_args.extend(security_flags)
            
            wasmtime_args.append(str(wasm_file))
            
            # 设置环境变量
            env = os.environ.copy()
            env["RUST_BACKTRACE"] = "1"  # 获取错误栈
            
            print(f"   执行命令: {' '.join(wasmtime_args)}")
            
            # 对于可能无限循环的测试，使用更短的超时
            test_timeout = self.timeout
            if test_name in ["Infinite_Loop", "Stack_Overflow"]:
                test_timeout = 3  # 更短的超时用于检测无限循环
            
            result = subprocess.run(
                wasmtime_args,
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
                "args": wasmtime_args
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
                "should_fail": True,  # 期望超时或检测
                "reason": "无限循环应该被检测",
                "error_type": "execution"
            },
        }
        return expectations.get(test_name, {"should_fail": False})
    
    def analyze_result(self, test_name, result):
        """分析测试结果"""
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
            return "TIMEOUT", "执行超时"
        elif result.get("error"):
            return "RUNTIME_ERROR", f"运行时错误: {result['stderr']}"
        
        # 2. 检查参数错误（不支持的参数）
        if "unexpected argument" in output_lower:
            return "ARGUMENT_ERROR", f"不支持的参数: {result['stderr'].split('found')[0]}"
        
        # 3. 检查wasmtime特定错误模式
        wasmtime_error_patterns = [
            ("wasm trap", "WASM_TRAP", "WASM陷阱触发"),
            ("unreachable", "UNREACHABLE", "不可达指令"),
            ("out of bounds", "BOUNDS_ERROR", "边界检查错误"),
            ("type mismatch", "TYPE_ERROR", "类型错误"),
            ("divide by zero", "DIV_ZERO", "除零错误"),
            ("memory access", "MEMORY_ACCESS", "内存访问错误"),
            ("stack overflow", "STACK_OVERFLOW", "栈溢出"),
            ("illegal", "ILLEGAL_INSTRUCTION", "非法指令"),
            ("trap", "TRAP", "陷阱异常"),
        ]
        
        for pattern, error_type, description in wasmtime_error_patterns:
            if pattern in output_lower:
                return error_type, f"{description}"
        
        # 4. 检查通用错误模式
        if "error" in output_lower and "wasm" in output_lower:
            return "WASM_ERROR", "WASM模块错误"
        elif "segfault" in output_lower or "segmentation" in output_lower:
            return "SEGFAULT", "分段错误"
        elif "exception" in output_lower:
            return "EXCEPTION", "异常发生"
        elif "panic" in output_lower:
            return "PANIC", "系统恐慌"
        elif "abort" in output_lower:
            return "ABORT", "程序中止"
        elif "invalid" in output_lower:
            return "INVALID", "无效操作"
        
        # 5. 基于预期行为分析
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
        
        # 检查安全配置
        self.check_wasmtime_configuration()
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
            result = self.run_wasmtime_test(wasm_file, test_name)
            
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
                "args": result.get("args", [])
            }
            
            self.test_results[test_name] = test_result
            
            # 显示结果
            if status in ["WASM_TRAP", "TRAP", "BOUNDS_ERROR", "MEMORY_ACCESS", 
                         "DIV_ZERO", "STACK_OVERFLOW", "UNREACHABLE", "TIMEOUT_DETECTED"]:
                status_icon = "✅"
                result_type = "安全机制生效"
            elif status == "COMPLETED":
                status_icon = "⚠️"
                result_type = "正常完成"
            elif status == "FALSE_NEGATIVE":
                status_icon = "❌"
                result_type = "安全漏洞未检测"
            elif status == "SILENT_ERROR":
                status_icon = "🔍"
                result_type = "静默错误"
            elif status == "ARGUMENT_ERROR":
                status_icon = "🚫"
                result_type = "参数错误"
            else:
                status_icon = "❓"
                result_type = "需要分析"
            
            print(f"{status_icon} 结果: {status} - {details} ({result_type})")
            
            # 显示错误输出（如果有）
            if result.get('stderr') and not result.get('file_error'):
                error_preview = result['stderr'].replace('\n', ' ').strip()
                if error_preview and len(error_preview) > 10:
                    # 截取关键错误信息
                    important_parts = []
                    for part in error_preview.split('.'):
                        if any(keyword in part.lower() for keyword in 
                              ['error', 'trap', 'fail', 'invalid', 'exception']):
                            important_parts.append(part.strip())
                    
                    if important_parts:
                        error_display = '. '.join(important_parts)[:150] + "..."
                        print(f"   错误: {error_display}")
                    else:
                        print(f"   错误: {error_preview[:100]}...")
            
            print()
            time.sleep(0.1)  # 短暂延迟
        
        return True
    
    def generate_report(self):
        """生成详细测试报告"""
        total = len(self.test_results)
        
        # 统计安全机制触发的情况
        security_triggered = sum(1 for r in self.test_results.values() 
                               if r["status"] in ["WASM_TRAP", "TRAP", "BOUNDS_ERROR", 
                                                "MEMORY_ACCESS", "DIV_ZERO", "STACK_OVERFLOW",
                                                "UNREACHABLE", "ILLEGAL_INSTRUCTION", "TIMEOUT_DETECTED"])
        
        false_negatives = sum(1 for r in self.test_results.values() 
                            if r["status"] == "FALSE_NEGATIVE")
        completed = sum(1 for r in self.test_results.values() 
                      if r["status"] == "COMPLETED")
        timeouts = sum(1 for r in self.test_results.values() 
                     if r["status"] in ["TIMEOUT", "TIMEOUT_DETECTED"])
        failed = sum(1 for r in self.test_results.values() 
                   if r["status"] in ["COMPILE_FAILED", "FILE_ERROR", "INVALID_WASM", "ARGUMENT_ERROR"])
        other = total - (security_triggered + false_negatives + completed + timeouts + failed)
        
        # 计算检测率
        effective_tests = total - failed
        true_detection_rate = round(security_triggered / effective_tests * 100, 2) if effective_tests > 0 else 0
        
        report = {
            "platform": "wasmtime",
            "wasmtime_version": self.wasmtime_version,
            "timestamp": datetime.now().isoformat(),
            "wasmtime_path": str(self.wasmtime_path),
            "timeout": self.timeout,
            "security_features": self.security_features,
            "test_environment": {
                "manifest_generated": self.manifest['generated_at'],
                "total_tests": total
            },
            "results": self.test_results,
            "summary": {
                "total_tests": total,
                "security_mechanisms_triggered": security_triggered,
                "false_negatives": false_negatives,
                "completed_normally": completed,
                "timeouts": timeouts,
                "failed_tests": failed,
                "other_results": other,
                "effective_tests": effective_tests
            },
            "security_effectiveness": {
                "detection_rate": true_detection_rate,
                "false_negative_rate": round(false_negatives / effective_tests * 100, 2) if effective_tests > 0 else 0,
                "successful_tests": effective_tests
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
        print(f"   ❌ 假阴性(漏洞未检测): {summary['false_negatives']}")
        print(f"   ⚠️  正常完成: {summary['completed_normally']}")
        print(f"   ⏱️  超时: {summary['timeouts']}")
        print(f"   💥 失败: {summary['failed_tests']}")
        print(f"   ❓ 其他: {summary['other_results']}")
        
        print(f"\n🛡️  安全效果:")
        print(f"   真实检测率: {effectiveness['detection_rate']}%")
        if effectiveness['false_negative_rate'] > 0:
            print(f"   假阴性率: {effectiveness['false_negative_rate']}%")
        print(f"   有效测试: {effectiveness['successful_tests']}")
        
        print(f"\n📋 详细结果:")
        for test_name, result in report['results'].items():
            if result["status"] in ["WASM_TRAP", "TRAP", "BOUNDS_ERROR", "MEMORY_ACCESS", 
                                  "DIV_ZERO", "STACK_OVERFLOW", "UNREACHABLE", "TIMEOUT_DETECTED"]:
                icon = "✅"
            elif result["status"] == "FALSE_NEGATIVE":
                icon = "❌"
            elif result["status"] == "COMPLETED":
                icon = "⚠️"
            elif result["status"] in ["TIMEOUT", "COMPILE_FAILED", "FILE_ERROR", "ARGUMENT_ERROR"]:
                icon = "💥"
            elif result["status"] == "SILENT_ERROR":
                icon = "🔍"
            else:
                icon = "❓"
            
            print(f"   {icon} {test_name}: {result['status']} - {result['details']}")

def find_wasmtime():
    """查找wasmtime可执行文件"""
    possible_paths = [
       
        "/opt/wasmtime-secure/wasmtime",
       
    ]
    
    for path in possible_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
    
    return None

def main():
    print("wasmtime安全测试框架（兼容版）")
    print("=" * 50)
    
    # 查找wasmtime
    wasmtime_path = find_wasmtime()
    if not wasmtime_path:
        print("❌ 未找到wasmtime可执行文件")
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
