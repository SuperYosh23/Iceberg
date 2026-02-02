#!/bin/bash

# Iceberg Launcher Windows Build Script (using osu-wine)
echo "Building Iceberg Launcher for Windows..."

# Function to run commands with osu-wine or regular wine
run_wine() {
    if command -v osu-wine &> /dev/null; then
        osu-wine --wine "$@"
    elif command -v wine &> /dev/null; then
        wine "$@"
    else
        echo "❌ Neither osu-wine nor wine found!"
        echo "Please install osu-wine or wine first."
        exit 1
    fi
}

# Check if osu-wine or wine is installed
if ! command -v osu-wine &> /dev/null && ! command -v wine &> /dev/null; then
    echo "❌ Neither osu-wine nor wine found!"
    echo "Please install osu-wine or wine first:"
    echo "  osu-wine: https://github.com/NelloKudo/osu-winello"
    echo "  wine: sudo apt install wine"
    exit 1
fi

# Detect which wine is being used
if command -v osu-wine &> /dev/null; then
    echo "✅ Using osu-wine"
    WINE_CMD="osu-wine --wine"
else
    echo "✅ Using regular wine"
    WINE_CMD="wine"
fi

# Check if Python is available in wine
echo "🔍 Checking Python availability in $WINE_CMD..."
if ! run_wine python --version &> /dev/null; then
    echo "📦 Python not found in $WINE_CMD. Installing Python..."
    
    # Try to download and install Python for Windows
    echo "📥 Downloading Python installer..."
    PYTHON_INSTALLER="python-3.11.9-amd64.exe"
    
    # Create temp directory
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    # Download Python installer
    if command -v wget &> /dev/null; then
        wget "https://www.python.org/ftp/python/3.11.9/$PYTHON_INSTALLER"
    elif command -v curl &> /dev/null; then
        curl -O "https://www.python.org/ftp/python/3.11.9/$PYTHON_INSTALLER"
    else
        echo "❌ Neither wget nor curl found. Cannot download Python installer."
        echo "Please install wget or curl and try again."
        cd - > /dev/null
        rm -rf "$TEMP_DIR"
        exit 1
    fi
    
    # Install Python in wine
    echo "🔧 Installing Python in $WINE_CMD (this may take a few minutes)..."
    run_wine "$PYTHON_INSTALLER" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    
    # Wait a bit for installation to complete
    sleep 5
    
    # Clean up
    cd - > /dev/null
    rm -rf "$TEMP_DIR"
    
    # Test if Python is now available
    if ! run_wine python --version &> /dev/null; then
        echo "❌ Python installation failed. Trying alternative approach..."
        
        # Try using wine's built-in python if available
        if run_wine winepython --version &> /dev/null; then
            echo "✅ Found winepython, using that instead"
            # Create a python wrapper
            cat > python_wrapper.py << 'EOF'
import sys
import subprocess

# Try winepython first
try:
    subprocess.run(["winepython"] + sys.argv[1:])
except:
    # Fallback to python
    subprocess.run(["python"] + sys.argv[1:])
EOF
            echo "Created python wrapper, but this may not work properly."
        else
            echo "❌ No Python found in wine environment. Please install Python manually:"
            echo "1. Download Python from https://www.python.org/downloads/windows/"
            echo "2. Install it using: osu-wine --wine python-3.11.9-amd64.exe"
            echo "3. Run this script again"
            exit 1
        fi
    else
        echo "✅ Python successfully installed in $WINE_CMD"
    fi
else
    echo "✅ Python found in $WINE_CMD"
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/
rm -rf dist/

# Install PyInstaller in wine environment
echo "📦 Installing PyInstaller..."
run_wine python -m pip install pyinstaller

# Build Windows executable
echo "🔨 Building Windows executable..."
run_wine python -m PyInstaller IcebergLauncher_windows.spec

# Check if build was successful
if [ -f "dist/IcebergLauncher.exe" ]; then
    echo "✅ Windows build successful!"
    echo "Executable created at: dist/IcebergLauncher.exe"
    
    # Get file size
    if command -v du &> /dev/null; then
        echo "Size: $(du -h dist/IcebergLauncher.exe | cut -f1)"
    fi
    
    # Create Windows batch file for running
    echo "📝 Creating Windows launcher script..."
    cat > dist/run_iceberg.bat << 'EOF'
@echo off
cd /d "%~dp0"
IcebergLauncher.exe
EOF
    
    echo "🎉 Windows build complete!"
    echo "Files created in dist/:"
    echo "  - IcebergLauncher.exe (main executable)"
    echo "  - run_iceberg.bat (launcher script)"
    echo ""
    echo "To distribute:"
    echo "1. Copy the entire dist/ folder"
    echo "2. Users can run IcebergLauncher.exe or run_iceberg.bat"
    echo ""
    echo "Built with: $WINE_CMD"
    
else
    echo "❌ Windows build failed!"
    echo "Check the output above for errors."
    exit 1
fi
