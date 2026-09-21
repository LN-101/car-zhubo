#!/usr/bin/env python3
"""Test script for Zhubo TTS integration."""

import sys
from pathlib import Path

# Add the backend app to path
sys.path.insert(0, str(Path(__file__).parent))

def test_zhubo_adapter_import():
    """Test that the Zhubo adapter can be imported."""
    try:
        from app.tts.adapters.zhubo_adapter import ZhuboTTSAdapter
        print("✓ ZhuboTTSAdapter imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import ZhuboTTSAdapter: {e}")
        return False

def test_zhubo_adapter_init():
    """Test that the Zhubo adapter can be initialized."""
    try:
        from app.tts.adapters.zhubo_adapter import ZhuboTTSAdapter
        adapter = ZhuboTTSAdapter(base_url="http://localhost:8765")
        print(f"✓ ZhuboTTSAdapter initialized with base_url: {adapter.base_url}")
        return True
    except Exception as e:
        print(f"✗ Failed to initialize ZhuboTTSAdapter: {e}")
        return False

def test_config_loading():
    """Test that the configuration loads correctly."""
    try:
        from app.config import Settings
        settings = Settings()
        print(f"✓ Configuration loaded")
        print(f"  - TTS Provider: {settings.tts_provider}")
        print(f"  - Zhubo TTS URL: {settings.zhubo_tts_url}")
        return True
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        return False

def test_tts_provider_detection():
    """Test that the TTS provider detection works."""
    try:
        from app.config import Settings
        from app.main import _tts_provider
        
        # Mock settings for testing
        import app.main
        original_settings = app.main.settings
        
        # Test zhubo provider
        app.main.settings = Settings(tts_provider="zhubo")
        provider = _tts_provider()
        if provider == "zhubo":
            print(f"✓ TTS provider detection works: zhubo")
        else:
            print(f"✗ Expected 'zhubo', got '{provider}'")
            return False
        
        # Test idextts2 provider
        app.main.settings = Settings(tts_provider="idextts2")
        provider = _tts_provider()
        if provider == "idextts2":
            print(f"✓ TTS provider detection works: idextts2")
        else:
            print(f"✗ Expected 'idextts2', got '{provider}'")
            return False
        
        # Restore original settings
        app.main.settings = original_settings
        return True
    except Exception as e:
        print(f"✗ Failed to test TTS provider detection: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Zhubo TTS Integration\n" + "="*50)
    
    tests = [
        test_config_loading,
        test_zhubo_adapter_import,
        test_zhubo_adapter_init,
        test_tts_provider_detection,
    ]
    
    results = []
    for test in tests:
        print(f"\n{test.__doc__}")
        results.append(test())
    
    print("\n" + "="*50)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    sys.exit(0 if passed == total else 1)
