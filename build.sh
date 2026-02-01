#!/bin/bash

# Iceberg Launcher Build Script
echo "Building Iceberg Launcher executable..."

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/
rm -rf dist/

# Build executable
echo "Building executable..."
pyinstaller IcebergLauncher.spec

# Check if build was successful
if [ -f "dist/IcebergLauncher" ]; then
    echo "✅ Build successful!"
    echo "Executable created at: dist/IcebergLauncher"
    echo "Size: $(du -h dist/IcebergLauncher | cut -f1)"
else
    echo "❌ Build failed!"
    exit 1
fi

# Optional: Create a simple installer script
echo "Creating launcher script..."
cat > run_iceberg.sh << 'EOF'
#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
"$DIR/IcebergLauncher"
EOF
chmod +x run_iceberg.sh

echo "🎉 Iceberg Launcher build complete!"
echo "Run with: ./dist/IcebergLauncher"
