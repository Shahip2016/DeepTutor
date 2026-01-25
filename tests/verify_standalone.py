import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Mock logger if it fails to import
try:
    from src.logging.logger import get_logger
except Exception:
    class MockLogger:
        def info(self, msg): print(f"[INFO] {msg}")
        def error(self, msg): print(f"[ERROR] {msg}")
        def warning(self, msg): print(f"[WARN] {msg}")
    def get_logger(name): return MockLogger()
    print("Using Mock Logger")

# Test MasteryService (Local Implementation)
async def verify_mastery():
    print("\n--- Verifying Mastery Service ---")
    from src.services.knowledge.mastery import MasteryService
    
    # Use a temp directory for mastery data
    temp_dir = Path("./data/test_mastery")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    service = MasteryService(base_dir=temp_dir)
    user_id = "test_user"
    kb_name = "math_kb"
    
    # Test update
    print("Updating mastery for 'Calculus'...")
    service.update_mastery(user_id, kb_name, "Calculus", 1.0)
    
    data = service.load_mastery(user_id, kb_name)
    score = data["concepts"]["Calculus"]["score"]
    print(f"OK: Mastery update successful. Calculus score: {score}")
    
    # Test predictive assistance
    print("Simulating struggle in 'Algebra'...")
    service.update_mastery(user_id, kb_name, "Algebra", -2.0)
    
    assistance = service.predict_struggle(user_id, kb_name, "We will solve Algebra equations.")
    if assistance:
        print(f"OK: Predictive assistance triggered: {assistance}")
    else:
        print("FAIL: Predictive assistance failed to trigger")

    # Clean up
    for f in temp_dir.glob("*.json"):
        f.unlink()
    temp_dir.rmdir()

async def verify_tts_structure():
    print("\n--- Verifying TTS Provider Structure ---")
    from src.services.tts.factory import TTSFactory
    from src.services.tts.providers.openai import OpenAITTSProvider
    
    try:
        # Check factory
        print("Checking TTSFactory...")
        
        # Test config validation in OpenAI provider
        print("Validating OpenAI TTS config...")
        config = {
            "model": "tts-1",
            "api_key": "sk-test",
            "base_url": "https://api.openai.com/v1"
        }
        provider = OpenAITTSProvider(config)
        print("OK: OpenAITTSProvider initialized successfully")
        
    except Exception as e:
        print(f"FAIL: TTS Verification failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    await verify_mastery()
    await verify_tts_structure()
    print("\nVerification complete.")

if __name__ == "__main__":
    asyncio.run(main())
