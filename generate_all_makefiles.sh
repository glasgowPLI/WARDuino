#!/bin/sh

set -e  # Exit on any error

SRC_DIR=$(pwd)
CMAKE_FLAGS_COMMON='-DCMAKE_C_COMPILER=clang -DCMAKE_C_FLAGS="-march=morello -mabi=purecap -O2" -DBUILD_EMULATOR=ON'

# List of folder names and flags
build_dirs=(
  "build-purecap-hw-sw"
  "build-purecap-hw"
  "build-purecap-sw"
  "build-purecap-nocheck"
  "build-native-sw"
  "build-native"
)

flags_list=(
  "-DBUILD_MORELLO_PURECAP=ON -DHARDWARE_BOUND_CHECKS=ON  -DSOFTWARE_BOUND_CHECKS=ON"
  "-DBUILD_MORELLO_PURECAP=ON -DHARDWARE_BOUND_CHECKS=ON  -DSOFTWARE_BOUND_CHECKS=OFF"
  "-DBUILD_MORELLO_PURECAP=ON -DHARDWARE_BOUND_CHECKS=OFF -DSOFTWARE_BOUND_CHECKS=ON"
  "-DBUILD_MORELLO_PURECAP=ON -DHARDWARE_BOUND_CHECKS=OFF -DSOFTWARE_BOUND_CHECKS=OFF"
  "-DBUILD_MORELLO_PURECAP=OFF -DHARDWARE_BOUND_CHECKS=OFF -DSOFTWARE_BOUND_CHECKS=ON"
  "-DBUILD_MORELLO_PURECAP=OFF -DHARDWARE_BOUND_CHECKS=OFF -DSOFTWARE_BOUND_CHECKS=OFF"
)

# Loop through both arrays
i=0
while [ $i -lt ${#build_dirs[@]} ]; do
  dir=${build_dirs[$i]}
  flags=${flags_list[$i]}
  echo "🔧 Configuring $dir"
  mkdir -p "$dir"
  cd "$dir"
  eval cmake "$SRC_DIR" $CMAKE_FLAGS_COMMON $flags
  cd "$SRC_DIR"
  i=$((i + 1))
done

echo "✅ All CMake build files generated."
