#!/usr/bin/env python3
"""
运行WARDuino基准测试并进行数据分析
使用WARDuino内部性能计数器数据版本
"""

import os
import subprocess
import json
import time
import statistics
import matplotlib
# 设置matplotlib使用非交互式后端
matplotlib.use('Agg')  # 这行很重要，避免图形界面阻塞
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from datetime import datetime
import numpy as np
import re

class BenchmarkRunner:
    def __init__(self):
        self.work_dir = "/home/yuxin/WARDuino_test"
        # 创建results子目录
        self.results_dir = os.path.join(self.work_dir, "results")
        os.makedirs(self.results_dir, exist_ok=True)
        
        # 使用WARDuino基准测试目录
        #self.tests_dir = "/home/yuxin/perform_test/WARDuino_binaries"
        self.tests_dir = "/home/yuxin/WARDuino_benchmarks"
        self.warduino_base_dir = "/home/yuxin/WARDuino-safe"
        self.results = []
        
        self.configurations = [
            "baseline", "memory", "stack", "address", "full"
        ]
        
        self.config_order = {
            'baseline': 0, 'memory': 1, 'stack': 2, 'address': 3, 'full': 4
        }
        
        # 设置matplotlib字体和样式
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        plt.style.use('default')
    
    def get_warduino_binary_path(self, config_name):
        """获取WARDuino二进制文件路径"""
        build_dir = os.path.join(self.warduino_base_dir, f"build-{config_name}")
        binary_path = os.path.join(build_dir, "wdcli")
        return binary_path
    
    def check_environment(self):
        """检查测试环境"""
        print("检查测试环境...")
        
        missing_binaries = []
        for config in self.configurations:
            binary_path = self.get_warduino_binary_path(config)
            if not os.path.exists(binary_path):
                missing_binaries.append(config)
        
        if missing_binaries:
            print(f"❌ 缺失WARDuino二进制文件: {missing_binaries}")
            return False
        
        wasm_files = [f for f in os.listdir(self.tests_dir) if f.endswith('.wasm')]
        if not wasm_files:
            print("❌ 未找到WASM测试文件")
            return False
        
        print(f"✅ 找到WARDuino配置: {len(self.configurations)}个")
        print(f"✅ 找到WASM测试文件: {len(wasm_files)}个")
        print(f"✅ 结果将保存到: {self.results_dir}")
        return True
    
    def parse_performance_counters(self, output):
        """解析WARDuino输出的性能计数器数据"""
        try:
            # 将输出转换为字符串
            output_str = output.decode('utf-8') if isinstance(output, bytes) else str(output)
            
            # 查找性能计数器部分 - 使用更宽松的匹配
            perf_section = None
            lines = output_str.split('\n')
            in_perf_section = False
            perf_lines = []
            
            # 尝试多种可能的性能计数器标记
            perf_markers = [
                "=== FINAL PERFORMANCE COUNTERS ===",
                "FINAL PERFORMANCE COUNTERS",
                "PERFORMANCE COUNTERS",
                "Execution Time:"
            ]
            
            for line in lines:
                # 检查是否进入性能计数器部分
                if any(marker in line for marker in perf_markers):
                    in_perf_section = True
                    perf_lines = []
                    # 如果这一行包含性能计数器标记，也添加到解析行中
                    if ":" in line and "===" not in line:
                        perf_lines.append(line.strip())
                    continue
                
                # 检查是否离开性能计数器部分
                if in_perf_section and ("===" in line or "==ERROR:" in line or "SUMMARY:" in line):
                    in_perf_section = False
                    break
                
                # 收集性能计数器行
                if in_perf_section and line.strip():
                    perf_lines.append(line.strip())
            
            # 如果没有找到明确的性能计数器部分，尝试在整个输出中查找关键性能指标
            if not perf_lines:
                # 在整个输出中查找关键性能指标
                for line in lines:
                    if any(keyword in line for keyword in ["Execution Time:", "Total Instructions:", "Memory Accesses:"]):
                        perf_lines.append(line.strip())
            
            if not perf_lines:
                print("⚠️  未找到性能计数器数据")
                return None
            
            # 解析性能计数器数据
            perf_data = {}
            
            for line in perf_lines:
                if ":" in line:
                    try:
                        key, value = line.split(":", 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # 提取数值
                        if key == "Execution Time":
                            # 提取时钟周期数 - 更宽松的匹配
                            match = re.search(r'(\d+)\s*clock cycles', value)
                            if match:
                                perf_data['execution_time_cycles'] = int(match.group(1))
                            else:
                                # 尝试直接提取数字
                                match = re.search(r'(\d+)', value)
                                if match:
                                    perf_data['execution_time_cycles'] = int(match.group(1))
                        elif key == "Total Instructions":
                            perf_data['total_instructions'] = int(value)
                        elif key == "Memory Accesses":
                            perf_data['memory_accesses'] = int(value)
                        elif key == "Stack Operations":
                            perf_data['stack_operations'] = int(value)
                        elif key == "Function Calls":
                            perf_data['function_calls'] = int(value)
                        elif key == "Sanitizer Checks":
                            perf_data['sanitizer_checks'] = int(value)
                        elif key == "Module Size":
                            perf_data['module_size_bytes'] = int(value.split()[0])
                        elif key == "Memory Pages":
                            match = re.search(r'(\d+)\s*\((\d+)\s*bytes\)', value)
                            if match:
                                perf_data['memory_pages'] = int(match.group(1))
                                perf_data['memory_allocated_bytes'] = int(match.group(2))
                        elif key == "Dynamic Allocation":
                            perf_data['dynamic_allocation_bytes'] = int(value.split()[0])
                        elif key == "Total Estimated":
                            perf_data['total_memory_bytes'] = int(value.split()[0])
                    except Exception as e:
                        print(f"解析行 '{line}' 时出错: {e}")
                        continue
            
            # 检查是否成功解析了关键数据
            if 'execution_time_cycles' not in perf_data:
                print("⚠️  未找到执行时间数据")
                return None
                
            return perf_data
            
        except Exception as e:
            print(f"解析性能计数器失败: {e}")
            return None
    
    def run_single_test(self, config_name, wasm_file, iterations=10):
        """运行单个测试配置，使用WARDuino内部性能计数器"""
        warduino_binary = self.get_warduino_binary_path(config_name)
        wasm_path = os.path.join(self.tests_dir, wasm_file)
        
        print(f"  测试: {config_name:15} - {wasm_file:20}", end="")
        
        execution_times = []
        memory_usages = []
        all_perf_data = []
        error_messages = []
        
        for i in range(iterations):
            try:
                # 运行WARDuino并捕获输出
                result = subprocess.run(
                    [warduino_binary, wasm_path, "--no-debug", "--invoke", "start"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=self.work_dir,
                    timeout=30  # 30秒超时
                )
                
                # 检查是否有错误输出，但继续尝试解析性能计数器
                if result.stderr:
                    stderr_output = result.stderr.decode('utf-8')
                    if stderr_output.strip():
                        error_messages.append(stderr_output[:200])  # 保存错误信息但不中断
                
                # 解析性能计数器 - 即使有错误信息也尝试解析
                perf_data = self.parse_performance_counters(result.stdout)
                
                # 如果stdout中没有找到性能计数器，尝试在stderr中查找
                if not perf_data and result.stderr:
                    perf_data = self.parse_performance_counters(result.stderr)
                
                if perf_data and 'execution_time_cycles' in perf_data:
                    execution_times.append(perf_data['execution_time_cycles'])
                    memory_usages.append(perf_data.get('total_memory_bytes', 0))
                    all_perf_data.append(perf_data)
                    print(" ✅", end="")
                else:
                    print(" ❌ 无性能数据", end="")
                    # 保存原始输出以便调试
                    debug_file = os.path.join(self.results_dir, f"debug_{config_name}_{wasm_file}_{i}.txt")
                    #with open(debug_file, 'w') as f:
                        #f.write("=== STDOUT ===\n")
                        #f.write(result.stdout.decode('utf-8'))
                        #f.write("\n=== STDERR ===\n")
                        #f.write(result.stderr.decode('utf-8'))
                    execution_times.append(float('inf'))
                    memory_usages.append(0)
                
            except subprocess.TimeoutExpired:
                print(" ⏰ 超时", end="")
                execution_times.append(float('inf'))
                memory_usages.append(0)
            except Exception as e:
                print(f" ❌ 错误: {e}", end="")
                execution_times.append(float('inf'))
                memory_usages.append(0)
        
        # 如果有错误信息但成功获取了性能数据，显示警告但不标记为失败
        if error_messages and execution_times and any(t != float('inf') for t in execution_times):
            print(f" ⚠️ 有错误但获取了数据", end="")
        
        # 计算统计信息
        valid_times = [t for t in execution_times if t != float('inf')]
        valid_memory = [m for i, m in enumerate(memory_usages) if execution_times[i] != float('inf')]
        
        if valid_times:
            avg_time = statistics.mean(valid_times)
            std_time = statistics.stdev(valid_times) if len(valid_times) > 1 else 0
            avg_memory = statistics.mean(valid_memory) if valid_memory else 0
            std_memory = statistics.stdev(valid_memory) if len(valid_memory) > 1 else 0
            success_rate = len(valid_times) / iterations * 100
            
            # 收集性能计数器数据
            if all_perf_data:
                avg_instructions = statistics.mean([d.get('total_instructions', 0) for d in all_perf_data])
                std_instructions = statistics.stdev([d.get('total_instructions', 0) for d in all_perf_data]) if len(all_perf_data) > 1 else 0
                avg_memory_accesses = statistics.mean([d.get('memory_accesses', 0) for d in all_perf_data])
                std_memory_accesses = statistics.stdev([d.get('memory_accesses', 0) for d in all_perf_data]) if len(all_perf_data) > 1 else 0
                avg_stack_ops = statistics.mean([d.get('stack_operations', 0) for d in all_perf_data])
                std_stack_ops = statistics.stdev([d.get('stack_operations', 0) for d in all_perf_data]) if len(all_perf_data) > 1 else 0
                avg_function_calls = statistics.mean([d.get('function_calls', 0) for d in all_perf_data])
                std_function_calls = statistics.stdev([d.get('function_calls', 0) for d in all_perf_data]) if len(all_perf_data) > 1 else 0
            else:
                avg_instructions = std_instructions = avg_memory_accesses = std_memory_accesses = 0
                avg_stack_ops = std_stack_ops = avg_function_calls = std_function_calls = 0
        else:
            avg_time = float('inf')
            std_time = 0
            avg_memory = 0
            std_memory = 0
            success_rate = 0
            avg_instructions = std_instructions = avg_memory_accesses = std_memory_accesses = 0
            avg_stack_ops = std_stack_ops = avg_function_calls = std_function_calls = 0
        
        print(f" | 时间: {avg_time:8.2f}周期 | 内存: {avg_memory/1024/1024:6.2f}MB | 成功率: {success_rate:5.1f}%")
        
        # 保存错误信息到结果中
        result_data = {
            'config': config_name,
            'test_program': wasm_file,
            'avg_time_cycles': avg_time,
            'std_time_cycles': std_time,
            'avg_memory_bytes': avg_memory,
            'std_memory_bytes': std_memory,
            'avg_memory_mb': avg_memory / (1024 * 1024),
            'std_memory_mb': std_memory / (1024 * 1024),
            'success_rate': success_rate,
            'iterations': len(valid_times),
            'total_iterations': iterations,
            'avg_instructions': avg_instructions,
            'std_instructions': std_instructions,
            'avg_memory_accesses': avg_memory_accesses,
            'std_memory_accesses': std_memory_accesses,
            'avg_stack_operations': avg_stack_ops,
            'std_stack_operations': std_stack_ops,
            'avg_function_calls': avg_function_calls,
            'std_function_calls': std_function_calls
        }
        
        # 如果有错误信息但成功运行，记录错误信息但不标记为失败
        if error_messages and len(valid_times) > 0:
            result_data['has_errors'] = True
            result_data['error_count'] = len(error_messages)
            result_data['sample_error'] = error_messages[0]  # 保存一个样本错误信息
        
        return result_data
    
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
        
        self.save_raw_results()
    
    def save_raw_results(self):
        """保存原始测试结果到results目录"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(self.results_dir, f"benchmark_results_{timestamp}.json")
        
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
                baseline_times[test_program] = baseline_data.iloc[0]['avg_time_cycles']
                baseline_memory[test_program] = baseline_data.iloc[0]['avg_memory_bytes']
        
        # 计算相对开销
        for test_program in df['test_program'].unique():
            if test_program in baseline_times:
                baseline_time = baseline_times[test_program]
                baseline_mem = baseline_memory[test_program]
                
                for config in ['memory', 'stack', 'address', 'full']:
                    config_data = df[(df['config'] == config) & (df['test_program'] == test_program)]
                    
                    if not config_data.empty and baseline_time != float('inf'):
                        config_time = config_data.iloc[0]['avg_time_cycles']
                        config_memory = config_data.iloc[0]['avg_memory_bytes']
                        
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
        
        # 性能对比表格
        print("\n1. 执行时间对比 (时钟周期)")
        print("-" * 80)
        time_summary = df.pivot_table(
            values='avg_time_cycles', 
            index='test_program', 
            columns='config', 
            aggfunc='mean'
        )
        time_summary = time_summary[self.configurations]
        print(time_summary.round(0))
        
        print("\n2. 内存使用对比 (MB)")
        print("-" * 80)
        memory_summary = df.pivot_table(
            values='avg_memory_mb', 
            index='test_program', 
            columns='config', 
            aggfunc='mean'
        )
        memory_summary = memory_summary[self.configurations]
        print(memory_summary.round(2))
        
        print("\n3. 测试成功率 (%)")
        print("-" * 80)
        success_summary = df.pivot_table(
            values='success_rate',
            index='test_program',
            columns='config', 
            aggfunc='mean'
        )
        success_summary = success_summary[self.configurations]
        print(success_summary.round(1))
        
        # 指令统计
        print("\n4. 指令执行统计")
        print("-" * 80)
        instruction_summary = df.groupby('config').agg({
            'avg_instructions': 'mean',
            'avg_memory_accesses': 'mean',
            'avg_stack_operations': 'mean',
            'avg_function_calls': 'mean'
        }).round(0)
        print(instruction_summary)
    
    def create_performance_charts(self, df, overhead_df):
        """创建性能分析图表，保存到results目录"""
        print("\n生成性能分析图表...")
        
        try:
            # 创建图表：执行时间对比
            plt.figure(figsize=(15, 12))
            
            # 1. 执行时间对比
            plt.subplot(3, 2, 1)
            time_data = []
            for _, row in df.iterrows():
                if row['avg_time_cycles'] != float('inf'):
                    time_data.append({
                        'Config': row['config'],
                        'Test Program': row['test_program'].replace('.wasm', ''),
                        'Execution Time (cycles)': row['avg_time_cycles'],
                        'Config Order': self.config_order.get(row['config'], 5)
                    })
            
            if time_data:
                time_df = pd.DataFrame(time_data)
                time_df = time_df.sort_values('Config Order')
                
                unique_programs = time_df['Test Program'].unique()
                configs = time_df['Config'].unique()
                
                x = np.arange(len(unique_programs))
                width = 0.15
                
                for i, config in enumerate(configs):
                    config_data = time_df[time_df['Config'] == config]
                    times = []
                    for program in unique_programs:
                        program_data = config_data[config_data['Test Program'] == program]
                        if not program_data.empty:
                            times.append(program_data.iloc[0]['Execution Time (cycles)'])
                        else:
                            times.append(0)
                    
                    plt.bar(x + i * width, times, width, label=config)
                
                plt.xlabel('Test Programs')
                plt.ylabel('Execution Time (clock cycles)')
                plt.title('Execution Time Comparison (Internal Counters)')
                plt.xticks(x + width * 2, unique_programs, rotation=45)
                plt.legend()
                plt.grid(True, alpha=0.3)
            
            # 2. 内存使用对比
            plt.subplot(3, 2, 2)
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
                memory_df = memory_df.sort_values('Config Order')
                
                unique_programs = memory_df['Test Program'].unique()
                configs = memory_df['Config'].unique()
                
                x = np.arange(len(unique_programs))
                width = 0.15
                
                for i, config in enumerate(configs):
                    config_data = memory_df[memory_df['Config'] == config]
                    memories = []
                    for program in unique_programs:
                        program_data = config_data[config_data['Test Program'] == program]
                        if not program_data.empty:
                            memories.append(program_data.iloc[0]['Memory Usage (MB)'])
                        else:
                            memories.append(0)
                    
                    plt.bar(x + i * width, memories, width, label=config)
                
                plt.xlabel('Test Programs')
                plt.ylabel('Memory Usage (MB)')
                plt.title('Memory Usage Comparison')
                plt.xticks(x + width * 2, unique_programs, rotation=45)
                plt.legend()
                plt.grid(True, alpha=0.3)
            
            # 3. 时间开销
            plt.subplot(3, 2, 3)
            if not overhead_df.empty:
                valid_time_overhead = overhead_df[overhead_df['time_overhead_percent'] != float('inf')]
                if not valid_time_overhead.empty:
                    avg_time_by_config = valid_time_overhead.groupby('config_type')['time_overhead_percent'].mean()
                    
                    config_types = ['Memory Protection', 'Stack Protection', 'Address Sanitizer', 'Full Protection']
                    overhead_values = []
                    
                    for config_type in config_types:
                        if config_type in avg_time_by_config:
                            overhead_values.append(avg_time_by_config[config_type])
                        else:
                            overhead_values.append(0)
                    
                    bars = plt.bar(config_types, overhead_values, color=['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4'])
                    plt.ylabel('Time Overhead (%)')
                    plt.title('Average Time Overhead (vs Baseline)')
                    plt.xticks(rotation=45)
                    plt.grid(True, alpha=0.3)
                    
                    for bar in bars:
                        height = bar.get_height()
                        if height > 0:
                            plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                                    f'{height:.1f}%', ha='center', va='bottom')
            
            # 4. 内存开销
            plt.subplot(3, 2, 4)
            if not overhead_df.empty:
                valid_memory_overhead = overhead_df[overhead_df['memory_overhead_percent'] != float('inf')]
                if not valid_memory_overhead.empty:
                    avg_memory_by_config = valid_memory_overhead.groupby('config_type')['memory_overhead_percent'].mean()
                    
                    config_types = ['Memory Protection', 'Stack Protection', 'Address Sanitizer', 'Full Protection']
                    memory_overhead_values = []
                    
                    for config_type in config_types:
                        if config_type in avg_memory_by_config:
                            memory_overhead_values.append(avg_memory_by_config[config_type])
                        else:
                            memory_overhead_values.append(0)
                    
                    bars = plt.bar(config_types, memory_overhead_values, color=['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4'])
                    plt.ylabel('Memory Overhead (%)')
                    plt.title('Average Memory Overhead (vs Baseline)')
                    plt.xticks(rotation=45)
                    plt.grid(True, alpha=0.3)
                    
                    for bar in bars:
                        height = bar.get_height()
                        if height > 0:
                            plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                                    f'{height:.1f}%', ha='center', va='bottom')
            
            # 5. 指令执行统计
            plt.subplot(3, 2, 5)
            instruction_data = []
            for _, row in df.iterrows():
                if row['avg_instructions'] > 0:
                    instruction_data.append({
                        'Config': row['config'],
                        'Instructions (millions)': row['avg_instructions'] / 1e6,
                        'Memory Accesses (millions)': row['avg_memory_accesses'] / 1e6,
                        'Function Calls (thousands)': row['avg_function_calls'] / 1e3,
                        'Config Order': self.config_order.get(row['config'], 5)
                    })
            
            if instruction_data:
                instr_df = pd.DataFrame(instruction_data)
                instr_df = instr_df.groupby('Config').mean().reset_index()
                instr_df = instr_df.sort_values('Config Order')
                
                x = np.arange(len(instr_df))
                width = 0.25
                
                plt.bar(x - width, instr_df['Instructions (millions)'], width, label='Instructions', color='#ff6b6b')
                plt.bar(x, instr_df['Memory Accesses (millions)'], width, label='Memory Accesses', color='#4ecdc4')
                plt.bar(x + width, instr_df['Function Calls (thousands)'], width, label='Function Calls', color='#45b7d1')
                
                plt.xlabel('Configuration')
                plt.ylabel('Count')
                plt.title('Instruction Execution Statistics')
                plt.xticks(x, instr_df['Config'], rotation=45)
                plt.legend()
                plt.grid(True, alpha=0.3)
            
            # 6. 配置性能对比
            plt.subplot(3, 2, 6)
            if not overhead_df.empty:
                valid_data = overhead_df[
                    (overhead_df['time_overhead_percent'] != float('inf')) & 
                    (overhead_df['memory_overhead_percent'] != float('inf'))
                ]
                
                if not valid_data.empty:
                    config_summary = valid_data.groupby('config_type').agg({
                        'time_overhead_percent': 'mean',
                        'memory_overhead_percent': 'mean'
                    }).reset_index()
                    
                    x = np.arange(len(config_summary))
                    width = 0.35
                    
                    plt.bar(x - width/2, config_summary['time_overhead_percent'], width, 
                           label='Time Overhead', color='#ff6b6b')
                    plt.bar(x + width/2, config_summary['memory_overhead_percent'], width, 
                           label='Memory Overhead', color='#4ecdc4')
                    
                    plt.xlabel('Security Configuration')
                    plt.ylabel('Overhead (%)')
                    plt.title('Security Check Overhead Comparison')
                    plt.xticks(x, config_summary['config_type'], rotation=45)
                    plt.legend()
                    plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # 保存图表到results目录
            chart_path = os.path.join(self.results_dir, "warduino_performance_analysis.png")
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"性能分析图表已保存: {chart_path}")
            
        except Exception as e:
            print(f"图表生成失败: {e}")
            import traceback
            traceback.print_exc()
    
    def generate_detailed_report(self, df, overhead_df):
        """生成详细数据报告到results目录"""
        try:
            report_path = os.path.join(self.results_dir, "detailed_performance_report.md")
            
            with open(report_path, 'w') as f:
                f.write("# WARDuino安全检查详细性能报告\n\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"结果目录: {self.results_dir}\n\n")
                f.write("**注意**: 所有时间数据来自WARDuino内部性能计数器（时钟周期）\n")
                f.write("**格式**: 平均值 ± 标准差（基于成功运行的次数）\n")
                f.write("**策略**: 即使有内存泄漏错误，只要能获取性能数据就视为成功运行\n\n")
                
                # 执行时间详情（包含标准差）
                f.write("## 执行时间详情 (时钟周期)\n\n")
                f.write("| 测试程序 | 基线 | 内存保护 | 栈保护 | 地址消毒剂 | 全保护 |\n")
                f.write("|----------|------|----------|--------|------------|--------|\n")
                
                for test_program in df['test_program'].unique():
                    row_data = [test_program.replace('.wasm', '')]
                    for config in self.configurations:
                        data = df[(df['test_program'] == test_program) & (df['config'] == config)]
                        if not data.empty and data.iloc[0]['avg_time_cycles'] != float('inf'):
                            avg = data.iloc[0]['avg_time_cycles']
                            std = data.iloc[0]['std_time_cycles']
                            row_data.append(f"{avg:,.0f} ± {std:,.0f}")
                        else:
                            row_data.append("超时/错误")
                    f.write("| " + " | ".join(row_data) + " |\n")
                
                # 内存使用详情（包含标准差）
                f.write("\n## 内存使用详情 (MB)\n\n")
                f.write("| 测试程序 | 基线 | 内存保护 | 栈保护 | 地址消毒剂 | 全保护 |\n")
                f.write("|----------|------|----------|--------|------------|--------|\n")
                
                for test_program in df['test_program'].unique():
                    row_data = [test_program.replace('.wasm', '')]
                    for config in self.configurations:
                        data = df[(df['test_program'] == test_program) & (df['config'] == config)]
                        if not data.empty and data.iloc[0]['avg_memory_mb'] > 0:
                            avg = data.iloc[0]['avg_memory_mb']
                            std = data.iloc[0]['std_memory_mb']
                            row_data.append(f"{avg:.2f} ± {std:.2f}")
                        else:
                            row_data.append("N/A")
                    f.write("| " + " | ".join(row_data) + " |\n")
                
                # 成功率详情
                f.write("\n## 测试成功率 (%)\n\n")
                f.write("| 测试程序 | 基线 | 内存保护 | 栈保护 | 地址消毒剂 | 全保护 |\n")
                f.write("|----------|------|----------|--------|------------|--------|\n")
                
                for test_program in df['test_program'].unique():
                    row_data = [test_program.replace('.wasm', '')]
                    for config in self.configurations:
                        data = df[(df['test_program'] == test_program) & (df['config'] == config)]
                        if not data.empty:
                            row_data.append(f"{data.iloc[0]['success_rate']:.1f}")
                        else:
                            row_data.append("N/A")
                    f.write("| " + " | ".join(row_data) + " |\n")
                
                # 指令执行统计（包含标准差）
                f.write("\n## 指令执行统计\n\n")
                f.write("| 配置 | 平均指令数 | 平均内存访问 | 平均栈操作 | 平均函数调用 |\n")
                f.write("|------|------------|-------------|-----------|-------------|\n")
                
                for config in self.configurations:
                    data = df[df['config'] == config]
                    if not data.empty:
                        avg_instr = data['avg_instructions'].mean()
                        std_instr = data['std_instructions'].mean()
                        avg_mem_acc = data['avg_memory_accesses'].mean()
                        std_mem_acc = data['std_memory_accesses'].mean()
                        avg_stack_ops = data['avg_stack_operations'].mean()
                        std_stack_ops = data['std_stack_operations'].mean()
                        avg_func_calls = data['avg_function_calls'].mean()
                        std_func_calls = data['std_function_calls'].mean()
                        
                        f.write(f"| {config} | {avg_instr:,.0f} ± {std_instr:,.0f} | {avg_mem_acc:,.0f} ± {std_mem_acc:,.0f} | {avg_stack_ops:,.0f} ± {std_stack_ops:,.0f} | {avg_func_calls:,.0f} ± {std_func_calls:,.0f} |\n")
                
                # 开销分析
                f.write("\n## 安全检查开销分析\n\n")
                if not overhead_df.empty:
                    f.write("| 检查类型 | 平均时间开销 | 平均内存开销 | 最大时间开销 | 最大内存开销 |\n")
                    f.write("|----------|--------------|--------------|--------------|--------------|\n")
                    
                    valid_overhead = overhead_df[
                        (overhead_df['time_overhead_percent'] != float('inf')) & 
                        (overhead_df['memory_overhead_percent'] != float('inf'))
                    ]
                    
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
                recommendations = [
                    ("高性能场景", "baseline", "无安全检查，性能最优"),
                    ("内存安全优先", "memory", "防止内存越界访问，开销适中"), 
                    ("栈完整性优先", "stack", "保护返回地址和栈数据，开销较小"),
                    ("内存错误检测", "address", "检测use-after-free等内存错误，开销较大"),
                    ("全面保护", "full", "所有安全检查，安全性最高，开销最大")
                ]
                
                for scenario, config, reason in recommendations:
                    f.write(f"- **{scenario}**: `{config}` - {reason}\n")
                
                # 测试策略说明
                f.write("\n## 测试策略说明\n\n")
                f.write("- 即使测试过程中出现内存泄漏或其他运行时错误，只要能够获取性能计数器数据，就视为成功运行\n")
                f.write("- 这种策略确保了在安全检查可能触发误报的情况下，仍然能够收集性能数据\n")
                f.write("- 成功率反映了能够成功获取性能数据的测试比例\n")
                f.write("- 带有警告标志(⚠️)的测试表示有错误信息但成功获取了数据\n")
                
                # 生成的文件列表
                f.write("\n## 生成的文件\n\n")
                result_files = [f for f in os.listdir(self.results_dir) if f.endswith(('.png', '.json', '.md'))]
                for file in sorted(result_files):
                    file_path = os.path.join(self.results_dir, file)
                    file_size = os.path.getsize(file_path) / 1024  # KB
                    f.write(f"- `{file}` ({file_size:.1f} KB)\n")
            
            print(f"详细报告已生成: {report_path}")
            return report_path
            
        except Exception as e:
            print(f"生成详细报告时出错: {e}")
            import traceback
            traceback.print_exc()
            return None

def main():
    """主函数"""
    runner = BenchmarkRunner()
    
    # 检查环境
    if not runner.check_environment():
        print("环境检查失败，请确保:")
        print("1. WARDuino基准测试目录存在: /home/yuxin/WARDuino_benchmarks")
        print("2. 已运行 build_warduino_configs.sh 编译WARDuino")
        return
    
    try:
        # 运行基准测试
        runner.run_all_benchmarks()
        
        # 分析和生成报告
        df, overhead_df = runner.analyze_performance()
        if df is not None:
            runner.generate_comprehensive_report(df, overhead_df)
            runner.create_performance_charts(df, overhead_df)
            runner.generate_detailed_report(df, overhead_df)
        
        # 显示生成的文件列表
        print("\n" + "="*80)
        print("生成的文件列表:")
        print("="*80)
        result_files = [f for f in os.listdir(runner.results_dir) if f.endswith(('.png', '.json', '.md'))]
        for file in sorted(result_files):
            file_path = os.path.join(runner.results_dir, file)
            file_size = os.path.getsize(file_path) / 1024  # KB
            print(f"  - {file} ({file_size:.1f} KB)")
        
        print(f"\n🎉 基准测试完成! 所有结果已保存到: {runner.results_dir}")
        
    except Exception as e:
        print(f"基准测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
