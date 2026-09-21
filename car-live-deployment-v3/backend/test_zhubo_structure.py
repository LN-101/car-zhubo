#!/usr/bin/env python3
"""Simple test script for Zhubo TTS integration (no dependencies required)."""

import ast
import sys
from pathlib import Path

def test_syntax_check():
    """Test that all modified files have valid Python syntax."""
    files_to_check = [
        "app/tts/adapters/zhubo_adapter.py",
        "app/main.py",
        "app/config.py"
    ]
    
    all_valid = True
    for file_path in files_to_check:
        full_path = Path(__file__).parent / file_path
        if not full_path.exists():
            print(f"✗ File not found: {file_path}")
            all_valid = False
            continue
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                ast.parse(f.read())
            print(f"✓ Syntax valid: {file_path}")
        except SyntaxError as e:
            print(f"✗ Syntax error in {file_path}: {e}")
            all_valid = False
    
    return all_valid

def test_adapter_structure():
    """Test that the Zhubo adapter has the required structure."""
    adapter_path = Path(__file__).parent / "app/tts/adapters/zhubo_adapter.py"
    
    with open(adapter_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_elements = [
        "class ZhuboTTSAdapter",
        "def synthesize(",
        "def health_check(",
        "def _map_voice_id(",
        "import httpx"
    ]
    
    all_present = True
    for element in required_elements:
        if element in content:
            print(f"✓ Found: {element}")
        else:
            print(f"✗ Missing: {element}")
            all_present = False
    
    return all_present

def test_config_structure():
    """Test that the config has Zhubo settings."""
    config_path = Path(__file__).parent / "app/config.py"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_elements = [
        "zhubo_tts_url",
        'http://localhost:8765'
    ]
    
    all_present = True
    for element in required_elements:
        if element in content:
            print(f"✓ Found in config: {element}")
        else:
            print(f"✗ Missing in config: {element}")
            all_present = False
    
    return all_present

def test_main_integration():
    """Test that main.py has Zhubo integration."""
    main_path = Path(__file__).parent / "app/main.py"
    
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_elements = [
        "ZhuboTTSAdapter",
        "_zhubo_adapter",
        "def _get_zhubo_adapter()",
        'if provider == "zhubo":'
    ]
    
    all_present = True
    for element in required_elements:
        if element in content:
            print(f"✓ Found in main.py: {element}")
        else:
            print(f"✗ Missing in main.py: {element}")
            all_present = False
    
    return all_present

def test_env_example():
    """Test that .env.example has Zhubo configuration."""
    env_path = Path(__file__).parent / ".env.example"
    
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_elements = [
        "ZHUBO_TTS_URL",
        "TTS_PROVIDER"
    ]
    
    all_present = True
    for element in required_elements:
        if element in content:
            print(f"✓ Found in .env.example: {element}")
        else:
            print(f"✗ Missing in .env.example: {element}")
            all_present = False
    
    return all_present

if __name__ == "__main__":
    print("Testing Zhubo TTS Integration (Structure)\n" + "="*50)
    
    tests = [
        ("Syntax Check", test_syntax_check),
        ("Adapter Structure", test_adapter_structure),
        ("Config Structure", test_config_structure),
        ("Main Integration", test_main_integration),
        ("Environment Example", test_env_example),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * 50)
        results.append(test_func())
    
    print("\n" + "="*50)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ Zhubo TTS integration structure is complete!")
    else:
        print("\n✗ Some checks failed, please review the output above.")
    
    sys.exit(0 if passed == total else 1)
