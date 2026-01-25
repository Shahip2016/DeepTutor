import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.tts.factory import TTSFactory
from src.services.knowledge.mastery import get_mastery_service
from src.services.llm.factory import get_provider_presets

async def verify_tts():
    print("--- Verifying TTS Factory ---")
    try:
        provider = TTSFactory.get_provider("openai")
        print(f"✓ OpenAI TTS Provider initialized: {type(provider).__name__}")
        
        # Test config validation
        provider.validate_config({"model": "tts-1", "api_key": "test", "base_url": "http://test"})
        print("✓ TTS Config validation passed")
    except Exception as e:
        print(f"✗ TTS Verification failed: {e}")

async def verify_mastery():
    print("\n--- Verifying Mastery Service ---")
    try:
        service = get_mastery_service()
        user_id = "test_user"
        kb_name = "test_kb"
        
        # Test update
        service.update_mastery(user_id, kb_name, "Calculus", 1.0)
        data = service.load_mastery(user_id, kb_name)
        score = data["concepts"]["Calculus"]["score"]
        print(f"✓ Mastery update successful. Calculus score: {score}")
        
        # Test predictive assistance
        service.update_mastery(user_id, kb_name, "Algebra", -0.5)
        assistance = service.predict_struggle(user_id, kb_name, "Let's talk about Algebra.")
        if assistance:
            print(f"✓ Predictive assistance triggered: {assistance}")
        else:
            print("✗ Predictive assistance failed to trigger")
            
    except Exception as e:
        print(f"✗ Mastery Verification failed: {e}")

async def verify_llm_presets():
    print("\n--- Verifying LLM Presets ---")
    presets = get_provider_presets()
    if "google" in presets["api"]:
        print("✓ Google Gemini preset found in LLM Factory")
        print(f"  Models: {presets['api']['google']['models']}")
    else:
        print("✗ Google Gemini preset NOT found")

async def main():
    await verify_tts()
    await verify_mastery()
    await verify_llm_presets()
    print("\nVerification complete.")

if __name__ == "__main__":
    asyncio.run(main())
