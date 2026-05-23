#!/bin/bash
echo "=== WARDuino内存安全测试套件 ==="
echo "开始时间: $(date)"
echo ""

# 检查WARDuino
WARDUNIO="~/WARDuino/build-emu/wdcli"
if [ ! -f "$WARDUNIO" ]; then
    echo "❌ 错误: 找不到WARDuino可执行文件"
    echo "请将warduino放置在当前目录"
    exit 1
fi

# 测试结果存储
declare -A test_results
declare -A test_exit_codes
declare -A test_categories

# 测试分类
test_categories=(
    ["test_basic_memory"]="基础内存访问"
    ["test_pointers"]="指针操作" 
    ["test_array_bounds"]="数组边界"
    ["test_dynamic_patterns"]="动态内存模式"
    ["test_complex_patterns"]="复杂访问模式"
    ["test_special_cases"]="特殊情况"
    ["test_control_flow"]="控制流相关"
)

# 运行所有测试
TOTAL_TESTS=0
DETECTED_VIOLATIONS=0
MISSED_VIOLATIONS=0

echo "运行测试套件..."
echo "========================"

for wasm_file in ward_tests/*.wasm; do
    if [ ! -f "$wasm_file" ]; then
        continue
    fi
    
    # 提取测试名称
    test_name=$(basename "$wasm_file" .wasm)
    category=${test_categories[$test_name]:-"未分类"}
    
    echo ""
    echo "测试: $test_name"
    echo "分类: $category"
    
    # 运行测试
    $WARDUNIO  "$wasm_file" --no-debug --invoke _start> /dev/null 2>&1
    EXIT_CODE=$?
    
    # 记录结果
    test_exit_codes[$test_name]=$EXIT_CODE
    ((TOTAL_TESTS++))
    
    # 分析结果
    case $EXIT_CODE in
        0)
            test_results[$test_name]="MISSED"
            ((MISSED_VIOLATIONS++))
            echo "结果: ❌ 未检测到违规"
            echo "      测试正常结束，但应该检测到内存安全违规"
            ;;
        1)
            test_results[$test_name]="DETECTED" 
            ((DETECTED_VIOLATIONS++))
            echo "结果: ✅ 检测到违规"
            echo "      WARDuino成功识别并阻止了内存安全违规"
            ;;
        139)
            test_results[$test_name]="CRASH"
            ((DETECTED_VIOLATIONS++))
            echo "结果: ✅ 段错误检测"
            echo "      通过段错误检测到内存违规"
            ;;
        *)
            test_results[$test_name]="UNKNOWN"
            echo "结果: 🔍 未知退出代码 $EXIT_CODE"
            ;;
    esac
done

echo ""
echo "========================"
echo "=== 测试报告 ==="
echo "========================"
echo "测试完成时间: $(date)"
echo ""

# 总体统计
echo "总体统计:"
echo "=========="
echo "总测试数: $TOTAL_TESTS"
echo "检测到的违规: $DETECTED_VIOLATIONS"
echo "未检测到的违规: $MISSED_VIOLATIONS"

if [ $TOTAL_TESTS -gt 0 ]; then
    detection_rate=$((DETECTED_VIOLATIONS * 100 / TOTAL_TESTS))
    echo "检测率: ${detection_rate}%"
fi

echo ""
echo "详细结果:"
echo "=========="
for test_name in "${!test_results[@]}"; do
    result=${test_results[$test_name]}
    exit_code=${test_exit_codes[$test_name]}
    category=${test_categories[$test_name]:-"未分类"}
    
    case $result in
        "DETECTED"|"CRASH") 
            symbol="✅"
            status="检测成功"
            ;;
        "MISSED")
            symbol="❌" 
            status="检测失败"
            ;;
        *)
            symbol="🔍"
            status="未知"
            ;;
    esac
    
    printf "%-25s %s %-12s (退出码: %-3s) [%s]\n" \
        "$test_name" "$symbol" "$status" "$exit_code" "$category"
done

echo ""
echo "分类统计:"
echo "=========="
declare -A category_stats
for test_name in "${!test_results[@]}"; do
    category=${test_categories[$test_name]:-"未分类"}
    result=${test_results[$test_name]}
    
    if [ -z "${category_stats[$category]}" ]; then
        category_stats[$category]="0,0"  # detected,total
    fi
    
    detected=$(echo ${category_stats[$category]} | cut -d, -f1)
    total=$(echo ${category_stats[$category]} | cut -d, -f2)
    
    if [ "$result" = "DETECTED" ] || [ "$result" = "CRASH" ]; then
        ((detected++))
    fi
    ((total++))
    
    category_stats[$category]="$detected,$total"
done

for category in "${!category_stats[@]}"; do
    detected=$(echo ${category_stats[$category]} | cut -d, -f1)
    total=$(echo ${category_stats[$category]} | cut -d, -f2)
    
    if [ $total -gt 0 ]; then
        rate=$((detected * 100 / total))
        printf "%-20s: %2d/%2d (%3d%%) \n" "$category" $detected $total $rate
    fi
done

echo ""
echo "建议和改进方向:"
echo "================"
if [ $DETECTED_VIOLATIONS -eq $TOTAL_TESTS ]; then
    echo "🎉 优秀! WARDuino检测到了所有内存安全违规。"
    echo "   这表明WARDuino具有强大的内存保护能力。"
elif [ $DETECTED_VIOLATIONS -gt $((TOTAL_TESTS / 2)) ]; then
    echo "👍 良好! WARDuino检测到了大部分内存安全违规。"
    echo "   在大多数情况下可以提供足够的内存保护。"
else
    echo "⚠️  需要改进! WARDuino未能检测到许多内存安全违规。"
    echo "   建议加强内存安全检测机制。"
fi

# 生成详细报告文件
echo ""
echo "生成详细报告..."
REPORT_FILE="warduino_memory_safety_report_$(date +%Y%m%d_%H%M%S).txt"

{
    echo "WARDuino内存安全测试报告"
    echo "生成时间: $(date)"
    echo "================================"
    echo ""
    echo "总体统计:"
    echo "总测试数: $TOTAL_TESTS"
    echo "检测到的违规: $DETECTED_VIOLATIONS" 
    echo "未检测到的违规: $MISSED_VIOLATIONS"
    if [ $TOTAL_TESTS -gt 0 ]; then
        echo "检测率: ${detection_rate}%"
    fi
    echo ""
    echo "详细测试结果:"
    for test_name in "${!test_results[@]}"; do
        echo "$test_name: ${test_results[$test_name]} (退出码: ${test_exit_codes[$test_name]})"
    done
} > "$REPORT_FILE"

echo "详细报告已保存至: $REPORT_FILE"
