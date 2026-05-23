#!/bin/bash
echo "=== 验证WARDuino测试环境 ==="
echo ""

# 检查WARDuino
echo "1. 检查WARDuino..."
WARDUNIO_PATH="$HOME/WARDuino/build-emu/wdcli"
if [ -f "$WARDUNIO_PATH" ]; then
    echo "✅ 找到: $WARDUNIO_PATH"
    echo "   权限: $(ls -l "$WARDUNIO_PATH" | cut -d' ' -f1)"
    echo "   大小: $(du -h "$WARDUNIO_PATH" | cut -f1)"
else
    echo "❌ 未找到: $WARDUNIO_PATH"
    echo "   请检查WARDuino编译和安装"
fi

# 检查测试文件
echo ""
echo "2. 检查测试文件..."
if [ -d "ward_tests" ]; then
    C_FILES=$(ls ward_tests/*.c 2>/dev/null | wc -l)
    WASM_FILES=$(ls ward_tests/*.wasm 2>/dev/null | wc -l)
    echo "   C源文件: $C_FILES 个"
    echo "   WASM文件: $WASM_FILES 个"
    
    if [ $WASM_FILES -gt 0 ]; then
        echo "   前5个WASM文件:"
        ls ward_tests/*.wasm | head -5 | while read file; do
            size=$(du -h "$file" | cut -f1)
            echo "     - $(basename "$file") ($size)"
        done
    else
        echo "   ❌ 没有WASM文件，需要编译"
    fi
else
    echo "   ❌ ward_tests目录不存在"
fi

# 测试WARDuino基本功能
echo ""
echo "3. 测试WARDuino基本功能..."
if [ -f "$WARDUNIO_PATH" ] && [ -f "ward_tests/test_basic_memory.wasm" ]; then
    echo "   运行测试: test_basic_memory.wasm"
    "$WARDUNIO_PATH"  ward_tests/test_basic_memory.wasm --no-debug --invoke _start
    exit_code=$?
    echo "   退出代码: $exit_code"
    
    case $exit_code in
        0) echo "   结果: 正常结束" ;;
        1) echo "   结果: ✅ 检测到内存违规" ;;
        139) echo "   结果: ✅ 段错误" ;;
        *) echo "   结果: 未知 ($exit_code)" ;;
    esac
else
    echo "   ⚠️  跳过基本功能测试"
fi

echo ""
echo "=== 环境验证完成 ==="
if [ -f "$WARDUNIO_PATH" ] && [ -f "ward_tests/test_basic_memory.wasm" ]; then
    echo "✅ 环境准备就绪，可以运行测试"
else
    echo "❌ 环境有问题，请检查上述错误"
fi
