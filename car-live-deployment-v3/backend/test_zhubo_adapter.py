#!/usr/bin/env python3
"""
Test script for Zhubo TTS adapter.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.tts.adapters.zhubo_adapter import ZhuboTTSAdapter
from app.tts.models import TTSRequest

async def test_adapter():
    """Test the Zhubo TTS adapter."""
    adapter = ZhuboTTSAdapter(base_url="http://localhost:8765")
    
    print("Testing Zhubo TTS adapter...")
    
    # Test health check
    print("\n1. Health check:")
    is_healthy = await adapter.health_check()
    print(f"   Service healthy: {is_healthy}")
    
    if not is_healthy:
        print("   Warning: Service is not healthy. Make sure zhubo TTS is running on port 8765.")
        await adapter.close()
        return
    
    # Test synthesis
    print("\n2. Speech synthesis:")
    request = TTSRequest(
        text="大家好，欢迎来到汽车直播间。",
        voice_id="female_warm_01",
        speed_factor=1.0,
        tone="warm",
        intensity=0.5,
        volume=1.0
    )
    
    try:
        audio_data = await adapter.synthesize(request)
        print(f"   ✓ Synthesized {len(audio_data)} bytes")
        
        # Save to file for verification
        output_path = Path("/tmp/zhubo_test.wav")
        output_path.write_bytes(audio_data)
        print(f"   ✓ Saved to {output_path}")
        
    except Exception as e:
        print(f"   ✗ Synthesis failed: {e}")
    
    # Test voice mapping
    print("\n3. Voice ID mapping:")
    test_voices = [
        "female_warm_01",
        "female_energetic_01",
        "male_steady_01",
        "unknown_voice"
    ]
    
    for voice_id in test_voices:
        mapped = adapter._map_voice_id(voice_id)
        print(f"   {voice_id} -> {mapped}")
    
    await adapter.close()
    print("\n✓ Test completed")

if __name__ == "__main__":
    asyncio.run(test_adapter())
