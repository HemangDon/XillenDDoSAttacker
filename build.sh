#!/bin/bash

echo "========================================"
echo "   XillenDoS C++ Engine Builder"
echo "========================================"
echo

if [ ! -d "build" ]; then
    mkdir build
fi
cd build

echo "Configuring CMake..."
cmake .. -DCMAKE_BUILD_TYPE=Release

echo
echo "Building C++ Engine..."
make -j$(nproc)

echo
echo "Copying engine to project directory..."
if [ -f "libdos_engine.so" ]; then
    cp libdos_engine.so ../engine/dos_engine.so
    echo "✅ C++ Engine built successfully!"
else
    echo "❌ Build failed!"
    exit 1
fi

echo
echo "========================================"
echo "   Build Complete!"
echo "========================================"
echo
echo "You can now run: python3 main.py"
echo
