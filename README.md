<div align="center">
  <h1>WARDuino</h1>

  <p>
    <strong>Wasm virtual machine for ESP32 / Arduino</strong>
  </p>

  <p>
    <a href="https://github.com/TOPLLab/WARDuino/actions/workflows/compile.yml"><img src="https://github.com/TOPLLab/WARDuino/actions/workflows/compile.yml/badge.svg"></a>
    <a href="https://github.com/TOPLLab/WARDuino/actions/workflows/test.yml"><img src="https://github.com/TOPLLab/WARDuino/actions/workflows/test.yml/badge.svg"></a>
    <a href="https://doi.org/10.1016/j.cola.2024.101268"><img src="https://img.shields.io/badge/DOI-10.1016%2Fj.cola.2024.101268-blue.svg"></a>
    <a href="https://github.com/TOPLLab/WARDuino/blob/master/LICENSE"><img src="https://img.shields.io/badge/License-MPL_2.0-blue.svg"></a>
  </p>

  <b>
    <a href="./README.md#build-and-development-instructions">Installation</a>
    <span> | </span>
    <a href="./tutorials/">Examples</a>
    <span> | </span>
    <a href="./README.md#webassembly-specification-tests">Run Specification tests</a>
    <span> | </span>
    <a href="https://topllab.github.io/WARDuino/guide/get-started.html">Documentation</a>
  </b>
</div>

## About

This project is released under the Mozilla Public License 2.0, and is being developed as part of an active research project at the University of Ghent's [TOPL Lab](https://github.com/TOPLLab).

+ The WARDuino virtual machine is a WebAssembly runtime for microcontrollers, which runs both under the Arduino and ESP-IDF toolchains.
+ The WARDuino virtual machine features an extensive debugger with novel techniques such as out-of-place debugging.
+ The virtual machine allows developers to implement their own primitives in C++, which are callable from Wasm.
+ The WARDuino project also includes a [VS Code extension](https://github.com/TOPLLab/WARDuino-VSCode) to use both the remote debugging and the out-of-place debugging facilities offered by the virtual machine.

> [!WARNING]
> WARDuino is not 1.0, since this is an active research project. Expect possible bugs or performance issues.

## Build and Development Instructions

> [!NOTE]
> **Supported platforms:** Linux (Ubuntu), macOS, ESP-IDF, Arduino, CHERI (experimental)

The project uses CMake. Quick install looks like this:

```bash
git clone --recursive git@github.com:TOPLLab/WARDuino.git
cd WARDuino
mkdir build-emu
cd build-emu
cmake .. -D BUILD_EMULATOR=ON
make
