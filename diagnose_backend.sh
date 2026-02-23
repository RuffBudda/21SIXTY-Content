#!/bin/bash
# Simple diagnostics script for backend startup failures
# This script tests the backend environment without needing systemd

set -e

echo "====== BACKEND STARTUP DIAGNOSTICS ======"
echo ""

# Check Python version
echo "✓ Python Version:"
python --version
echo ""

# Check if .env exists
echo "✓ Environment File:"
if [ -f /root/content-generator/.env ]; then
    echo "  ✓ .env file exists"
    echo "  Contains MASTER_PASSWORD: $(grep 'MASTER_PASSWORD=' /root/content-generator/.env | sed 's/=.*/=***/')"
else
    echo "  ✗ .env file NOT FOUND"
fi
echo ""

# Check installed packages
echo "✓ Installed Packages (Core Requirements):"
pip list | grep -E "^(fastapi|uvicorn|sqlalchemy|aiosqlite|openai|pythondotenv|assemblyai)" || echo "  ✗ Some packages missing"
echo ""

# Try importing everything
echo "✓ Testing Imports:"
cd /root/content-generator/backend || cd ./backend || true

python3 << 'EOF'
import sys
print("  Testing fastapi...", end=" ")
try:
    import fastapi
    print("✓")
except Exception as e:
    print(f"✗ {e}")
    sys.exit(1)

print("  Testing dotenv...", end=" ")
try:
    import dotenv
    print("✓")
except Exception as e:
    print(f"✗ {e}")
    sys.exit(1)

print("  Testing sqlalchemy...", end=" ")
try:
    import sqlalchemy
    print("✓")
except Exception as e:
    print(f"✗ {e}")
    sys.exit(1)

print("  Testing aiosqlite...", end=" ")
try:
    import aiosqlite
    print("✓")
except Exception as e:
    print(f"✗ {e}")
    sys.exit(1)

print("  Testing openai...", end=" ")
try:
    import openai
    print("✓")
except Exception as e:
    print(f"✗ {e}")
    sys.exit(1)

print("  Testing assemblyai...", end=" ")
try:
    import assemblyai
    print("✓")
except Exception as e:
    print(f"✗ {e}")
    sys.exit(1)

print("  Testing apscheduler...", end=" ")
try:
    import apscheduler
    print("✓")
except Exception as e:
    print(f"✗ {e}")
    sys.exit(1)

print("  All core imports OK!")
EOF

echo ""
echo "✓ Testing main.py syntax:"
python -m py_compile main.py && echo "  ✓ main.py syntax is valid" || echo "  ✗ Syntax error in main.py"
echo ""

echo "✓ Testing service startup (5 second timeout):"
timeout 5 python -m uvicorn main:app --host 0.0.0.0 --port 8001 || echo "  (Service started or timed out - expected behavior)"
echo ""

echo "====== END DIAGNOSTICS ======"
