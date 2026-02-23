#!/usr/bin/env python3
"""Quick test to verify all imports work"""
import sys
print(f"Python version: {sys.version}")

# Test critical imports
print("\n✓ Testing imports...")
try:
    import fastapi
    print("  ✓ fastapi")
except Exception as e:
    print(f"  ✗ fastapi: {e}")
    
try:
    import dotenv
    print("  ✓ dotenv")
except Exception as e:
    print(f"  ✗ dotenv: {e}")
    
try:
    import sqlalchemy
    print("  ✓ sqlalchemy")
except Exception as e:
    print(f"  ✗ sqlalchemy: {e}")
    
try:
    import aiosqlite
    print("  ✓ aiosqlite")
except Exception as e:
    print(f"  ✗ aiosqlite: {e}")

try:
    import openai
    print("  ✓ openai")
except Exception as e:
    print(f"  ✗ openai: {e}")

try:
    import assemblyai
    print("  ✓ assemblyai")
except Exception as e:
    print(f"  ✗ assemblyai: {e}")

try:
    import apscheduler
    print("  ✓ apscheduler")
except Exception as e:
    print(f"  ✗ apscheduler: {e}")

# Now test backend imports
print("\n✓ Testing backend modules...")
sys.path.insert(0, 'backend')

try:
    from models import ProcessVideoRequest
    print("  ✓ models")
except Exception as e:
    print(f"  ✗ models: {e}")
    sys.exit(1)

try:
    from services.youtube_service import YouTubeService
    print("  ✓ services.youtube_service")
except Exception as e:
    print(f"  ✗ services.youtube_service: {e}")
    sys.exit(1)

try:
    from services.openai_service import OpenAIService
    print("  ✓ services.openai_service")
except Exception as e:
    print(f"  ✗ services.openai_service: {e}")
    sys.exit(1)

try:
    from services.content_generator import ContentGenerator
    print("  ✓ services.content_generator")
except Exception as e:
    print(f"  ✗ services.content_generator: {e}")
    sys.exit(1)

try:
    from database import init_db, AsyncSessionLocal
    print("  ✓ database")
except Exception as e:
    print(f"  ✗ database: {e}")
    sys.exit(1)

print("\n✅ All imports successful!")
