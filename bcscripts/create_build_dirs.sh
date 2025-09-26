#!/bin/bash

# Create CHERI purecap build folders
mkdir -p build-purecap-hw-sw      # BUILD_MORELLO_PURECAP=ON, HW=ON, SW=ON
mkdir -p build-purecap-hw         # BUILD_MORELLO_PURECAP=ON, HW=ON, SW=OFF
mkdir -p build-purecap-sw         # BUILD_MORELLO_PURECAP=ON, HW=OFF, SW=ON
mkdir -p build-purecap-nocheck    # BUILD_MORELLO_PURECAP=ON, HW=OFF, SW=OFF

# Create native (non-CHERI) build folders
mkdir -p build-native-sw          # BUILD_MORELLO_PURECAP=OFF, HW=OFF, SW=ON
mkdir -p build-native             # BUILD_MORELLO_PURECAP=OFF, HW=OFF, SW=OFF

echo "✅ All build folders created."

