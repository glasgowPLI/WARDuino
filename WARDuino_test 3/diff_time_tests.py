#!/usr/bin/env python3
"""
运行WARDuino基准测试并进行数据分析
使用subprocess调用外部命令测试运行时间和内存占用
"""

import os
import subprocess
import json
import time
import statistics
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from datetime import datetime
import numpy as np
import psutil
import re

class BenchmarkRunner:
    def __init__(self):
        self.work_dir = "/home/yuxin/WARDuino_test"
        self.tests_dir = os.path.join(self.work_dir, "tests")
        self.ward_bin_dir = os.path.join(self.work_dir, "WARD_bin")  # 测试模块wasm文件目录
        self.warduino_base_dir = "/home/yuxin/WARDuino-safe"  # WARDuino源码目录
        self.results = []
        
        # 测试配置 - 5个不同安全检查配置
        self.configurations = [
            "baseline",  # 基线：无任何安全检查
            "memory",    # 内存保护：只开启内存保护
            "stack",     # 栈保护：只开启栈保护
            "address",   # 地址消毒剂：只开启地址消毒剂
            "full"       # 全保护：开启所有检查
        ]
        
        # 配置顺序映射（用于图表排序）
        self.config_order = {
            'baseline': 0,
            'memory': 1,
            'stack': 2,
            'address': 3,
            'full': 4
        }
        
        # 设置matplotlib字体
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
    
    def get_warduino_binary_path(self, config_name):
        """获取WARDuino二进制文件路径"""
        build_dir = os.path.join(self.warduino_base_dir, f"build-{config_name}")
        binary_path = os.path.join(build_dir, "wdcli")
        return binary_path
    
    def check_environment(self):
        """检查测试环境"""
        print("检查测试环境...")
        
        # 检查WARDuino二进制文件
        missing_binaries = []
        for config in self.configurations:
            binary_path = self.get_warduino_binary_path(config)
            if not os.path.exists(binary_path):
                missing_binaries.append(config)
        
        if missing_binaries:
            print(f"❌ 缺失WARDuino二进制文件: {missing_binaries}")
            print("请先运行 build_warduino_configs.sh 编译WARDuino")
            return False
        
        # 检查WASM测试文件
        wasm_files = [f for f in os.listdir(self.tests_dir) if f.endswith('.wasm')]
        if not wasm_files:
            print("❌ 未找到WASM测试文件")
            print("请先运行 generate_benchmarks.py 生成测试程序")
            return False
        
        print(f"✅ 找到WARDuino配置: {len(self.configurations)}个")
        print(f"✅ 找到WASM测试文件: {len(wasm_files)}个")
        
        # 显示可执行文件信息
        print("\n可执行文件信息:")
        for config in self.configurations:
            binary_path = self.get_warduino_binary_path(config)
            if os.path.exists(binary_path):
                size = os.path.getsize(binary_path) / 1024 / 1024  # MB
                print(f"  - {config:15} {size:.2f} MB (路径: {binary_path})")
        
        return True
    
    def measure_memory_usage(self, pid):
        """测量进程内存使用"""
        try:
            process = psutil.Process(pid)
            memory_info = process.memory_info()
            return memory_info.rss / 1024  # 返回KB
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0
    
    def run_single_test(self, config_name, wasm_file, iterations=5):
        """运行单个测试配置，测量时间和内存"""
        warduino_binary = self.get_warduino_binary_path(config_name)
        wasm_path = os.path.join(self.tests_dir, wasm_file)
        
        print(f"  测试: {config_name:15} - {wasm_file:20}", end="")
        
        times = []
        memory_usages = []
        return_codes = []
        peak_memory = 0
        
        for i in range(iterations):
            try:
                # 使用time命令测量时间和内存
                start_time = time.perf_counter()
                
                # 运行WARDuino并测量内存，添加 --no-debug 参数
                proc = subprocess.Popen(
                    [warduino_binary, wasm_path, "--no-debug"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=self.work_dir
                )
                
                # 监控内存使用
                peak_memory_kb = 0
                try:
                    while proc.poll() is None:
                        current_memory = self.measure_memory_usage(proc.pid)
                        peak_memory_kb = max(peak_memory_kb, current_memory)
                        time.sleep(0.01)  # 10ms间隔
                except:
                    pass
                
                # 等待进程结束
                stdout, stderr = proc.communicate(timeout=30)
                execution_time = (time.perf_counter() - start_time) * 1000  # 毫秒
                
                times.append(execution_time)
                memory_usages.append(peak_memory_kb)
                return_codes.append(proc.returncode)
                
                if proc.returncode != 0:
                    print(f" ⚠️ 返回值: {proc.returncode}", end="")
                
            except subprocess.TimeoutExpired:
                print(" ⏰ 超时", end="")
                times.append(float('inf'))
                memory_usages.append(0)
                return_codes.append(-1)
                if 'proc' in locals():
                    proc.terminate()
            except Exception as e:
                print(f" ❌ 错误: {e}", end="")
                times.append(float('inf'))
                memory_usages.append(0)
                return_codes.append(-1)
        
        # 计算统计信息
        valid_times = [t for t in times if t != float('inf')]
        valid_memory = [m for i, m in enumerate(memory_usages) if times[i] != float('inf')]
        
        if valid_times:
            avg_time = statistics.mean(valid_times)
            std_time = statistics.stdev(valid_times) if len(valid_times) > 1 else 0
            avg_memory = statistics.mean(valid_memory) if valid_memory else 0
            std_memory = statistics.stdev(valid_memory) if len(valid_memory) > 1 else 0
            success_rate = len(valid_times) / iterations * 100
        else:
            avg_time = float('inf')
            std_time = 0
            avg_memory = 0
            std_memory = 0
            success_rate = 0
        
        print(f" | 时间: {avg_time:6.2f}ms | 内存: {avg_memory/1024:5.2f}MB | 成功率: {success_rate:5.1f}%")
        
        return {
            'config': config_name,
            'test_program': wasm_file,
            'avg_time_ms': avg_time,
            'std_time_ms': std_time,
            'avg_memory_kb': avg_memory,
            'std_memory_kb': std_memory,
            'avg_memory_mb': avg_memory / 1024,
            'success_rate': success_rate,
            'iterations': len(valid_times),
            'total_iterations': iterations,
            'return_codes': return_codes
        }
    
    def run_all_benchmarks(self):
        """运行所有基准测试"""
        print("开始运行WARDuino基准测试...")
        
        wasm_files = [f for f in os.listdir(self.tests_dir) if f.endswith('.wasm')]
        
        for wasm_file in wasm_files:
            print(f"\n测试程序: {wasm_file}")
            print("-" * 80)
            
            for config in self.configurations:
                result = self.run_single_test(config, wasm_file)
                if result:
                    self.results.append(result)
        
        # 保存原始结果
        self.save_raw_results()
    
    def save_raw_results(self):
        """保存原始测试结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(self.work_dir, f"benchmark_results_{timestamp}.json")
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n原始结果已保存: {results_file}")
        return results_file
    
    def analyze_performance(self):
        """分析性能数据"""
        if not self.results:
            print("没有测试结果可分析")
            return None, None
        
        df = pd.DataFrame(self.results)
        
        # 计算性能开销（相对于baseline）
        overhead_data = []
        baseline_times = {}
        baseline_memory = {}
        
        # 收集baseline数据
        for test_program in df['test_program'].unique():
            baseline_data = df[(df['config'] == 'baseline') & (df['test_program'] == test_program)]
            if not baseline_data.empty:
                baseline_times[test_program] = baseline_data.iloc[0]['avg_time_ms']
                baseline_memory[test_program] = baseline_data.iloc[0]['avg_memory_kb']
        
        # 计算相对开销
        for test_program in df['test_program'].unique():
            if test_program in baseline_times:
                baseline_time = baseline_times[test_program]
                baseline_mem = baseline_memory[test_program]
                
                for config in ['memory', 'stack', 'address', 'full']:
                    config_data = df[(df['config'] == config) & (df['test_program'] == test_program)]
                    
                    if not config_data.empty and baseline_time != float('inf'):
                        config_time = config_data.iloc[0]['avg_time_ms']
                        config_memory = config_data.iloc[0]['avg_memory_kb']
                        
                        if config_time != float('inf'):
                            time_overhead = ((config_time - baseline_time) / baseline_time) * 100
                        else:
                            time_overhead = float('inf')
                        
                        if baseline_mem > 0:
                            memory_overhead = ((config_memory - baseline_mem) / baseline_mem) * 100
                        else:
                            memory_overhead = float('inf')
                        
                        overhead_data.append({
                            'test_program': test_program,
                            'config': config,
                            'time_overhead_percent': time_overhead,
                            'memory_overhead_percent': memory_overhead,
                            'config_type': self.get_config_type(config),
                            'baseline_time': baseline_time,
                            'config_time': config_time,
                            'baseline_memory': baseline_mem,
                            'config_memory': config_memory
                        })
        
        return df, pd.DataFrame(overhead_data)
    
    def get_config_type(self, config):
        """获取配置类型描述"""
        types = {
            'baseline': 'Baseline',
            'memory': 'Memory Protection',
            'stack': 'Stack Protection',
            'address': 'Address Sanitizer',
            'full': 'Full Protection'
        }
        return types.get(config, 'Unknown')
    
    def generate_comprehensive_report(self, df, overhead_df):
        """生成综合分析报告"""
        print("\n" + "="*80)
        print("WARDuino安全检查性能综合分析报告")
        print("="*80)
        
        # 1. 总体性能对比 - 按配置顺序排列
        print("\n1. 总体性能对比 (执行时间 ms)")
        print("-" * 60)
        
        time_summary = df.pivot_table(
            values='avg_time_ms', 
            index='test_program', 
            columns='config', 
            aggfunc='mean'
        )
        # 按配置顺序重新排列列
        time_summary = time_summary[self.configurations]
        print(time_summary.round(2))
        
        # 2. 内存使用对比 - 按配置顺序排列
        print("\n2. 内存使用对比 (MB)")
        print("-" * 60)
        
        memory_summary = df.pivot_table(
            values='avg_memory_mb', 
            index='test_program', 
            columns='config', 
            aggfunc='mean'
        )
        # 按配置顺序重新排列列
        memory_summary = memory_summary[self.configurations]
        print(memory_summary.round(2))
        
        # 3. 安全检查开销分析
        print("\n3. 安全检查开销分析 (相对于基线 %)")
        print("-" * 60)
        
        if not overhead_df.empty:
            time_overhead_summary = overhead_df.pivot_table(
                values='time_overhead_percent',
                index='test_program', 
                columns='config_type',
                aggfunc='mean'
            )
            print("时间开销:")
            print(time_overhead_summary.round(1))
            
            memory_overhead_summary = overhead_df.pivot_table(
                values='memory_overhead_percent',
                index='test_program', 
                columns='config_type',
                aggfunc='mean'
            )
            print("\n内存开销:")
            print(memory_overhead_summary.round(1))
            
            # 计算平均开销
            valid_time_overhead = overhead_df[overhead_df['time_overhead_percent'] != float('inf')]
            valid_memory_overhead = overhead_df[overhead_df['memory_overhead_percent'] != float('inf')]
            
            if not valid_time_overhead.empty:
                avg_time_overhead = valid_time_overhead.groupby('config_type')['time_overhead_percent'].mean()
                print(f"\n平均时间开销:")
                for config_type, overhead in avg_time_overhead.items():
                    print(f"  {config_type:20}: {overhead:6.1f}%")
            
            if not valid_memory_overhead.empty:
                avg_memory_overhead = valid_memory_overhead.groupby('config_type')['memory_overhead_percent'].mean()
                print(f"\n平均内存开销:")
                for config_type, overhead in avg_memory_overhead.items():
                    print(f"  {config_type:20}: {overhead:6.1f}%")
        
        # 4. 成功率统计 - 按配置顺序排列
        print("\n4. 测试成功率 (%)")
        print("-" * 60)
        success_summary = df.pivot_table(
            values='success_rate',
            index='test_program',
            columns='config', 
            aggfunc='mean'
        )
        # 按配置顺序重新排列列
        success_summary = success_summary[self.configurations]
        print(success_summary.round(1))
    
    def create_performance_charts(self, df, overhead_df):
        """创建性能分析图表"""
        print("\n生成性能分析图表...")
        
        # 设置图表样式
        plt.style.use('default')
        fig = plt.figure(figsize=(20, 12))
        fig.suptitle('WARDuino Security Performance Analysis', fontsize=16, fontweight='bold')
        
        # 1. 执行时间对比 - 按配置顺序排列
        ax1 = plt.subplot(2, 2, 1)
        time_data = []
        for _, row in df.iterrows():
            if row['avg_time_ms'] != float('inf'):
                time_data.append({
                    'Config': row['config'],
                    'Test Program': row['test_program'].replace('.wasm', ''),
                    'Execution Time (ms)': row['avg_time_ms'],
                    'Config Order': self.config_order.get(row['config'], 5)
                })
        
        if time_data:
            time_df = pd.DataFrame(time_data)
            # 按配置顺序排序
            time_df = time_df.sort_values('Config Order')
            sns.barplot(data=time_df, x='Test Program', y='Execution Time (ms)', hue='Config', ax=ax1)
            ax1.set_title('Execution Time Comparison', fontsize=12, fontweight='bold')
            ax1.tick_params(axis='x', rotation=45)
            ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # 2. 内存使用对比 - 按配置顺序排列
        ax2 = plt.subplot(2, 2, 2)
        memory_data = []
        for _, row in df.iterrows():
            if row['avg_memory_mb'] > 0:
                memory_data.append({
                    'Config': row['config'],
                    'Test Program': row['test_program'].replace('.wasm', ''),
                    'Memory Usage (MB)': row['avg_memory_mb'],
                    'Config Order': self.config_order.get(row['config'], 5)
                })
        
        if memory_data:
            memory_df = pd.DataFrame(memory_data)
            # 按配置顺序排序
            memory_df = memory_df.sort_values('Config Order')
            sns.barplot(data=memory_df, x='Test Program', y='Memory Usage (MB)', hue='Config', ax=ax2)
            ax2.set_title('Memory Usage Comparison', fontsize=12, fontweight='bold')
            ax2.tick_params(axis='x', rotation=45)
            ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # 3. 时间开销分析 - 修复饼图错误，改为柱状图
        ax3 = plt.subplot(2, 2, 3)
        if not overhead_df.empty:
            valid_time_overhead = overhead_df[overhead_df['time_overhead_percent'] != float('inf')]
            if not valid_time_overhead.empty:
                # 计算每个配置类型的平均时间开销
                avg_time_by_config = valid_time_overhead.groupby('config_type')['time_overhead_percent'].mean().reset_index()
                # 添加配置顺序用于排序
                config_order_map = {
                    'Memory Protection': 1,
                    'Stack Protection': 2,
                    'Address Sanitizer': 3,
                    'Full Protection': 4
                }
                avg_time_by_config['Order'] = avg_time_by_config['config_type'].map(config_order_map)
                avg_time_by_config = avg_time_by_config.sort_values('Order')
                
                # 只使用正值的开销数据
                positive_overhead = avg_time_by_config[avg_time_by_config['time_overhead_percent'] > 0]
                
                if not positive_overhead.empty:
                    colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']
                    bars = ax3.bar(positive_overhead['config_type'], positive_overhead['time_overhead_percent'], 
                                  color=colors[:len(positive_overhead)])
                    ax3.set_title('Time Overhead of Security Checks', fontsize=12, fontweight='bold')
                    ax3.set_ylabel('Time Overhead (%)')
                    ax3.tick_params(axis='x', rotation=45)
                    
                    # 在柱子上添加数值标签
                    for bar in bars:
                        height = bar.get_height()
                        ax3.text(bar.get_x() + bar.get_width()/2., height + 1,
                                f'{height:.1f}%', ha='center', va='bottom')
        
        # 4. 内存开销分析
        ax4 = plt.subplot(2, 2, 4)
        if not overhead_df.empty:
            valid_memory_overhead = overhead_df[overhead_df['memory_overhead_percent'] != float('inf')]
            if not valid_memory_overhead.empty:
                # 计算每个配置类型的平均内存开销
                avg_memory_by_config = valid_memory_overhead.groupby('config_type')['memory_overhead_percent'].mean().reset_index()
                # 添加配置顺序用于排序
                avg_memory_by_config['Order'] = avg_memory_by_config['config_type'].map(config_order_map)
                avg_memory_by_config = avg_memory_by_config.sort_values('Order')
                
                # 只使用正值的开销数据
                positive_memory_overhead = avg_memory_by_config[avg_memory_by_config['memory_overhead_percent'] > 0]
                
                if not positive_memory_overhead.empty:
                    colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']
                    bars = ax4.bar(positive_memory_overhead['config_type'], positive_memory_overhead['memory_overhead_percent'], 
                                  color=colors[:len(positive_memory_overhead)])
                    ax4.set_title('Memory Overhead of Security Checks', fontsize=12, fontweight='bold')
                    ax4.set_ylabel('Memory Overhead (%)')
                    ax4.tick_params(axis='x', rotation=45)
                    
                    # 在柱子上添加数值标签
                    for bar in bars:
                        height = bar.get_height()
                        ax4.text(bar.get_x() + bar.get_width()/2., height + 1,
                                f'{height:.1f}%', ha='center', va='bottom')
        
        plt.tight_layout()
        
        # 保存图表
        chart_path = os.path.join(self.work_dir, "warduino_security_performance_analysis.png")
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"图表已保存: {chart_path}")
        
        # 生成详细数据报告
        self.generate_detailed_report(df, overhead_df)
    
    def generate_detailed_report(self, df, overhead_df):
        """生成详细数据报告"""
        report_path = os.path.join(self.work_dir, "detailed_security_performance_report.md")
        
        with open(report_path, 'w') as f:
            f.write("# WARDuino安全检查详细性能报告\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 执行时间详情 - 按配置顺序排列
            f.write("## 执行时间详情 (毫秒)\n\n")
            f.write("| 测试程序 | 基线 | 内存保护 | 栈保护 | 地址消毒剂 | 全保护 |\n")
            f.write("|----------|------|----------|--------|------------|--------|\n")
            
            for test_program in df['test_program'].unique():
                row_data = [test_program.replace('.wasm', '')]
                for config in self.configurations:  # 按配置顺序
                    data = df[(df['test_program'] == test_program) & (df['config'] == config)]
                    if not data.empty and data.iloc[0]['avg_time_ms'] != float('inf'):
                        row_data.append(f"{data.iloc[0]['avg_time_ms']:.2f}")
                    else:
                        row_data.append("超时/错误")
                f.write("| " + " | ".join(row_data) + " |\n")
            
            # 内存使用详情 - 按配置顺序排列
            f.write("\n## 内存使用详情 (MB)\n\n")
            f.write("| 测试程序 | 基线 | 内存保护 | 栈保护 | 地址消毒剂 | 全保护 |\n")
            f.write("|----------|------|----------|--------|------------|--------|\n")
            
            for test_program in df['test_program'].unique():
                row_data = [test_program.replace('.wasm', '')]
                for config in self.configurations:  # 按配置顺序
                    data = df[(df['test_program'] == test_program) & (df['config'] == config)]
                    if not data.empty and data.iloc[0]['avg_memory_mb'] > 0:
                        row_data.append(f"{data.iloc[0]['avg_memory_mb']:.2f}")
                    else:
                        row_data.append("N/A")
                f.write("| " + " | ".join(row_data) + " |\n")
            
            # 开销分析
            f.write("\n## 安全检查开销分析\n\n")
            if not overhead_df.empty:
                f.write("| 检查类型 | 平均时间开销 | 平均内存开销 | 最大时间开销 | 最大内存开销 |\n")
                f.write("|----------|--------------|--------------|--------------|--------------|\n")
                
                valid_overhead = overhead_df[(overhead_df['time_overhead_percent'] != float('inf')) & 
                                           (overhead_df['memory_overhead_percent'] != float('inf'))]
                if not valid_overhead.empty:
                    for config_type in ['Memory Protection', 'Stack Protection', 'Address Sanitizer', 'Full Protection']:
                        data = valid_overhead[valid_overhead['config_type'] == config_type]
                        if not data.empty:
                            avg_time = data['time_overhead_percent'].mean()
                            avg_memory = data['memory_overhead_percent'].mean()
                            max_time = data['time_overhead_percent'].max()
                            max_memory = data['memory_overhead_percent'].max()
                            f.write(f"| {config_type} | {avg_time:.1f}% | {avg_memory:.1f}% | {max_time:.1f}% | {max_memory:.1f}% |\n")
            
            # 配置建议
            f.write("\n## 配置建议\n\n")
            f.write("基于测试结果，推荐以下配置策略:\n\n")
            
            config_recommendations = [
                ("高性能场景", "baseline", "无安全检查，性能最优"),
                ("内存安全优先", "memory", "防止内存越界访问，开销适中"), 
                ("栈完整性优先", "stack", "保护返回地址和栈数据，开销较小"),
                ("内存错误检测", "address", "检测use-after-free等内存错误，开销较大"),
                ("全面保护", "full", "所有安全检查，安全性最高，开销最大")
            ]
            
            for scenario, config, reason in config_recommendations:
                f.write(f"- **{scenario}**: `{config}` - {reason}\n")
            
            # 测试环境信息
            f.write("\n## 测试环境信息\n\n")
            f.write(f"- 工作目录: {self.work_dir}\n")
            f.write(f"- WARDuino源码: /home/yuxin/WARDuino-safe\n")
            f.write(f"- 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- 测试配置数: {len(self.configurations)}\n")
            f.write(f"- 测试程序数: {len(df['test_program'].unique())}\n")
            
            # 构建信息
            f.write("\n## 构建信息\n\n")
            for config in self.configurations:
                binary_path = self.get_warduino_binary_path(config)
                if os.path.exists(binary_path):
                    size = os.path.getsize(binary_path) / 1024 / 1024
                    f.write(f"- `{config}`: {size:.2f} MB\n")
        
        print(f"详细报告已生成: {report_path}")

def main():
    """主函数"""
    runner = BenchmarkRunner()
    
    # 检查环境
    if not runner.check_environment():
        print("环境检查失败，请确保:")
        print("1. 已运行 generate_benchmarks.py 生成测试程序")
        print("2. 已运行 build_warduino_configs.sh 编译WARDuino")
        return
    
    # 运行基准测试
    runner.run_all_benchmarks()
    
    # 分析和生成报告
    df, overhead_df = runner.analyze_performance()
    if df is not None:
        runner.generate_comprehensive_report(df, overhead_df)
        runner.create_performance_charts(df, overhead_df)
    
    print("\n🎉 基准测试完成!")
    print("生成的输出文件:")
    print("  - benchmark_results_YYYYMMDD_HHMMSS.json (原始数据)")
    print("  - warduino_security_performance_analysis.png (分析图表)") 
    print("  - detailed_security_performance_report.md (详细报告)")

if __name__ == "__main__":
    main()
