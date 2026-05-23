#!/bin/bash

# 工作目录设置
WARDUINO_SRC_DIR="/home/yuxin/WARDuino-safe"
WARD_TEST_DIR="/home/yuxin/WARDuino_test"

echo "WARDuino源码目录: $WARDUINO_SRC_DIR"
echo "测试工作目录: $WARD_TEST_DIR"

# 检查WARDuino源码目录
if [ ! -d "$WARDUINO_SRC_DIR" ]; then
    echo "错误: WARDuino源码目录不存在: $WARDUINO_SRC_DIR"
    exit 1
fi

# 检查测试目录
if [ ! -d "$WARD_TEST_DIR" ]; then
    echo "创建测试目录: $WARD_TEST_DIR"
    mkdir -p "$WARD_TEST_DIR"
fi

# 基础编译函数
compile_warduino() {
    local config_name=$1
    local memory_protection=$2
    local stack_protection=$3
    local address_sanitizer=$4
    local cfi_protection=$5
    local performance_counters=$6
    local build_type=$7
    
    echo "编译配置: $config_name"
    
    # 在WARDuino-safe目录下创建构建目录
    local build_dir="$WARDUINO_SRC_DIR/build-$config_name"
    echo "构建目录: $build_dir"
    mkdir -p "$build_dir"
    cd "$build_dir"
    
    # 构建CMake命令
    CMAKE_CMD="cmake \"$WARDUINO_SRC_DIR\" \
        -DCMAKE_BUILD_TYPE=$build_type \
        -DBUILD_EMULATOR=ON \
        -DBUILD_ESP=OFF \
        -DBUILD_UNITTEST=OFF"
        #-DPERFORMANCE_COUNTERS=ON" 
    
    # 添加安全选项
    CMAKE_CMD="$CMAKE_CMD -DENABLE_MEMORY_PROTECTION=$memory_protection"
    CMAKE_CMD="$CMAKE_CMD -DENABLE_STACK_PROTECTION=$stack_protection"
    CMAKE_CMD="$CMAKE_CMD -DENABLE_ADDRESS_SANITIZER=$address_sanitizer"
    CMAKE_CMD="$CMAKE_CMD -DENABLE_CFI_PROTECTION=$cfi_protection"
    CMAKE_CMD="$CMAKE_CMD -DPERFORMANCE_COUNTERS=$performance_counters"
    
    echo "执行: $CMAKE_CMD"
    eval $CMAKE_CMD
        
    if [ $? -eq 0 ]; then
        make -j$(nproc)
        if [ $? -eq 0 ]; then
            echo "✅ 完成: $config_name"
            
        else
            echo "❌ 编译失败: $config_name"
        fi
    else
        echo "❌ CMake配置失败: $config_name"
    fi
    
    cd - > /dev/null
    echo "----------------------------------------"
}

# 清理旧构建（在WARDuino-safe目录下）
echo "清理旧构建文件..."
cd "$WARDUINO_SRC_DIR"
rm -rf build-*

# 编译不同配置
echo "开始编译不同安全检查配置的WARDuino..."

# 1. 基线配置 - 无任何安全检查
compile_warduino "baseline" "OFF" "OFF" "OFF" "OFF" "ON" "Release"

# 2. 内存保护配置 - 只开启内存保护
compile_warduino "memory" "ON" "OFF" "OFF" "OFF" "ON" "Release"

# 3. 栈保护配置 - 只开启栈保护  
compile_warduino "stack" "OFF" "ON" "OFF" "OFF" "ON" "Release"

# 4. 地址消毒剂配置 - 只开启地址消毒剂
compile_warduino "address" "OFF" "OFF" "ON" "OFF" "ON" "Release"

# 5. kz配置 - 只开启kz
compile_warduino "cfi" "OFF" "OFF" "OFF" "ON"  "ON" "Release"

# 6. 全保护配置 - 开启所有检查
compile_warduino "full" "ON" "ON" "ON" "ON" "ON" "Release"

echo "所有配置编译完成!"

# 检查生成的可执行文件
echo "检查生成的可执行文件:"
ls -la "$WARDUINO_SRC_DIR/build-*/" 2>/dev/null || echo "无文件生成"

# 显示构建摘要
echo "构建摘要:"
echo "WARDuino源码: $WARDUINO_SRC_DIR"
echo "WARDuino构建目录: $WARDUINO_SRC_DIR/build-*"
echo "测试工作目录: $WARD_TEST_DIR"
echo "WARDuino可执行文件位置: $WARDUINO_SRC_DIR/"
