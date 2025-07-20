#!/bin/bash

set -e  # Exit on any error

SRC_DIR=$(pwd)  # Assume you are in the top-level WARDuino source folder
CMAKE_FLAGS_COMMON="-DCMAKE_C_COMPILER=clang -DCMAKE_C_FLAGS=\"-march=morello -mabi=purecap -O2\" -DBUILD_EMULATOR=ON"

# Define build configurations
declare -A BUILD_CONFIGS=(
  [build-purecap-hw-sw]="-DBUILD_MORELLO_PURECAP=ON  -DHARDWARE_BOUND_CHECKS=ON  -DSOFTWARE_BOUND_CHECKS=ON"
  [build-purecap-hw]   ="-DBUILD_MORELLO_PURECAP=ON  -DHARDWARE_BOUND_CHECKS=ON  -DSOFTWARE_BOUND_CHECKS=OFF"
  [build-purecap-sw]   ="-DBUILD_MORELLO_PURECAP=ON  -DHARDWARE_BOUND_CHECKS=OFF -DSOFTWARE_BOUND_CHECKS=ON"
  [build-purecap-nocheck]="-DBUILD_MORELLO_PURECAP=ON  -DHARDWARE_BOUND_CHECKS=OFF -DSOFTWARE_BOUND_CHECKS=OFF"
  [build-native-sw]    ="-DBUILD_MORELLO_PURECAP=OFF -DHARDWARE_BOUND_CHECKS=OFF -DSOFTWARE_BOUND_CHECKS=ON"
  [build-native]       ="-DBUILD_MORELLO_PURECAP=OFF -DHARDWARE_BOUND_CHECKS=OFF -DSOFTWARE_BOUND_CHECKS=OFF"
)

for dir in "${!BUILD_CONFIGS[@]}"; do
  echo "🔧 Configuring $dir"
  mkdir -p "$dir"
  cd "$dir"
  eval cmake "$SRC_DIR" $CMAKE_FLAGS_COMMON ${BUILD_CONFIGS[$dir]}
  cd "$SRC_DIR"
done"wq


echo "✅ All CMake build

