#!/usr/bin/env python3
"""
Test script to verify Windows auto-detection functionality
Run this script to test both Linux and Windows modes without needing actual Windows
"""

import os
import sys
import subprocess

def test_windows_mode():
    """Test the launcher in Windows simulation mode"""
    print("🧪 Testing Windows Mode...")
    print("=" * 50)
    
    # Set environment variable to force Windows mode
    env = os.environ.copy()
    env["FORCE_WINDOWS_MODE"] = "true"
    
    # Launch the application with Windows simulation
    try:
        print("Launching launcher in Windows simulation mode...")
        print("You should see:")
        print("- '🧪 TEST MODE: Simulating Windows detection' in console")
        print("- No osu-wine download button in Options")
        print("- Windows-specific help text in Options")
        print("\nPress Ctrl+C to stop the launcher")
        
        subprocess.run([sys.executable, "main.py"], env=env, check=True)
        
    except KeyboardInterrupt:
        print("\n✅ Test completed - User stopped launcher")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running launcher: {e}")
    except FileNotFoundError:
        print("❌ main.py not found. Make sure you're in the correct directory.")

def test_linux_mode():
    """Test the launcher in normal Linux mode"""
    print("🐧 Testing Linux Mode...")
    print("=" * 50)
    
    # Ensure Windows mode is disabled
    env = os.environ.copy()
    env.pop("FORCE_WINDOWS_MODE", None)
    
    try:
        print("Launching launcher in normal Linux mode...")
        print("You should see:")
        print("- Normal platform detection message")
        print("- osu-wine download button in Options")
        print("- Linux-specific help text in Options")
        print("\nPress Ctrl+C to stop the launcher")
        
        subprocess.run([sys.executable, "main.py"], env=env, check=True)
        
    except KeyboardInterrupt:
        print("\n✅ Test completed - User stopped launcher")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running launcher: {e}")
    except FileNotFoundError:
        print("❌ main.py not found. Make sure you're in the correct directory.")

def main():
    """Main test menu"""
    print("🎮 Titanic Launcher - Windows Detection Test")
    print("=" * 50)
    print("This script helps you test the Windows auto-detection")
    print("functionality without needing a Windows system.")
    print()
    
    while True:
        print("Choose test mode:")
        print("1. 🪟 Test Windows simulation mode")
        print("2. 🐧 Test normal Linux mode")
        print("3. 📋 Show what to look for")
        print("4. ❌ Exit")
        print()
        
        try:
            choice = input("Enter your choice (1-4): ").strip()
            
            if choice == "1":
                test_windows_mode()
            elif choice == "2":
                test_linux_mode()
            elif choice == "3":
                show_test_guide()
            elif choice == "4":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-4.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except EOFError:
            print("\n👋 Goodbye!")
            break
        
        print("\n" + "=" * 50 + "\n")

def show_test_guide():
    """Show what to look for during testing"""
    print("📋 Testing Guide")
    print("=" * 30)
    print()
    print("In Windows mode, you should see:")
    print("✅ Console message: '🧪 TEST MODE: Simulating Windows detection'")
    print("✅ Options dialog:")
    print("   - NO 'Download osu-wine' button")
    print("   - Help text says 'Windows detected: Games will launch directly without wine'")
    print("✅ Game launch: Attempts to run osu!.exe directly (will fail if no .exe exists)")
    print()
    print("In Linux mode, you should see:")
    print("✅ Console message: 'Platform detection: linux -> Linux'")
    print("✅ Options dialog:")
    print("   - 'Download osu-wine' button visible")
    print("   - Help text mentions osu-wine")
    print("✅ Game launch: Uses osu-wine (will fail if not installed)")
    print()
    print("Note: Actual game launching will fail without installed games,")
    print("but you can verify the UI changes and console messages.")
    print()

if __name__ == "__main__":
    main()
