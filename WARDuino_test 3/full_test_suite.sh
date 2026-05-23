#!/bin/bash
echo "=== WARDuino完整内存安全测试套件 ==="
echo "使用WARDuino: ~/WARDuino/build-emu/wdcli"
echo "开始时间: $(date)"
echo ""

# 设置正确的路径
WARDUNIO_PATH="$HOME/WARDuino/build-emu/wdcli"

# 步骤1: 验证环境
echo "步骤1: 验证环境..."
if [ ! -f "$WARDUNIO_PATH" ]; then
    echo "❌ 错误: 找不到WARDuino: $WARDUNIO_PATH"
    exit 1
fi
echo "✅ WARDuino可用: $WARDUNIO_PATH"

# 步骤2: 检查测试文件
echo ""
echo "步骤2: 检查测试文件..."
if [ ! -d "ward_tests" ] || [ -z "$(ls ward_tests/*.wasm 2>/dev/null)" ]; then
    echo "❌ 错误: 没有WASM测试文件"
    echo "请先运行编译脚本生成测试文件"
    exit 1
fi

WASM_FILES=(ward_tests/*.wasm)
echo "✅ 找到 ${#WASM_FILES[@]} 个测试文件"

# 步骤3: 运行分类测试
echo ""
echo "步骤3: 运行内存安全测试..."
echo "=============================="

# 测试分类和结果
declare -A categories
categories=(
    ["basic"]="基础内存操作"
    ["pointer"]="指针操作" 
    ["array"]="数组边界"
    ["heap"]="堆内存"
    ["control"]="控制流"
    ["special"]="特殊情况"
)

declare -A category_results
total_tests=0
total_detected=0

for wasm_file in "${WASM_FILES[@]}"; do
    test_name=$(basename "$wasm_file" .wasm)
    
    # 确定测试类别
    category="other"
    for cat_key in "${!categories[@]}"; do
        if [[ "$test_name" == *"$cat_key"* ]]; then
            category="$cat_key"
            break
        fi
    done
    
    echo ""
    echo "🔍 测试: $test_name"
    echo "   类别: ${categories[$category]:-$category}"
    
    # 运行测试
    "$WARDUNIO_PATH"  "$wasm_file" --no-debug --invoke _start> /dev/null 2>&1
    exit_code=$?
    
    ((total_tests++))
    
    # 初始化类别统计
    if [ -z "${category_results[$category]}" ]; then
        category_results[$category]="0,0" # detected,total
    fi
    
    detected=$(echo ${category_results[$category]} | cut -d, -f1)
    total=$(echo ${category_results[$category]} | cut -d, -f2)
    
    # 分析结果
    case $exit_code in
        0)
            echo "   结果: ❌ 未检测到违规"
            ;;
        1|139)
            echo "   结果: ✅ 检测到违规"
            ((detected++))
            ((total_detected++))
            ;;
        *)
            echo "   结果: 🔍 未知 ($exit_code)"
            ;;
    esac
    
    ((total++))
    category_results[$category]="$detected,$total"
done

# 步骤4: 生成报告
echo ""
echo "=============================="
echo "=== 内存安全测试报告 ==="
echo "=============================="
echo "测试完成时间: $(date)"
echo "WARDuino路径: $WARDUNIO_PATH"
echo ""

# 总体统计
echo "📊 总体统计:"
echo "总测试数: $total_tests"
echo "检测到的违规: $total_detected"
if [ $total_tests -gt 0 ]; then
    detection_rate=$((total_detected * 100 / total_tests))
    echo "检测率: ${detection_rate}%"
fi

# 分类统计
echo ""
echo "📈 分类统计:"
for category in "${!categories[@]}"; do
    if [ -n "${category_results[$category]}" ]; then
        detected=$(echo ${category_results[$category]} | cut -d, -f1)
        total=$(echo ${category_results[$category]} | cut -d, -f2)
        if [ $total -gt 0 ]; then
            rate=$((detected * 100 / total))
            printf "  %-12s: %2d/%2d (%3d%%) - %s\n" "$category" $detected $total $rate "${categories[$category]}"
        fi
    fi
done

# 其他类别
if [ -n "${category_results[other]}" ]; then
    detected=$(echo ${category_results[other]} | cut -d, -f1)
    total=$(echo ${category_results[other]} | cut -d, -f2)
    if [ $total -gt 0 ]; then
        rate=$((detected * 100 / total))
        printf "  %-12s: %2d/%2d (%3d%%) - %s\n" "other" $detected $total $rate "其他测试"
    fi
fi

# 能力评估
echo ""
echo "🎯 WARDuino内存安全能力评估:"

if [ $total_tests -eq 0 ]; then
    echo "❌ 没有运行任何测试"
elif [ $total_detected -eq $total_tests ]; then
    echo "✅ 优秀 - 检测到所有内存安全违规 (100%)"
    echo "   WARDuino具有强大的内存保护能力"
elif [ $detection_rate -ge 80 ]; then
    echo "✅ 很好 - 检测到大多数内存安全违规 (${detection_rate}%)"
    echo "   WARDuino提供有效的内存保护"
elif [ $detection_rate -ge 60 ]; then
    echo "⚠️  良好 - 检测到较多内存安全违规 (${detection_rate}%)"
    echo "   WARDuino具有较好的内存保护能力"
elif [ $detection_rate -ge 40 ]; then
    echo "⚠️  一般 - 检测到部分内存安全违规 (${detection_rate}%)"
    echo "   WARDuino具有基本的内存保护能力"
else
    echo "❌ 需要改进 - 检测率较低 (${detection_rate}%)"
    echo "   建议加强内存安全检测机制"
fi

# 生成详细报告文件
REPORT_FILE="warduino_memory_safety_report_$(date +%Y%m%d_%H%M%S).txt"
{
    echo "WARDuino内存安全测试报告"
    echo "=============================="
    echo "测试时间: $(date)"
    echo "WARDuino路径: $WARDUNIO_PATH"
    echo "测试目录: $(pwd)"
    echo ""
    echo "总体结果:"
    echo "  总测试数: $total_tests"
    echo "  检测到的违规: $total_detected"
    echo "  检测率: ${detection_rate}%"
    echo ""
    echo "分类结果:"
    for category in "${!categories[@]}"; do
        if [ -n "${category_results[$category]}" ]; then
            detected=$(echo ${category_results[$category]} | cut -d, -f1)
            total=$(echo ${category_results[$category]} | cut -d, -f2)
            if [ $total -gt 0 ]; then
                rate=$((detected * 100 / total))
                echo "  ${categories[$category]}: $detected/$total ($rate%)"
            fi
        fi
    done
    if [ -n "${category_results[other]}" ]; then
        detected=$(echo ${category_results[other]} | cut -d, -f1)
        total=$(echo ${category_results[other]} | cut -d, -f2)
        if [ $total -gt 0 ]; then
            rate=$((detected * 100 / total))
            echo "  其他测试: $detected/$total ($rate%)"
        fi
    fi
    echo ""
    echo "评估结论:"
    if [ $total_detected -eq $total_tests ]; then
        echo "WARDuino展现了优秀的内存安全检测能力，能够有效识别和阻止各种内存安全违规。"
    elif [ $detection_rate -ge 80 ]; then
        echo "WARDuino具有良好的内存安全检测能力，在大多数情况下能够提供有效的保护。"
    elif [ $detection_rate -ge 60 ]; then
        echo "WARDuino具有较好的内存安全检测能力，能够识别多数类型的内存违规。"
    elif [ $detection_rate -ge 40 ]; then
        echo "WARDuino具有基本的内存安全检测能力，能够识别部分类型的内存违规。"
    else
        echo "WARDuino的内存安全检测能力有限，建议进一步改进和优化检测机制。"
    fi
} > "$REPORT_FILE"

echo ""
echo "=== 测试套件完成 ==="
echo "详细报告已保存: $REPORT_FILE"
echo "当前目录: $(pwd)"
