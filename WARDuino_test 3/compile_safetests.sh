#!/bin/bash

# WARDuino测试编译脚本
# 编译所有ward_tests子目录的C程序为WASM模块

echo "开始编译WARDuino测试程序..."

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查clang是否安装
if ! command -v clang &> /dev/null; then
    echo -e "${RED}错误: 未找到clang编译器${NC}"
    exit 1
fi

# 检查目标是否支持wasm32
echo -e "${YELLOW}检查WASM目标支持...${NC}"
clang --target=wasm32 -v > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}错误: clang不支持wasm32目标${NC}"
    echo "请安装wasm支持: sudo apt-get install lld wasi-libc"
    exit 1
fi

# 创建输出目录（如果需要）
#mkdir -p output

# 定义编译函数
compile_test() {
    local source_file="ward_tests/$1"
    local output_file="ward_tests/$2"
    
    echo -e "${YELLOW}编译: $source_file -> $output_file${NC}"
    
    clang --target=wasm32 \
          -nostdlib \
          -Wl,--no-entry \
          -Wl,--export-all \
          -Wl,--allow-undefined \
          -o "$output_file" \
          "$source_file"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 成功: $output_file${NC}"
        # 显示文件大小
        size=$(stat -f%z "$output_file" 2>/dev/null || stat -c%s "$output_file" 2>/dev/null)
        echo "  文件大小: ${size} bytes"
        return 0
    else
        echo -e "${RED}✗ 失败: $source_file${NC}"
        return 1
    fi
}

# 计数器
success_count=0
fail_count=0

# 编译所有测试文件
echo -e "\n${YELLOW}=== 开始编译测试程序 ===${NC}"

# 基础功能测试
compile_test "compute_test.c" "compute_test.wasm" && ((success_count++)) || ((fail_count++))
compile_test "control_test.c" "control_test.wasm" && ((success_count++)) || ((fail_count++))
compile_test "memory_test.c" "memory_test.wasm" && ((success_count++)) || ((fail_count++))

# 内存安全测试
compile_test "oob_read.c" "oob_read.wasm" && ((success_count++)) || ((fail_count++))
compile_test "oob_write.c" "oob_write.wasm" && ((success_count++)) || ((fail_count++))
compile_test "stack_overflow.c" "stack_overflow.wasm" && ((success_count++)) || ((fail_count++))

# 其他安全测试
compile_test "test_Buffer_Underflow.c" "test_Buffer_Underflow.wasm" && ((success_count++)) || ((fail_count++))
compile_test "test_Division_By_Zero.c" "test_Division_By_Zero.wasm" && ((success_count++)) || ((fail_count++))
compile_test "test_Double_Free.c" "test_Double_Free.wasm" && ((success_count++)) || ((fail_count++))
compile_test "test_Double_Free_Simulation.c" "test_Double_Free_Simulation.wasm" && ((success_count++)) || ((fail_count++))
compile_test "test_Format_String_Simulation.c" "test_Format_String_Simulation.wasm" && ((success_count++)) || ((fail_count++))
compile_test "test_Heap_Overflow.c" "test_Heap_Overflow.wasm" && ((success_count++)) || ((fail_count++))
compile_test "test_Infinite_Loop.c" "test_Infinite_Loop.wasm" && ((success_count++)) || ((fail_count++))
compile_test "test_Integer_Overflow.c" "test_Integer_Overflow.wasm" && ((success_count++)) || ((fail_count++))
compile_test "test_Memory_Access.c" "test_Memory_Access.wasm" && ((success_count++)) || ((fail_count++))
compile_test "test_Memory_Alignment.c" "test_Memory_Alignment.wasm" && ((success_count++)) || ((fail_count++))
compile_test "test_Null_Pointer_Dereference.c" "test_Null_Pointer_Dereference.wasm" && ((success_count++)) || ((fail_count++))
compile_test "test_OOB_Read.c" "test_OOB_Read.wasm" && ((success_count++)) || ((fail_count++))
compile_test "test_OOB_Write.c" "test_OOB_Write.wasm" && ((success_count++)) || ((fail_count++))

# 内存对齐测试
compile_test "memory_alignment.c" "memory_alignment.wasm" && ((success_count++)) || ((fail_count++))

# 汇总结果
echo -e "\n${YELLOW}=== 编译完成 ===${NC}"
echo -e "${GREEN}成功: $success_count 个文件${NC}"
if [ $fail_count -gt 0 ]; then
    echo -e "${RED}失败: $fail_count 个文件${NC}"
fi

# 创建测试清单
echo -e "\n${YELLOW}生成测试清单...${NC}"
cat > test_manifest.txt << EOF
WARDuino测试模块清单
生成时间: $(date)
成功编译: $success_count 个模块

可用测试模块:
$(ls *.wasm 2>/dev/null | while read file; do echo "  - $file"; done)

测试分类:
- 基础功能测试: compute_test.wasm, control_test.wasm, memory_test.wasm
- 内存安全测试: oob_read.wasm, oob_write.wasm, stack_overflow.wasm
- 边界检查测试: test_Buffer_Underflow.wasm, test_OOB_Read.wasm, test_OOB_Write.wasm
- 算术异常测试: test_Division_By_Zero.wasm, test_Integer_Overflow.wasm
- 指针安全测试: test_Null_Pointer_Dereference.wasm, test_Memory_Access.wasm
- 控制流测试: test_Infinite_Loop.wasm
- 内存管理测试: test_Double_Free.wasm, test_Heap_Overflow.wasm

使用说明:
使用WARDuino运行时加载这些WASM模块进行内存安全测试。
EOF

echo -e "${GREEN}测试清单已保存到: test_manifest.txt${NC}"

# 验证WASM文件
echo -e "\n${YELLOW}验证WASM文件...${NC}"
if command -v wasm-objdump &> /dev/null; then
    for wasm_file in *.wasm; do
        if [ -f "$wasm_file" ]; then
            echo -n "验证 $wasm_file: "
            wasm-objdump -h "$wasm_file" > /dev/null 2>&1
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}有效${NC}"
            else
                echo -e "${RED}无效${NC}"
            fi
        fi
    done
else
    echo "注意: 未安装wasm-objdump，跳过WASM文件验证"
fi

echo -e "\n${GREEN}所有编译任务完成!${NC}"
