#!/bin/bash
echo "=== WARDuino内存安全测试快速启动 ==="
echo ""

# 验证WARDuino路径
WARDUNIO_PATH="$HOME/WARDuino/build-emu/wdcli"

if [ ! -f "$WARDUNIO_PATH" ]; then
    echo "❌ 错误: 找不到WARDuino"
    echo "路径: $WARDUNIO_PATH"
    echo ""
    echo "请确保:"
    echo "1. WARDuino已正确编译"
    echo "2. 可执行文件位于: ~/WARDuino/build-emu/wdcli"
    echo "3. 您有执行权限"
    exit 1
fi

echo "✅ 找到WARDuino: $WARDUNIO_PATH"

# 检查测试文件
if [ ! -d "ward_tests" ] || [ -z "$(ls ward_tests/*.wasm 2>/dev/null)" ]; then
    echo "❌ 错误: 没有WASM测试文件"
    echo ""
    echo "请先运行编译脚本:"
    echo "  ./compile_all_tests.sh"
    echo "或"
    echo "  ./smart_compile_manager.sh"
    exit 1
fi

echo "✅ 找到WASM测试文件"

# 选择测试模式
echo ""
echo "请选择测试模式:"
echo "1) 快速测试 (运行前5个测试)"
echo "2) 完整测试 (运行所有测试)"
echo "3) 详细测试 (带完整日志)"
echo ""
read -p "请输入选择 (1-3): " choice

case $choice in
    1)
        echo "运行快速测试..."
        count=0
        for wasm_file in ward_tests/*.wasm; do
            if [ $count -ge 5 ]; then
                break
            fi
            test_name=$(basename "$wasm_file" .wasm)
            echo "测试: $test_name"
            "$WARDUNIO_PATH"  "$wasm_file" --no-debug --invoke _start > /dev/null 2>&1
            exit_code=$?
            case $exit_code in
                0) echo "  结果: 正常结束" ;;
                1) echo "  结果: ✅ 检测到违规" ;;
                139) echo "  结果: ✅ 段错误" ;;
                *) echo "  结果: 未知 ($exit_code)" ;;
            esac
            ((count++))
        done
        ;;
    2)
        echo "运行完整测试..."
        ./full_test_suite.sh
        ;;
    3)
        echo "运行详细测试..."
        ./run_warduino_tests.sh
        ;;
    *)
        echo "无效选择，运行完整测试..."
        ./full_test_suite.sh
        ;;
esac

echo ""
echo "=== 测试完成 ==="
