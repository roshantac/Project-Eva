#!/usr/bin/env python3
"""
Eva AI - Verification Script
Checks if all components are properly installed and configured
"""

import os
import sys
from pathlib import Path

def check_file(path, description):
    """Check if a file exists"""
    if Path(path).exists():
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description} - NOT FOUND")
        return False

def check_directory(path, description):
    """Check if a directory exists"""
    if Path(path).is_dir():
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description} - NOT FOUND")
        return False

def check_command(command, description):
    """Check if a command is available"""
    if os.system(f"which {command} > /dev/null 2>&1") == 0:
        print(f"✅ {description}")
        return True
    else:
        print(f"⚠️  {description} - NOT FOUND (may be optional)")
        return False

def main():
    """Main verification function"""
    print("🔍 Eva AI - Verification Script")
    print("=" * 50)
    print()
    
    all_checks = []
    
    # Check Python version
    print("📋 Python Environment:")
    python_version = sys.version_info
    if python_version >= (3, 9):
        print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        all_checks.append(True)
    else:
        print(f"❌ Python {python_version.major}.{python_version.minor} (need 3.9+)")
        all_checks.append(False)
    print()
    
    # Check virtual environment
    print("📋 Virtual Environment:")
    all_checks.append(check_directory("venv", "Virtual environment"))
    print()
    
    # Check configuration
    print("📋 Configuration:")
    all_checks.append(check_file(".env", ".env file"))
    all_checks.append(check_file(".env.example", ".env.example file"))
    print()
    
    # Check backend structure
    print("📋 Backend Structure:")
    all_checks.append(check_file("app/main.py", "Main application"))
    all_checks.append(check_directory("app/config", "Config directory"))
    all_checks.append(check_directory("app/engines", "Engines directory"))
    all_checks.append(check_directory("app/services", "Services directory"))
    all_checks.append(check_directory("app/models", "Models directory"))
    all_checks.append(check_directory("app/websocket", "WebSocket directory"))
    all_checks.append(check_directory("app/utils", "Utils directory"))
    print()
    
    # Check frontend
    print("📋 Frontend:")
    all_checks.append(check_directory("client", "Client directory"))
    all_checks.append(check_file("client/package.json", "Frontend package.json"))
    all_checks.append(check_file("client/src/App.jsx", "Frontend App.jsx"))
    print()
    
    # Check scripts
    print("📋 Scripts:")
    all_checks.append(check_file("install.sh", "Install script"))
    all_checks.append(check_file("start.sh", "Start script"))
    all_checks.append(check_file("run.py", "Run script"))
    print()
    
    # Check documentation
    print("📋 Documentation:")
    all_checks.append(check_file("README.md", "README"))
    all_checks.append(check_file("QUICKSTART.md", "Quick start guide"))
    all_checks.append(check_file("START_HERE.md", "Start here guide"))
    all_checks.append(check_file("INDEX.md", "Documentation index"))
    print()
    
    # Check dependencies
    print("📋 Dependencies:")
    all_checks.append(check_file("requirements.txt", "Python requirements"))
    all_checks.append(check_file("package.json", "NPM package.json"))
    print()
    
    # Check system commands
    print("📋 System Commands:")
    check_command("python3", "Python 3")
    check_command("node", "Node.js")
    check_command("npm", "NPM")
    check_command("mongod", "MongoDB")
    check_command("redis-server", "Redis (optional)")
    check_command("ffmpeg", "FFmpeg")
    check_command("ollama", "Ollama (optional)")
    print()
    
    # Check directories
    print("📋 Directories:")
    all_checks.append(check_directory("logs", "Logs directory"))
    all_checks.append(check_directory("temp", "Temp directory"))
    all_checks.append(check_directory("uploads", "Uploads directory"))
    print()
    
    # Summary
    print("=" * 50)
    passed = sum(all_checks)
    total = len(all_checks)
    percentage = (passed / total) * 100 if total > 0 else 0
    
    print(f"📊 Verification Results: {passed}/{total} checks passed ({percentage:.1f}%)")
    print()
    
    if percentage == 100:
        print("✅ All checks passed! Eva AI is ready to run.")
        print()
        print("🚀 Next steps:")
        print("   1. Configure .env file")
        print("   2. Run: ./start.sh")
        print("   3. Open: http://localhost:5173")
        return 0
    elif percentage >= 80:
        print("⚠️  Most checks passed. Review warnings above.")
        print("   Some optional components may be missing.")
        print()
        print("🚀 You can still run Eva AI:")
        print("   1. Configure .env file")
        print("   2. Run: ./start.sh")
        return 0
    else:
        print("❌ Several checks failed. Please:")
        print("   1. Run: ./install.sh")
        print("   2. Install missing dependencies")
        print("   3. Run this script again")
        return 1

if __name__ == "__main__":
    sys.exit(main())
