#!/usr/bin/env python3
# analyze_results.py - 分析WARDuino测试结果

import json
import os
from pathlib import Path
from collections import defaultdict

def analyze_warduino_results(report_file):
    """分析WARDuino测试结果"""
    
    with open(report_file, 'r') as f:
        report = json.load(f)
    
    print("WARDuino测试结果深度分析")
    print("=" * 60)
    
    # 按文件类型分析
    file_categories = {
        "内存安全测试": ["oob_read", "oob_write", "stack_overflow", "test_OOB", "test_Buffer", "test_Heap"],
        "算术异常测试": ["test_Division", "test_Integer"],
        "指针安全测试": ["test_Null_Pointer", "test_Memory_Access"],
        "控制流测试": ["compute_test", "control_test", "test_Infinite"],
        "其他测试": ["test_Double_Free", "test_Format", "test_Memory_Alignment"]
    }
    
    category_results = defaultdict(lambda: {
        "total": 0,
        "security_triggered": 0,
        "completed": 0,
        "timeout": 0,
        "other": 0
    })
    
    # 分析每个测试结果
    for test_name, result in report["results"].items():
        # 确定测试类别
        category = "其他测试"
        for cat_name, keywords in file_categories.items():
            if any(keyword in test_name for keyword in keywords):
                category = cat_name
                break
        
        # 统计结果
        category_results[category]["total"] += 1
        status = result["status"]
        
        if status in ["TRAPPED", "ERROR", "SEGFAULT", "EXCEPTION", "BOUNDS_ERROR", 
                     "MEMORY_ACCESS_ERROR", "DIVISION_BY_ZERO", "INTEGER_OVERFLOW", "NULL_POINTER"]:
            category_results[category]["security_triggered"] += 1
        elif status == "COMPLETED":
            category_results[category]["completed"] += 1
        elif status == "TIMEOUT":
            category_results[category]["timeout"] += 1
        else:
            category_results[category]["other"] += 1
    
    # 打印分类结果
    print("\n📊 按测试类型分析:")
    for category, stats in category_results.items():
        if stats["total"] > 0:
            security_rate = (stats["security_triggered"] / stats["total"]) * 100
            print(f"  {category}:")
            print(f"    总计: {stats['total']}")
            print(f"    ✅ 安全触发: {stats['security_triggered']} ({security_rate:.1f}%)")
            print(f"    ⚠️  正常完成: {stats['completed']}")
            print(f"    ⏱️  超时: {stats['timeout']}")
            print(f"    ❓ 其他: {stats['other']}")
    
    # 分析配置有效性
    print("\n🔧 配置有效性分析:")
    config_effectiveness = defaultdict(lambda: {
        "total": 0,
        "security_triggered": 0,
        "completed": 0
    })
    
    for test_name, result in report["results"].items():
        config_key = f"{result.get('entry_point', 'unknown')}_{'nodebug' if result.get('use_no_debug') else 'debug'}"
        config_effectiveness[config_key]["total"] += 1
        
        status = result["status"]
        if status in ["TRAPPED", "ERROR", "SEGFAULT", "EXCEPTION", "BOUNDS_ERROR", 
                     "MEMORY_ACCESS_ERROR", "DIVISION_BY_ZERO", "INTEGER_OVERFLOW", "NULL_POINTER"]:
            config_effectiveness[config_key]["security_triggered"] += 1
        elif status == "COMPLETED":
            config_effectiveness[config_key]["completed"] += 1
    
    for config, stats in config_effectiveness.items():
        if stats["total"] > 0:
            security_rate = (stats["security_triggered"] / stats["total"]) * 100
            completion_rate = (stats["completed"] / stats["total"]) * 100
            print(f"  {config}: 安全率 {security_rate:.1f}%, 完成率 {completion_rate:.1f}%")
    
    # 找出成功的测试配置
    print("\n✅ 成功触发安全机制的测试:")
    successful_tests = []
    for test_name, result in report["results"].items():
        if result["status"] in ["TRAPPED", "ERROR", "SEGFAULT", "EXCEPTION", "BOUNDS_ERROR", 
                               "MEMORY_ACCESS_ERROR", "DIVISION_BY_ZERO", "INTEGER_OVERFLOW", "NULL_POINTER"]:
            successful_tests.append((test_name, result))
    
    for test_name, result in successful_tests[:10]:  # 只显示前10个
        print(f"  {test_name}: {result['status']} - {result['details']}")
    
    if len(successful_tests) > 10:
        print(f"  ... 还有 {len(successful_tests) - 10} 个成功测试")
    
    # 建议
    print("\n💡 改进建议:")
    
    low_detection_categories = []
    for category, stats in category_results.items():
        if stats["total"] > 0 and (stats["security_triggered"] / stats["total"]) < 0.3:
            low_detection_categories.append(category)
    
    if low_detection_categories:
        print("  1. 以下类别检测率较低，需要重点关注:")
        for category in low_detection_categories:
            print(f"     - {category}")
    
    # 分析超时问题
    timeout_count = sum(1 for r in report["results"].values() if r["status"] == "TIMEOUT")
    if timeout_count > 0:
        print(f"  2. 有 {timeout_count} 个测试超时，建议:")
        print("     - 增加超时时间或优化测试用例")
        print("     - 检查是否有无限循环测试")
    
    # 检查配置组合
    best_config = max(config_effectiveness.items(), 
                     key=lambda x: x[1]["security_triggered"] / x[1]["total"] if x[1]["total"] > 0 else 0)
    print(f"  3. 最有效的配置: {best_config[0]} (安全率 {(best_config[1]['security_triggered']/best_config[1]['total'])*100:.1f}%)")

def find_latest_report():
    """查找最新的测试报告"""
    report_dir = Path("ward_tests/report")
    if not report_dir.exists():
        print("❌ 报告目录不存在")
        return None
    
    report_files = list(report_dir.glob("warduino_security_report_*.json"))
    if not report_files:
        print("❌ 未找到测试报告")
        return None
    
    latest_report = max(report_files, key=lambda x: x.stat().st_mtime)
    return latest_report

def main():
    # 查找最新报告
    report_file = find_latest_report()
    if not report_file:
        return
    
    print(f"📄 分析报告: {report_file}")
    print()
    
    # 分析结果
    analyze_warduino_results(report_file)
    
    # 额外建议
    print("\n🚀 后续步骤:")
    print("  1. 针对低检测率的测试类别，修改测试用例使其更容易触发安全机制")
    print("  2. 尝试启用WARDuino的额外安全特性（如内存保护、控制流完整性）")
    print("  3. 考虑使用更激进的编译器选项生成WASM文件")
    print("  4. 手动验证成功案例，确保安全机制确实正确工作")

if __name__ == "__main__":
    main()
