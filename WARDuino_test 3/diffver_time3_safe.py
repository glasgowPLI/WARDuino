#!/usr/bin/env python3
"""
Run WARDuino benchmark tests and perform data analysis
Using WARDuino internal performance counters data version
"""

import os
import subprocess
import json
import time
import statistics
import matplotlib
# Set matplotlib to use non-interactive backend
matplotlib.use('Agg')  # Important to avoid GUI blocking
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from datetime import datetime
import numpy as np
import re

class BenchmarkRunner:
    def __init__(self):
        self.work_dir = "/home/yuxin/WARDuino_test"
        # Create results subdirectory
        self.results_dir = os.path.join(self.work_dir, "results")
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Use WARDuino benchmark directory
        self.tests_dir = "/home/yuxin/WARDuino_test/WARDuino_bin"
        self.warduino_base_dir = "/home/yuxin/WARDuino-safe"
        self.results = []
        
        # Add CFI configuration between stack and full
        self.configurations = [
            "baseline", "memory", "stack", "cfi", "address", "full"
        ]
        
        self.config_order = {
            'baseline': 0, 'memory': 1, 'stack': 2, 'cfi': 3, 'address': 4, 'full': 5
        }
        
        # Set color scheme - add color for CFI
        self.colors = {
            'baseline': '#2E86AB',
            'memory': '#A23B72', 
            'stack': '#F18F01',
            'cfi': '#6A4C93',  # Purple color for CFI
            'address': '#C73E1D',
            'full': '#3F7CAC'
        }
        
        # Set matplotlib font and style - use English only to avoid font issues
        self._setup_matplotlib()
        plt.style.use('default')
        sns.set_style("whitegrid")
    
    def _setup_matplotlib(self):
        """Set up matplotlib with English fonts only to avoid Chinese font issues"""
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
        plt.rcParams['axes.unicode_minus'] = False
        print("✅ Using English fonts for charts")
    
    def get_warduino_binary_path(self, config_name):
        """Get WARDuino binary file path"""
        build_dir = os.path.join(self.warduino_base_dir, f"build-{config_name}")
        binary_path = os.path.join(build_dir, "wdcli")
        return binary_path
    
    def check_environment(self):
        """Check test environment"""
        print("Checking test environment...")
        
        missing_binaries = []
        for config in self.configurations:
            binary_path = self.get_warduino_binary_path(config)
            if not os.path.exists(binary_path):
                missing_binaries.append(config)
        
        if missing_binaries:
            print(f"❌ Missing WARDuino binaries: {missing_binaries}")
            return False
        
        wasm_files = [f for f in os.listdir(self.tests_dir) if f.endswith('.wasm')]
        if not wasm_files:
            print("❌ No WASM test files found")
            return False
        
        print(f"✅ Found WARDuino configurations: {len(self.configurations)}")
        print(f"✅ Found WASM test files: {len(wasm_files)}")
        print(f"✅ Results will be saved to: {self.results_dir}")
        return True
    
    def analyze_wasm_module(self, wasm_file):
        """Analyze WASM module imports/exports"""
        try:
            # Use wasm-objdump to analyze module
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
            
            # Check for problematic imports
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
            print(f"WASM module analysis failed: {e}")
            return None
    
    def parse_performance_counters(self, output):
        """Parse WARDuino performance counter data - IMPROVED VERSION"""
        try:
            # Handle different input types
            if output is None:
                return None
                
            # If already string, use directly
            if isinstance(output, str):
                output_str = output
            # If bytes, decode to string
            elif isinstance(output, bytes):
                output_str = output.decode('utf-8', errors='ignore')
            else:
                # Convert other types to string
                output_str = str(output)
            
            # If output is empty, return directly
            if not output_str.strip():
                return None
            
            # Check for missing system function errors
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
            
            # Method 1: Check new performance counter format (===PERF_DATA_START=== and ===PERF_DATA_END===)
            start_marker = "===PERF_DATA_START==="
            end_marker = "===PERF_DATA_END==="
            
            if start_marker in output_str and end_marker in output_str:
                # Extract performance counter section
                start_index = output_str.find(start_marker) + len(start_marker)
                end_index = output_str.find(end_marker)
                perf_section = output_str[start_index:end_index].strip()
                
                # Parse performance counter data
                lines = perf_section.split('\n')
                for line in lines:
                    line = line.strip()
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Extract numerical values
                        if key == "Execution Time":
                            # Handle different formats: "12345 clock cycles" or just "12345"
                            match = re.search(r'(\d+)\s*(?:clock cycles)?', value)
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
                            perf_data['cfi_checks'] = int(value)  # Add CFI check parsing
                        elif key == "Total Estimated":
                            # Handle "12345 bytes" format
                            match = re.search(r'(\d+)\s*(?:bytes)?', value)
                            if match:
                                perf_data['total_memory_bytes'] = int(match.group(1))
            
            # Method 2: If new format not found, try old format with regex patterns
            if not perf_data or 'execution_time_cycles' not in perf_data:
                # Find execution time with more flexible pattern
                time_patterns = [
                    r'Execution Time:\s*(\d+)\s*clock cycles',
                    r'Execution Time:\s*(\d+)',
                    r'execution time:\s*(\d+)\s*cycles',
                    r'Time:\s*(\d+)\s*cycles'
                ]
                
                for pattern in time_patterns:
                    time_match = re.search(pattern, output_str, re.IGNORECASE)
                    if time_match:
                        perf_data['execution_time_cycles'] = int(time_match.group(1))
                        break
                
                # If execution time found, continue searching for other metrics
                if 'execution_time_cycles' in perf_data:
                    # Find other performance metrics with more flexible patterns
                    patterns = {
                        'total_instructions': [
                            r'Total Instructions:\s*(\d+)',
                            r'Instructions:\s*(\d+)',
                            r'total instructions:\s*(\d+)'
                        ],
                        'memory_accesses': [
                            r'Memory Accesses:\s*(\d+)',
                            r'Memory accesses:\s*(\d+)',
                            r'memory:\s*(\d+)'
                        ],
                        'stack_operations': [
                            r'Stack Operations:\s*(\d+)',
                            r'Stack operations:\s*(\d+)',
                            r'stack:\s*(\d+)'
                        ],
                        'function_calls': [
                            r'Function Calls:\s*(\d+)',
                            r'Function calls:\s*(\d+)',
                            r'functions:\s*(\d+)'
                        ],
                        'sanitizer_checks': [
                            r'Sanitizer Checks:\s*(\d+)',
                            r'Sanitizer checks:\s*(\d+)',
                            r'sanitizer:\s*(\d+)'
                        ],
                        'cfi_checks': [
                            r'CFI Checks:\s*(\d+)',
                            r'CFI checks:\s*(\d+)',
                            r'cfi:\s*(\d+)'
                        ],
                        'total_memory_bytes': [
                            r'Total Estimated:\s*(\d+)\s*bytes',
                            r'Total Memory:\s*(\d+)\s*bytes',
                            r'Memory:\s*(\d+)\s*bytes',
                            r'Total Estimated:\s*(\d+)'
                        ]
                    }
                    
                    for key, pattern_list in patterns.items():
                        for pattern in pattern_list:
                            match = re.search(pattern, output_str, re.IGNORECASE)
                            if match:
                                try:
                                    perf_data[key] = int(match.group(1))
                                    break  # Use first match found
                                except ValueError:
                                    continue
            
            # Method 3: Look for inline performance data in output
            if not perf_data or 'execution_time_cycles' not in perf_data:
                # Try to find performance data in common output formats
                inline_patterns = {
                    'execution_time_cycles': [
                        r'Time:\s*(\d+)\s*cycles',
                        r'Cycles:\s*(\d+)',
                        r'executed in\s*(\d+)\s*cycles',
                        r'took\s*(\d+)\s*cycles'
                    ]
                }
                
                for key, pattern_list in inline_patterns.items():
                    for pattern in pattern_list:
                        match = re.search(pattern, output_str, re.IGNORECASE)
                        if match:
                            try:
                                perf_data[key] = int(match.group(1))
                                break
                            except ValueError:
                                continue
            
            # If we found at least execution time, consider it successful
            if 'execution_time_cycles' in perf_data:
                # Fill missing values with 0 for consistency
                expected_fields = [
                    'total_instructions', 'memory_accesses', 'stack_operations',
                    'function_calls', 'sanitizer_checks', 'cfi_checks', 'total_memory_bytes'
                ]
                for field in expected_fields:
                    if field not in perf_data:
                        perf_data[field] = 0
                
                return perf_data
            
            # If no performance data found but program completed, check for completion markers
            completion_indicators = [
                "Checksum:",
                "Result:",
                "Completed",
                "Success",
                "Done"
            ]
            
            for indicator in completion_indicators:
                if indicator in output_str:
                    # Program ran but no performance counters - return minimal data
                    return {
                        'execution_time_cycles': 0,
                        'total_instructions': 0,
                        'memory_accesses': 0,
                        'stack_operations': 0,
                        'function_calls': 0,
                        'sanitizer_checks': 0,
                        'cfi_checks': 0,
                        'total_memory_bytes': 0,
                        'no_perf_counters': True
                    }
            
            return None
                
        except Exception as e:
            print(f"Error parsing performance counters: {e}")
            return None
    
    def run_single_test(self, config_name, wasm_file, iterations=10):
        """Run single test configuration"""
        # First analyze WASM module
        module_analysis = self.analyze_wasm_module(wasm_file)
        
        warduino_binary = self.get_warduino_binary_path(config_name)
        wasm_path = os.path.join(self.tests_dir, wasm_file)
        
        print(f"  Testing: {config_name:15} - {wasm_file:20}", end="")
        
        # Warn if there are problematic imports
        if module_analysis and module_analysis['has_problematic_imports']:
            print(f" ⚠️ External dependencies", end="")
        
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
                    timeout=1500
                )
                
                combined_output = result.stdout + result.stderr
                
                if result.stderr:
                    stderr_output = result.stderr.decode('utf-8', errors='ignore')
                    if stderr_output.strip():
                        error_messages.append(stderr_output[:500])
                
                perf_data = self.parse_performance_counters(combined_output)
                
                # Check if system functions are missing
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
                    # Check program output for other clues
                    output_str = combined_output.decode('utf-8', errors='ignore')
                    if "Checksum:" in output_str or "PERF_DATA" in output_str:
                        # Program seems to have run but no performance counters
                        print(" ⚠️ No counters", end="")
                    else:
                        print(" ❌ Failed", end="")
                    execution_times.append(float('inf'))
                    memory_usages.append(0)
                
            except subprocess.TimeoutExpired:
                print(" ⏰ Timeout", end="")
                execution_times.append(float('inf'))
                memory_usages.append(0)
            except Exception as e:
                print(f" 💥 Error", end="")
                execution_times.append(float('inf'))
                memory_usages.append(0)
        
        # If missing system functions detected
        if missing_primitives:
            missing_func = primitive_error_msg.split('primitive ')[-1] if 'primitive' in primitive_error_msg else primitive_error_msg
            print(f" ⚠️ Missing: {missing_func}")
            
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
        
        # Calculate statistics
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
        
        print(f" | Time: {avg_time:8.2f} cycles | Memory: {avg_memory/1024/1024:6.2f} MB | Success: {success_rate:5.1f}%")
        
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
        """Run all benchmark tests"""
        print("Starting WARDuino benchmark tests...")
        
        wasm_files = [f for f in os.listdir(self.tests_dir) if f.endswith('.wasm')]
        
        for wasm_file in wasm_files:
            print(f"\nTest Program: {wasm_file}")
            print("-" * 80)
            
            for config in self.configurations:
                result = self.run_single_test(config, wasm_file)
                if result:
                    self.results.append(result)
        
        self.save_raw_results()
    
    def save_raw_results(self):
        """Save raw test results to results directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(self.results_dir, f"benchmark_results_{timestamp}.json")
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nRaw results saved: {results_file}")
        return results_file
    
    def analyze_performance(self):
        """Analyze performance data"""
        if not self.results:
            print("No test results to analyze")
            return None, None
        
        df = pd.DataFrame(self.results)
        
        # Calculate performance overhead (relative to baseline)
        overhead_data = []
        baseline_times = {}
        baseline_memory = {}
        
        # Collect baseline data
        for test_program in df['test_program'].unique():
            baseline_data = df[(df['config'] == 'baseline') & (df['test_program'] == test_program)]
            if not baseline_data.empty:
                baseline_times[test_program] = baseline_data.iloc[0]['avg_time_cycles']
                baseline_memory[test_program] = baseline_data.iloc[0]['avg_memory_bytes']
        
        # Calculate relative overhead - include CFI in the list
        for test_program in df['test_program'].unique():
            if test_program in baseline_times:
                baseline_time = baseline_times[test_program]
                baseline_mem = baseline_memory[test_program]
                
                # Include CFI in the configurations to calculate overhead for
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
        """Get configuration type description"""
        types = {
            'baseline': 'Baseline',
            'memory': 'Memory Protection',
            'stack': 'Stack Protection',
            'cfi': 'CFI Protection',  # Added CFI description
            'address': 'Address Sanitizer',
            'full': 'Full Protection'
        }
        return types.get(config, 'Unknown')
    
    def generate_comprehensive_report(self, df, overhead_df):
        """Generate comprehensive analysis report"""
        print("\n" + "="*80)
        print("WARDuino Security Check Performance Analysis Report")
        print("="*80)
        
        # Performance comparison table
        print("\n1. Execution Time Comparison (Clock Cycles)")
        print("-" * 80)
        time_summary = df.pivot_table(
            values='avg_time_cycles', 
            index='test_program', 
            columns='config', 
            aggfunc='mean'
        )
        time_summary = time_summary[self.configurations]
        print(time_summary.round(0))
        
        print("\n2. Memory Usage Comparison (MB)")
        print("-" * 80)
        memory_summary = df.pivot_table(
            values='avg_memory_mb', 
            index='test_program', 
            columns='config', 
            aggfunc='mean'
        )
        memory_summary = memory_summary[self.configurations]
        print(memory_summary.round(2))
        
        print("\n3. Test Success Rate (%)")
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
        """Create comprehensive bar comparison charts"""
        print("\nGenerating comprehensive bar comparison charts...")
        
        try:
            # Filter invalid data
            valid_df = df[df['avg_time_cycles'] != float('inf')]
            if valid_df.empty:
                print("⚠️ No valid data to generate charts")
                return
            
            # 1. All modules execution time comparison
            self._create_all_modules_time_comparison(valid_df)
            
            # 2. All modules memory usage comparison
            self._create_all_modules_memory_comparison(valid_df)
            
            # 3. Individual module detailed comparison charts
            self._create_individual_module_charts(valid_df)
            
            # 4. Average results comparison (baseline as reference)
            self._create_average_comparison_chart(valid_df, overhead_df)
            
            # 5. Success rate comparison chart
            self._create_success_rate_chart(df)
            
            print("✅ All bar comparison charts generated successfully")
            
        except Exception as e:
            print(f"Chart generation failed: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_all_modules_time_comparison(self, df):
        """Create execution time comparison chart for all modules"""
        plt.figure(figsize=(16, 8))  # Slightly wider to accommodate more configurations
        
        # Get all test programs
        test_programs = sorted(df['test_program'].unique())
        n_programs = len(test_programs)
        
        # Set bar chart positions - adjust width for more configurations
        x = np.arange(n_programs)
        width = 0.12  # Reduced bar width to fit more configurations
        spacing = 0.02  # Bar spacing
        
        # Draw bar chart for each configuration
        for i, config in enumerate(self.configurations):
            config_data = []
            for program in test_programs:
                program_data = df[(df['test_program'] == program) & (df['config'] == config)]
                if not program_data.empty:
                    config_data.append(program_data.iloc[0]['avg_time_cycles'])
                else:
                    config_data.append(0)
            
            # Calculate positions
            positions = x + i * (width + spacing)
            bars = plt.bar(positions, config_data, width, 
                          label=self.get_config_type(config),
                          color=self.colors[config],
                          alpha=0.8)
            
            # Add value labels (if values are not too large)
            for bar, value in zip(bars, config_data):
                if value > 0:
                    height = bar.get_height()
                    if height < max(config_data) * 0.1:  # Only show if there's enough space above bar
                        plt.text(bar.get_x() + bar.get_width()/2., height + max(config_data)*0.01,
                                f'{value/1000:.0f}K', ha='center', va='bottom', fontsize=7, rotation=45)
        
        plt.xlabel('Test Programs', fontsize=12)
        plt.ylabel('Execution Time (Clock Cycles)', fontsize=12)
        plt.title('Execution Time Comparison Across All Test Modules', fontsize=14, fontweight='bold')
        plt.xticks(x + (len(self.configurations)-1)*(width+spacing)/2, 
                  [p.replace('.wasm', '') for p in test_programs], 
                  rotation=45, ha='right')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        chart_path = os.path.join(self.results_dir, "all_modules_time_comparison.png")
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"All modules execution time comparison chart saved: {chart_path}")
    
    def _create_all_modules_memory_comparison(self, df):
        """Create memory usage comparison chart for all modules"""
        plt.figure(figsize=(16, 8))
        
        test_programs = sorted(df['test_program'].unique())
        n_programs = len(test_programs)
        
        x = np.arange(n_programs)
        width = 0.12  # Reduced width
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
            
            # Add value labels
            for bar, value in zip(bars, config_data):
                if value > 0:
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height + max(config_data)*0.01,
                            f'{value:.2f}', ha='center', va='bottom', fontsize=7)
        
        plt.xlabel('Test Programs', fontsize=12)
        plt.ylabel('Memory Usage (MB)', fontsize=12)
        plt.title('Memory Usage Comparison Across All Test Modules', fontsize=14, fontweight='bold')
        plt.xticks(x + (len(self.configurations)-1)*(width+spacing)/2,
                  [p.replace('.wasm', '') for p in test_programs],
                  rotation=45, ha='right')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        chart_path = os.path.join(self.results_dir, "all_modules_memory_comparison.png")
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"All modules memory usage comparison chart saved: {chart_path}")
    
    def _create_individual_module_charts(self, df):
        """Create individual detailed comparison charts for each module"""
        test_programs = sorted(df['test_program'].unique())
        
        for program in test_programs:
            program_data = df[df['test_program'] == program]
            if program_data.empty:
                continue
            
            # Create subplots
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))  # Wider figure for more configurations
            fig.suptitle(f'Test Program: {program.replace(".wasm", "")}', fontsize=14, fontweight='bold')
            
            # Time comparison
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
            ax1.set_ylabel('Execution Time (Clock Cycles)')
            ax1.set_title('Execution Time Comparison')
            ax1.tick_params(axis='x', rotation=45)
            
            # Add values on bars
            for bar in bars1:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{height/1000:.0f}K', ha='center', va='bottom', fontsize=8)
            
            # Memory comparison
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
            ax2.set_ylabel('Memory Usage (MB)')
            ax2.set_title('Memory Usage Comparison')
            ax2.tick_params(axis='x', rotation=45)
            
            # Add values on bars
            for bar in bars2:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{height:.2f}', ha='center', va='bottom', fontsize=8)
            
            plt.tight_layout()
            
            # Save individual module chart
            safe_name = program.replace('.wasm', '').replace(' ', '_')
            chart_path = os.path.join(self.results_dir, f"module_{safe_name}_comparison.png")
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
        
        print(f"✅ Generated individual comparison charts for {len(test_programs)} modules")
    
    def _create_average_comparison_chart(self, df, overhead_df):
        """Create average results comparison chart (baseline as reference)"""
        if overhead_df.empty:
            print("⚠️ Not enough overhead data to generate average comparison chart")
            return
        
        plt.figure(figsize=(14, 8))  # Wider to accommodate more configurations
        
        # Calculate average overhead for each configuration
        avg_overhead = overhead_df.groupby('config')['time_overhead_percent'].mean()
        
        # Create bar chart
        config_names = [self.get_config_type(config) for config in avg_overhead.index]
        colors = [self.colors[config] for config in avg_overhead.index]
        
        bars = plt.bar(config_names, avg_overhead.values, color=colors, alpha=0.7)
        
        plt.xlabel('Configuration Type', fontsize=12)
        plt.ylabel('Performance Overhead Relative to Baseline (%)', fontsize=12)
        plt.title('Average Performance Overhead Comparison\n(Baseline as Reference)', fontsize=14, fontweight='bold')
        
        # Add percentage values on bars
        for bar, value in zip(bars, avg_overhead.values):
            plt.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1,
                    f'+{value:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        chart_path = os.path.join(self.results_dir, "average_overhead_comparison.png")
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Average performance overhead comparison chart saved: {chart_path}")
    
    def _create_success_rate_chart(self, df):
        """Create success rate comparison chart"""
        plt.figure(figsize=(12, 6))  # Wider for more configurations
        
        # Calculate average success rate for each configuration
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
        
        plt.xlabel('Configuration Type', fontsize=12)
        plt.ylabel('Success Rate (%)', fontsize=12)
        plt.title('Test Success Rate Comparison Across Configurations', fontsize=14, fontweight='bold')
        plt.ylim(0, 100)
        
        # Add percentage values on bars
        for bar, rate in zip(bars, success_rates):
            plt.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1,
                    f'{rate:.1f}%', ha='center', va='bottom', fontsize=11)
        
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        chart_path = os.path.join(self.results_dir, "success_rate_comparison.png")
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Success rate comparison chart saved: {chart_path}")
    
    def create_performance_charts(self, df, overhead_df):
        """Create performance analysis charts - maintain backward compatibility"""
        self.create_comprehensive_bar_charts(df, overhead_df)
    
    def generate_detailed_report(self, df, overhead_df):
        """Generate detailed data report to results directory"""
        try:
            report_path = os.path.join(self.results_dir, "detailed_performance_report.md")
            
            with open(report_path, 'w') as f:
                f.write("# WARDuino Security Check Detailed Performance Report\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"Results Directory: {self.results_dir}\n\n")
                f.write("**Note**: All time data comes from WARDuino internal performance counters (clock cycles)\n\n")
                
                # Chart references
                f.write("## Performance Comparison Charts\n\n")
                f.write("The following charts provide comprehensive performance comparison analysis:\n\n")
                f.write("- `all_modules_time_comparison.png` - Execution time comparison across all modules\n")
                f.write("- `all_modules_memory_comparison.png` - Memory usage comparison across all modules\n")
                f.write("- `module_*_comparison.png` - Individual module detailed comparisons\n")
                f.write("- `average_overhead_comparison.png` - Average performance overhead comparison (baseline as reference)\n")
                f.write("- `success_rate_comparison.png` - Test success rate comparison\n\n")
                
                # Execution time details - updated to include CFI
                f.write("## Execution Time Details (Clock Cycles)\n\n")
                f.write("| Test Program | Baseline | Memory Protection | Stack Protection | CFI Protection | Address Sanitizer | Full Protection |\n")
                f.write("|--------------|----------|-------------------|------------------|----------------|-------------------|-----------------|\n")
                
                for test_program in df['test_program'].unique():
                    row_data = [test_program.replace('.wasm', '')]
                    for config in self.configurations:
                        data = df[(df['test_program'] == test_program) & (df['config'] == config)]
                        if not data.empty and data.iloc[0]['avg_time_cycles'] != float('inf'):
                            avg = data.iloc[0]['avg_time_cycles']
                            row_data.append(f"{avg:,.0f}")
                        else:
                            row_data.append("Failed")
                    f.write("| " + " | ".join(row_data) + " |\n")
                
                # Memory usage details - updated to include CFI
                f.write("\n## Memory Usage Details (MB)\n\n")
                f.write("| Test Program | Baseline | Memory Protection | Stack Protection | CFI Protection | Address Sanitizer | Full Protection |\n")
                f.write("|--------------|----------|-------------------|------------------|----------------|-------------------|-----------------|\n")
                
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
                
                # Success rate details - updated to include CFI
                f.write("\n## Test Success Rate (%)\n\n")
                f.write("| Test Program | Baseline | Memory Protection | Stack Protection | CFI Protection | Address Sanitizer | Full Protection |\n")
                f.write("|--------------|----------|-------------------|------------------|----------------|-------------------|-----------------|\n")
                
                for test_program in df['test_program'].unique():
                    row_data = [test_program.replace('.wasm', '')]
                    for config in self.configurations:
                        data = df[(df['test_program'] == test_program) & (df['config'] == config)]
                        if not data.empty:
                            row_data.append(f"{data.iloc[0]['success_rate']:.1f}")
                        else:
                            row_data.append("N/A")
                    f.write("| " + " | ".join(row_data) + " |\n")
                
                # Performance overhead analysis - include CFI
                if not overhead_df.empty:
                    f.write("\n## Performance Overhead Analysis (Relative to Baseline)\n\n")
                    f.write("| Configuration | Average Time Overhead (%) | Average Memory Overhead (%) |\n")
                    f.write("|---------------|--------------------------|----------------------------|\n")
                    
                    for config in ['memory', 'stack', 'cfi', 'address', 'full']:
                        config_data = overhead_df[overhead_df['config'] == config]
                        if not config_data.empty:
                            avg_time_overhead = config_data['time_overhead_percent'].mean()
                            avg_memory_overhead = config_data['memory_overhead_percent'].mean()
                            f.write(f"| {self.get_config_type(config)} | +{avg_time_overhead:.1f}% | +{avg_memory_overhead:.1f}% |\n")
                
                # Show failed tests
                f.write("\n## Failed Tests\n\n")
                for _, row in df.iterrows():
                    if row.get('missing_primitive', False) or row['success_rate'] == 0:
                        f.write(f"- **{row['config']} - {row['test_program']}**: {row.get('error', 'Unknown error')}\n")
            
            print(f"Detailed report generated: {report_path}")
            return report_path
            
        except Exception as e:
            print(f"Error generating detailed report: {e}")
            import traceback
            traceback.print_exc()
            return None

def main():
    """Main function"""
    runner = BenchmarkRunner()
    
    # Check environment
    if not runner.check_environment():
        print("Environment check failed, please ensure:")
        print("1. WARDuino benchmark directory exists: /home/yuxin/WARDuino_benchmarks")
        print("2. build_warduino_configs.sh has been run to compile WARDuino")
        return
    
    try:
        # Run benchmark tests
        runner.run_all_benchmarks()
        
        # Analyze and generate reports
        df, overhead_df = runner.analyze_performance()
        if df is not None:
            runner.generate_comprehensive_report(df, overhead_df)
            runner.create_comprehensive_bar_charts(df, overhead_df)  # Use new chart generation method
            runner.generate_detailed_report(df, overhead_df)
        
        # Display generated file list
        print("\n" + "="*80)
        print("Generated Files List:")
        print("="*80)
        result_files = [f for f in os.listdir(runner.results_dir) if f.endswith(('.png', '.json', '.md'))]
        for file in sorted(result_files):
            file_path = os.path.join(runner.results_dir, file)
            file_size = os.path.getsize(file_path) / 1024  # KB
            print(f"  - {file} ({file_size:.1f} KB)")
        
        print(f"\n🎉 Benchmark tests completed! All results saved to: {runner.results_dir}")
        
    except Exception as e:
        print(f"Error during benchmark testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
