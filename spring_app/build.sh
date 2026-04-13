#!/usr/bin/env bash
# Build Spring Generator – Linux / macOS
# Requires: pip install flask numpy pyinstaller
set -e
cd "$(dirname "$0")"

echo "Installing / updating dependencies..."
pip install -q flask numpy pyinstaller

echo "Building executable..."
pyinstaller spring_generator.spec --clean

echo
echo "Build successful.  Executable: dist/spring_generator"
