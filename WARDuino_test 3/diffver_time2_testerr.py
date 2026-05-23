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
        self.tests_dir = "/home/yuxin/WARDuino_test/WARDuino_bin"
        self.warduino_base_dir = "/home/yuxin/WARDuino-safe"
        self.results = []
        
        # 在stack和full之间增加cfi配置
        self.configurations = [
            "baseline", "memory", "stack", "cfi", "address", "full"
        ]
        
        self.config_order = {
            'baseline': 0, 'memory': 1, 'stack': 2, 'cfi': 3, 'address': 4, 'full': 5
        }
        
        # 设置颜色方案 - 为cfi添加颜色
        self.colors = {
            'baseline': '#2E86AB',
            'memory': '#A23B72', 
            'stack': '#F18F01',
            'cfi': '#6A4C93',  # 紫色代表CFI
            'address': '#C73E1D',
            'full': '#3F7CAC'
        }
        
        # 设置matplotlib字体和样式
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        plt.style.use('default')
        sns.set_style("whitegrid")
    
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
    
    def analyze_wasm_module(self, wasm_file):
        """分析WASM模块的导入/导出情况"""
        try:
            # 使用wasm-objdump分析模块
            wasm_path = os.path.join(self.tests_dir, wasm_file)
            result = subprocess.run(
                ['wasm-objdump', '-x', wasm_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            imports = []
            exports = []
            
            lines = result.stdout.split('\n')
            for line in lines:
                if 'import' in line and 'env.' in line:
                    imports.append(line.strip())
                elif 'export' in line:
                    exports.append(line.strip())
            
            # 检查是否有问题导入
            problematic_imports = []
            for imp in imports:
                if any(func in imp for func in ['memset', 'memcpy', 'malloc', 'free']):
                    problematic_imports.append(imp)
            
            return {
                'imports': imports,
                'exports': exports,
                'problematic_imports': problematic_imports,
                'has_problematic_imports': len(problematic_imports) > 0
            }
            
        except Exception as e:
            print(f"分析WASM模块失败: {e}")
            return None
    
    def parse_performance_counters(self, output):
        """解析WARDuino输出的性能计数器数据"""
        try:
            # 处理不同类型的输入
            if output is None:
                return None
                
            # 如果已经是字符串，直接使用
            if isinstance(output, str):
                output_str = output
            # 如果是字节，解码为字符串
            elif isinstance(output, bytes):
                output_str = output.decode('utf-8', errors='ignore')
            else:
                # 其他类型转换为字符串
                output_str = str(output)
            
            # 如果输出为空，直接返回
            if not output_str.strip():
                return None
            
            # 检查是否有缺失系统函数的错误
            missing_primitives = [
                "Could not find primitive memset",
                "Could not find primitive memcpy", 
                "Could not find primitive"
            ]
            
            for primitive_error in missing_primitives:
                if primitive_error in output_str:
                    return {
                        "missing_primitive": primitive_error, 
                        "output": output_str[:500],
                        "type": "missing_import"
                    }
            
            perf_data = {}
            
            # 方法1: 检查新的性能计数器格式 (===PERF_DATA_START=== 和 ===PERF_DATA_END===)
            start_marker = "===PERF_DATA_START==="
            end_marker = "===PERF_DATA_END==="
            
            if start_marker in output_str and end_marker in output_str:
                # 提取性能计数器部分
                start_index = output_str.find(start_marker) + len(start_marker)
                end_index = output_str.find(end_marker)
                perf_section = output_str[start_index:end_index].strip()
                
                # 解析性能计数器数据
                lines = perf_section.split('\n')
                for line in lines:
                    line = line.strip()
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # 提取数值
                        if key == "Execution Time":
                            match = re.search(r'(\d+)\s*clock cycles', value)
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
                        elif key == "CFI Checks":
                            perf_data['cfi_checks'] = int(value)  # 添加CFI检查解析
                        elif key == "Total Estimated":
                            perf_data['total_memory_bytes'] = int(value.split()[0])
            
            # 方法2: 如果没有找到新格式，尝试旧格式
            if not perf_data or 'execution_time_cycles' not in perf_data:
                # 查找执行时间
                time_match = re.search(r'Execution Time:\s*(\d+)\s*clock cycles', output_str)
                if time_match:
                    perf_data['execution_time_cycles'] = int(time_match.group(1))
                
                # 如果找到了执行时间，继续查找其他指标
                if 'execution_time_cycles' in perf_data:
                    # 查找其他性能指标
                    patterns = {
                        'total_instructions': r'Total Instructions:\s*(\d+)',
                        'memory_accesses': r'Memory Accesses:\s*(\d+)',
                        'stack_operations': r'Stack Operations:\s*(\d+)',
                        'function_calls': r'Function Calls:\s*(\d+)',
                        'sanitizer_checks': r'Sanitizer Checks:\s*(\d+)',
                        'cfi_checks': r'CFI Checks:\s*(\d+)',  # 添加CFI检查模式
                        'total_memory_bytes': r'Total Estimated:\s*(\d+)'
                    }
                    
                    for key, pattern in patterns.items():
                        match = re.search(pattern, output_str)
                        if match:
                            perf_data[key] = int(match.group(1))
            
            # 如果成功解析了执行时间，返回数据
            if 'execution_time_cycles' in perf_data:
                return perf_data
            
            return None
                
        except Exception as e:
            return None
    
    def run_single_test(self, config_name, wasm_file, iterations=3):
        """运行单个测试配置"""
        # 先分析WASM模块
        module_analysis = self.analyze_wasm_module(wasm_file)
        
        warduino_binary = self.get_warduino_binary_path(config_name)
        wasm_path = os.path.join(self.tests_dir, wasm_file)
        
        print(f"  测试: {config_name:15} - {wasm_file:20}", end="")
        
        # 如果有问题导入，提前警告
        if module_analysis and module_analysis['has_problematic_imports']:
            print(f" ⚠️ 有外部依赖", end="")
        
        execution_times = []
        memory_usages = []
        all_perf_data = []
        error_messages = []
        missing_primitives = False
        primitive_error_msg = ""

        current_env = os.environ.copy()
        current_env['PYTHONPATH'] = ''
        current_env['LD_LIBRARY_PATH'] = ''
        
        for i in range(iterations):
            try:
                result = subprocess.run(
                    [warduino_binary, wasm_path, "--no-debug", "--invoke", "start"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=self.work_dir,
                    env=current_env,
                    timeout=500
                )
                
                combined_output = result.stdout + result.stderr
                
                if result.stderr:
                    stderr_output = result.stderr.decode('utf-8', errors='ignore')
                    if stderr_output.strip():
                        error_messages.append(stderr_output[:500])
                
                perf_data = self.parse_performance_counters(combined_output)
                
                # 检查是否缺少系统函数
                if perf_data and 'missing_primitive' in perf_data:
                    missing_primitives = True
                    primitive_error_msg = perf_data['missing_primitive']
                    break
                
                if perf_data and 'execution_time_cycles' in perf_data:
                    execution_times.append(perf_data['execution_time_cycles'])
                    memory_usages.append(perf_data.get('total_memory_bytes', 0))
                    all_perf_data.append(perf_data)
                    print(" ✅", end="")
                else:
                    # 检查程序输出，看是否有其他线索
                    output_str = combined_output.decode('utf-8', errors='ignore')
                    if "Checksum:" in output_str or "PERF_DATA" in output_str:
                        # 程序似乎运行了但没有性能计数器
                        print(" ⚠️ 无计数器", end="")
                    else:
                        print(" ❌ 失败", end="")
                    execution_times.append(float('inf'))
                    memory_usages.append(0)
                
            except subprocess.TimeoutExpired:
                print(" ⏰ 超时", end="")
                execution_times.append(float('inf'))
                memory_usages.append(0)
            except Exception as e:
                print(f" 💥 错误", end="")
                execution_times.append(float('inf'))
                memory_usages.append(0)
        
        # 如果检测到缺失系统函数
        if missing_primitives:
            missing_func = primitive_error_msg.split('primitive ')[-1] if 'primitive' in primitive_error_msg else primitive_error_msg
            print(f" ⚠️ 缺失: {missing_func}")
            
            return {
                'config': config_name,
                'test_program': wasm_file,
                'avg_time_cycles': float('inf'),
                'std_time_cycles': 0,
                'avg_memory_bytes': 0,
                'std_memory_bytes': 0,
                'avg_memory_mb': 0,
                'std_memory_mb': 0,
                'success_rate': 0,
                'iterations': 0,
                'total_iterations': iterations,
                'missing_primitive': True,
                'error': primitive_error_msg,
                'module_analysis': module_analysis
            }
        
        # 计算统计信息
        valid_times = [t for t in execution_times if t != float('inf')]
        valid_memory = [m for i, m in enumerate(memory_usages) if execution_times[i] != float('inf')]
        
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
        
        print(f" | 时间: {avg_time:8.2f}周期 | 内存: {avg_memory/1024/1024:6.2f}MB | 成功率: {success_rate:5.1f}%")
        
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
            'module_analysis': module_analysis
        }
        
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
        
        # 计算相对开销 - 包含cfi配置
        for test_program in df['test_program'].unique():
            if test_program in baseline_times:
                baseline_time = baseline_times[test_program]
                baseline_mem = baseline_memory[test_program]
                
                for config in ['memory', 'stack', 'cfi', 'address', 'full']:
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
            'baseline': '基线',
            'memory': '内存保护',
            'stack': '栈保护',
            'cfi': 'CFI保护',  # 添加CFI描述
            'address': '地址消毒剂',
            'full': '全保护'
        }
        return types.get(config, '未知')
    
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
    
    def create_comprehensive_bar_charts(self, df, overhead_df):
        """创建全面的棒状比较图"""
        print("\n生成全面的棒状比较图...")
        
        try:
            # 过滤无效数据
            valid_df = df[df['avg_time_cycles'] != float('inf')]
            if valid_df.empty:
                print("⚠️ 没有有效数据生成图表")
                return
            
            # 1. 所有模块排列一起的运行时间比较
            self._create_all_modules_time_comparison(valid_df)
            
            # 2. 所有模块排列一起的内存使用比较
            self._create_all_modules_memory_comparison(valid_df)
            
            # 3. 每个单独模块的详细比较图
            self._create_individual_module_charts(valid_df)
            
            # 4. 各模块平均结果比较（以baseline为基准）
            self._create_average_comparison_chart(valid_df, overhead_df)
            
            # 5. 成功率比较图
            self._create_success_rate_chart(df)
            
            print("✅ 所有棒状比较图生成完成")
            
        except Exception as e:
            print(f"图表生成失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_all_modules_time_comparison(self, df):
        """创建所有模块运行时间比较图"""
        plt.figure(figsize=(16, 8))  # 稍微加宽以适应更多配置
        
        # 获取所有测试程序
        test_programs = sorted(df['test_program'].unique())
        n_programs = len(test_programs)
        
        # 设置柱状图位置 - 调整宽度以适应更多配置
        x = np.arange(n_programs)
        width = 0.12  # 减小柱状图宽度以容纳更多配置
        spacing = 0.02  # 柱状图间距
        
        # 为每个配置绘制柱状图
        for i, config in enumerate(self.configurations):
            config_data = []
            for program in test_programs:
                program_data = df[(df['test_program'] == program) & (df['config'] == config)]
                if not program_data.empty:
                    config_data.append(program_data.iloc[0]['avg_time_cycles'])
                else:
                    config_data.append(0)
            
            # 计算位置
            positions = x + i * (width + spacing)
            bars = plt.bar(positions, config_data, width, 
                          label=self.get_config_type(config),
                          color=self.colors[config],
                          alpha=0.8)
            
            # 添加数值标签（如果数值不是太大）
            for bar, value in zip(bars, config_data):
                if value > 0:
                    height = bar.get_height()
                    if height < max(config_data) * 0.1:  # 只在柱子上方有足够空间时显示
                        plt.text(bar.get_x() + bar.get_width()/2., height + max(config_data)*0.01,
                                f'{value/1000:.0f}K', ha='center', va='bottom', fontsize=7, rotation=45)
        
        plt.xlabel('测试程序', fontsize=12)
        plt.ylabel('执行时间 (时钟周期)', fontsize=12)
        plt.title('所有测试模块运行时间比较', fontsize=14, fontweight='bold')
        plt.xticks(x + (len(self.configurations)-1)*(width+spacing)/2, 
                  [p.replace('.wasm', '') for p in test_programs], 
                  rotation=45, ha='right')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        chart_path = os.path.join(self.results_dir, "all_modules_time_comparison.png")
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"所有模块运行时间比较图已保存: {chart_path}")
    
    def _create_all_modules_memory_comparison(self, df):
        """创建所有模块内存使用比较图"""
        plt.figure(figsize=(16, 8))
        
        test_programs = sorted(df['test_program'].unique())
        n_programs = len(test_programs)
        
        x = np.arange(n_programs)
        width = 0.12  # 减小宽度
        spacing = 0.02
        
        for i, config in enumerate(self.configurations):
            config_data = []
            for program in test_programs:
                program_data = df[(df['test_program'] == program) & (df['config'] == config)]
                if not program_data.empty:
                    config_data.append(program_data.iloc[0]['avg_memory_mb'])
                else:
                    config_data.append(0)
            
            positions = x + i * (width + spacing)
            bars = plt.bar(positions, config_data, width,
                          label=self.get_config_type(config),
                          color=self.colors[config],
                          alpha=0.8)
            
            # 添加数值标签
            for bar, value in zip(bars, config_data):
                if value > 0:
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height + max(config_data)*0.01,
                            f'{value:.2f}', ha='center', va='bottom', fontsize=7)
        
        plt.xlabel('测试程序', fontsize=12)
        plt.ylabel('内存使用 (MB)', fontsize=12)
        plt.title('所有测试模块内存使用比较', fontsize=14, fontweight='bold')
        plt.xticks(x + (len(self.configurations)-1)*(width+spacing)/2,
                  [p.replace('.wasm', '') for p in test_programs],
                  rotation=45, ha='right')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        chart_path = os.path.join(self.results_dir, "all_modules_memory_comparison.png")
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"所有模块内存使用比较图已保存: {chart_path}")
    
    def _create_individual_module_charts(self, df):
        """为每个模块创建单独的详细比较图"""
        test_programs = sorted(df['test_program'].unique())
        
        for program in test_programs:
            program_data = df[df['test_program'] == program]
            if program_data.empty:
                continue
            
            # 创建子图
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))  # 加宽图表以适应更多配置
            fig.suptitle(f'测试程序: {program.replace(".wasm", "")}', fontsize=14, fontweight='bold')
            
            # 时间比较
            configs = []
            times = []
            times_std = []
            
            for config in self.configurations:
                config_data = program_data[program_data['config'] == config]
                if not config_data.empty:
                    configs.append(self.get_config_type(config))
                    times.append(config_data.iloc[0]['avg_time_cycles'])
                    times_std.append(config_data.iloc[0]['std_time_cycles'])
            
            bars1 = ax1.bar(configs, times, yerr=times_std, 
                           capsize=5, alpha=0.7,
                           color=[self.colors[c] for c in self.configurations if c in [cd['config'] for cd in program_data.to_dict('records')]])
            ax1.set_ylabel('执行时间 (时钟周期)')
            ax1.set_title('执行时间比较')
            ax1.tick_params(axis='x', rotation=45)
            
            # 在柱子上添加数值
            for bar in bars1:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{height/1000:.0f}K', ha='center', va='bottom', fontsize=8)
            
            # 内存比较
            configs = []
            memory = []
            memory_std = []
            
            for config in self.configurations:
                config_data = program_data[program_data['config'] == config]
                if not config_data.empty:
                    configs.append(self.get_config_type(config))
                    memory.append(config_data.iloc[0]['avg_memory_mb'])
                    memory_std.append(config_data.iloc[0]['std_memory_mb'])
            
            bars2 = ax2.bar(configs, memory, yerr=memory_std,
                           capsize=5, alpha=0.7,
                           color=[self.colors[c] for c in self.configurations if c in [cd['config'] for cd in program_data.to_dict('records')]])
            ax2.set_ylabel('内存使用 (MB)')
            ax2.set_title('内存使用比较')
            ax2.tick_params(axis='x', rotation=45)
            
            # 在柱子上添加数值
            for bar in bars2:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{height:.2f}', ha='center', va='bottom', fontsize=8)
            
            plt.tight_layout()
            
            # 保存单个模块图表
            safe_name = program.replace('.wasm', '').replace(' ', '_')
            chart_path = os.path.join(self.results_dir, f"module_{safe_name}_comparison.png")
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
        
        print(f"✅ 已为 {len(test_programs)} 个模块生成单独比较图")
    
    def _create_average_comparison_chart(self, df, overhead_df):
        """创建平均结果比较图（以baseline为基准）"""
        if overhead_df.empty:
            print("⚠️ 没有足够的开销数据生成平均比较图")
            return
        
        plt.figure(figsize=(14, 8))  # 加宽以适应更多配置
        
        # 计算每个配置的平均开销
        avg_overhead = overhead_df.groupby('config')['time_overhead_percent'].mean()
        
        # 创建柱状图
        config_names = [self.get_config_type(config) for config in avg_overhead.index]
        colors = [self.colors[config] for config in avg_overhead.index]
        
        bars = plt.bar(config_names, avg_overhead.values, color=colors, alpha=0.7)
        
        plt.xlabel('配置类型', fontsize=12)
        plt.ylabel('相对于基线的性能开销 (%)', fontsize=12)
        plt.title('各安全检查配置平均性能开销比较\n(以Baseline为基准)', fontsize=14, fontweight='bold')
        
        # 在柱子上添加百分比数值
        for bar, value in zip(bars, avg_overhead.values):
            plt.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1,
                    f'+{value:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        chart_path = os.path.join(self.results_dir, "average_overhead_comparison.png")
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"平均性能开销比较图已保存: {chart_path}")
    
    def _create_success_rate_chart(self, df):
        """创建成功率比较图"""
        plt.figure(figsize=(12, 6))  # 加宽以适应更多配置
        
        # 计算每个配置的平均成功率
        success_rates = []
        config_names = []
        
        for config in self.configurations:
            config_data = df[df['config'] == config]
            if not config_data.empty:
                avg_success = config_data['success_rate'].mean()
                success_rates.append(avg_success)
                config_names.append(self.get_config_type(config))
        
        bars = plt.bar(config_names, success_rates, 
                      color=[self.colors[config] for config in self.configurations],
                      alpha=0.7)
        
        plt.xlabel('配置类型', fontsize=12)
        plt.ylabel('成功率 (%)', fontsize=12)
        plt.title('各配置测试成功率比较', fontsize=14, fontweight='bold')
        plt.ylim(0, 100)
        
        # 在柱子上添加百分比数值
        for bar, rate in zip(bars, success_rates):
            plt.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1,
                    f'{rate:.1f}%', ha='center', va='bottom', fontsize=11)
        
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        chart_path = os.path.join(self.results_dir, "success_rate_comparison.png")
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"成功率比较图已保存: {chart_path}")
    
    def create_performance_charts(self, df, overhead_df):
        """创建性能分析图表 - 保持向后兼容"""
        self.create_comprehensive_bar_charts(df, overhead_df)
    
    def generate_detailed_report(self, df, overhead_df):
        """生成详细数据报告到results目录"""
        try:
            report_path = os.path.join(self.results_dir, "detailed_performance_report.md")
            
            with open(report_path, 'w') as f:
                f.write("# WARDuino安全检查详细性能报告\n\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"结果目录: {self.results_dir}\n\n")
                f.write("**注意**: 所有时间数据来自WARDuino内部性能计数器（时钟周期）\n\n")
                
                # 图表引用
                f.write("## 性能比较图表\n\n")
                f.write("以下图表提供了全面的性能比较分析：\n\n")
                f.write("- `all_modules_time_comparison.png` - 所有模块运行时间并列比较\n")
                f.write("- `all_modules_memory_comparison.png` - 所有模块内存使用并列比较\n")
                f.write("- `module_*_comparison.png` - 各模块单独详细比较\n")
                f.write("- `average_overhead_comparison.png` - 平均性能开销比较（以baseline为基准）\n")
                f.write("- `success_rate_comparison.png` - 测试成功率比较\n\n")
                
                # 执行时间详情 - 更新为包含CFI
                f.write("## 执行时间详情 (时钟周期)\n\n")
                f.write("| 测试程序 | 基线 | 内存保护 | 栈保护 | CFI保护 | 地址消毒剂 | 全保护 |\n")
                f.write("|----------|------|----------|--------|---------|------------|--------|\n")
                
                for test_program in df['test_program'].unique():
                    row_data = [test_program.replace('.wasm', '')]
                    for config in self.configurations:
                        data = df[(df['test_program'] == test_program) & (df['config'] == config)]
                        if not data.empty and data.iloc[0]['avg_time_cycles'] != float('inf'):
                            avg = data.iloc[0]['avg_time_cycles']
                            row_data.append(f"{avg:,.0f}")
                        else:
                            row_data.append("无法运行")
                    f.write("| " + " | ".join(row_data) + " |\n")
                
                # 内存使用详情 - 更新为包含CFI
                f.write("\n## 内存使用详情 (MB)\n\n")
                f.write("| 测试程序 | 基线 | 内存保护 | 栈保护 | CFI保护 | 地址消毒剂 | 全保护 |\n")
                f.write("|----------|------|----------|--------|---------|------------|--------|\n")
                
                for test_program in df['test_program'].unique():
                    row_data = [test_program.replace('.wasm', '')]
                    for config in self.configurations:
                        data = df[(df['test_program'] == test_program) & (df['config'] == config)]
                        if not data.empty and data.iloc[0]['avg_memory_mb'] > 0:
                            avg = data.iloc[0]['avg_memory_mb']
                            row_data.append(f"{avg:.2f}")
                        else:
                            row_data.append("N/A")
                    f.write("| " + " | ".join(row_data) + " |\n")
                
                # 成功率详情 - 更新为包含CFI
                f.write("\n## 测试成功率 (%)\n\n")
                f.write("| 测试程序 | 基线 | 内存保护 | 栈保护 | CFI保护 | 地址消毒剂 | 全保护 |\n")
                f.write("|----------|------|----------|--------|---------|------------|--------|\n")
                
                for test_program in df['test_program'].unique():
                    row_data = [test_program.replace('.wasm', '')]
                    for config in self.configurations:
                        data = df[(df['test_program'] == test_program) & (df['config'] == config)]
                        if not data.empty:
                            row_data.append(f"{data.iloc[0]['success_rate']:.1f}")
                        else:
                            row_data.append("N/A")
                    f.write("| " + " | ".join(row_data) + " |\n")
                
                # 性能开销分析 - 包含CFI
                if not overhead_df.empty:
                    f.write("\n## 性能开销分析 (相对于基线)\n\n")
                    f.write("| 配置 | 平均时间开销 (%) | 平均内存开销 (%) |\n")
                    f.write("|------|------------------|------------------|\n")
                    
                    for config in ['memory', 'stack', 'cfi', 'address', 'full']:
                        config_data = overhead_df[overhead_df['config'] == config]
                        if not config_data.empty:
                            avg_time_overhead = config_data['time_overhead_percent'].mean()
                            avg_memory_overhead = config_data['memory_overhead_percent'].mean()
                            f.write(f"| {self.get_config_type(config)} | +{avg_time_overhead:.1f}% | +{avg_memory_overhead:.1f}% |\n")
                
                # 显示无法运行的测试
                f.write("\n## 无法运行的测试\n\n")
                for _, row in df.iterrows():
                    if row.get('missing_primitive', False) or row['success_rate'] == 0:
                        f.write(f"- **{row['config']} - {row['test_program']}**: {row.get('error', '未知错误')}\n")
            
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
            runner.create_comprehensive_bar_charts(df, overhead_df)  # 使用新的图表生成方法
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
