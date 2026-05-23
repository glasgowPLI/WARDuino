#!/bin/bash
echo "=== WARDuino内存安全测试套件 ==="
echo "开始时间: $(date)"
echo ""

# 使用正确的路径
WARDUNIO_PATH="$HOME/WARDuino/build-emu/wdcli"

if [ ! -f "$WARDUNIO_PATH" ]; then
    echo "❌ 错误: 找不到WARDuino可执行文件: $WARDUNIO_PATH"
    echo "请确保WARDuino已正确编译并位于该路径"
    exit 1
fi

echo "✅ 使用WARDuino: $WARDUNIO_PATH"
echo "文件信息: $(file "$WARDUNIO_PATH")"

# 检查WASM测试文件
WASM_FILES=(ward_tests/*.wasm)
if [ ${#WASM_FILES[@]} -eq 0 ]; then
    echo "❌ 错误: 没有找到WASM测试文件"
    echo "请先运行编译脚本生成测试文件"
    exit 1
fi

echo "找到 ${#WASM_FILES[@]} 个WASM测试文件"

# 创建结果目录
RESULTS_DIR="test_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

# 运行测试
echo ""
echo "开始运行测试..."
echo "========================"

declare -A results
declare -A exit_codes
total_tests=0
detected=0
missed=0

for wasm_file in "${WASM_FILES[@]}"; do
    if [ ! -f "$wasm_file" ]; then
        continue
    fi
    
    test_name=$(basename "$wasm_file" .wasm)
    echo ""
    echo "测试: $test_name"
    echo "文件: $(basename "$wasm_file")"
    
    # 运行测试
    start_time=$(date +%s)
    "$WARDUNIO_PATH" --no-debug "$wasm_file" > "$RESULTS_DIR/${test_name}.log" 2>&1
    exit_code=$?
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    ((total_tests++))
    exit_codes["$test_name"]=$exit_code
    
    # 分析结果
    case $exit_code in
        0)
            results["$test_name"]="MISSED"
            ((missed++))
            echo "  结果: ❌ 未检测到违规"
            ;;
        1)
            results["$test_name"]="DETECTED"
            ((detected++))
            echo "  结果: ✅ 检测到违规"
            ;;
        139)
            results["$test_name"]="CRASH"
            ((detected++))
            echo "  结果: ✅ 段错误检测"
            ;;
        *)
            results["$test_name"]="UNKNOWN"
            echo "  结果: 🔍 未知退出码 $exit_code"
            ;;
    esac
    
    echo "  退出代码: $exit_code, 运行时间: ${duration}s"
    
    # 保存详细日志
    {
        echo "=== $test_name 测试日志 ==="
        echo "测试文件: $wasm_file"
        echo "WARDuino: $WARDUNIO_PATH"
        echo "退出代码: $exit_code"
        echo "运行时间: ${duration}s"
        echo "开始时间: $(date -d @$start_time)"
        echo "结束时间: $(date -d @$end_time)"
        if [ -s "$RESULTS_DIR/${test_name}.log" ]; then
            echo ""
            echo "输出内容:"
            cat "$RESULTS_DIR/${test_name}.log"
        fi
    } > "$RESULTS_DIR/${test_name}_detailed.log"
    
    # 清理临时日志文件
    rm -f "$RESULTS_DIR/${test_name}.log"
done

# 生成报告
echo ""
echo "========================"
echo "=== 测试报告 ==="
echo "========================"
echo "测试完成时间: $(date)"
echo "WARDuino路径: $WARDUNIO_PATH"
echo ""

echo "总体统计:"
echo "总测试数: $total_tests"
echo "检测到的违规: $detected"
echo "未检测到的违规: $missed"

if [ $total_tests -gt 0 ]; then
    detection_rate=$((detected * 100 / total_tests))
    echo "检测率: ${detection_rate}%"
fi

echo ""
echo "详细结果:"
for test_name in "${!results[@]}"; do
    result=${results["$test_name"]}
    exit_code=${exit_codes["$test_name"]}
    case $result in
        "DETECTED"|"CRASH") symbol="✅" ;;
        "MISSED") symbol="❌" ;;
        *) symbol="🔍" ;;
    esac
    echo "  $symbol $test_name: $result (退出码: $exit_code)"
done

# 保存总结报告
REPORT_FILE="$RESULTS_DIR/summary_report.txt"
{
    echo "WARDuino内存安全测试报告"
    echo "生成时间: $(date)"
    echo "WARDuino路径: $WARDUNIO_PATH"
    echo "测试目录: $(pwd)"
    echo "================================"
    echo ""
    echo "总体统计:"
    echo "总测试数: $total_tests"
    echo "检测到的违规: $detected"
    echo "未检测到的违规: $missed"
    if [ $total_tests -gt 0 ]; then
        echo "检测率: ${detection_rate}%"
    fi
    echo ""
    echo "详细结果:"
    for test_name in "${!results[@]}"; do
        echo "$test_name: ${results[$test_name]} (退出码: ${exit_codes[$test_name]})"
    done
    echo ""
    echo "日志文件保存在: $RESULTS_DIR/"
} > "$REPORT_FILE"

echo ""
echo "=== 测试完成 ==="
echo "报告已保存到: $REPORT_FILE"
echo "详细日志在: $RESULTS_DIR/"
echo "当前目录: $(pwd)"
