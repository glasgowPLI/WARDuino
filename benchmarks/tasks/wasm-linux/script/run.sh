#!/bin/bash

# Run the scripts with the specified runtime
bash opcode-profile.sh wasm3
python3 opcode-cate.py
python3 opcode-total.py
python3 opcode-graph.py
