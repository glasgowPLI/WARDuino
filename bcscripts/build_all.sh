#!/bin/sh

set -e  # Stop on first error

BUILD_DIRS="
../build-purecap-hw
../build-purecap-hw-sw
../build-native-sw
../build-native-nocheck
"

for dir in $BUILD_DIRS; do
  echo "🔨 Building in $dir..."
  if [ -f "$dir/Makefile" ]; then
    (cd "$dir" && make -j)
  else
    echo "⚠️  Skipping $dir (Makefile not found)"
  fi
done

echo "✅ All builds complete."

