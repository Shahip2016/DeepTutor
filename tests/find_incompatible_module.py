import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

modules_to_try = [
    "src.logging.logger",
    "src.services.config.loader",
    "src.services.config.unified_config",
    "src.services.llm.utils",
    "src.services.llm.capabilities",
    "src.services.llm.exceptions",
    "src.services.llm.cloud_provider",
    "src.services.llm.local_provider",
    "src.services.llm.factory",
    "src.services.tts.factory",
    "src.services.knowledge.mastery",
    "src.agents.chat.chat_agent",
]

for mod_name in modules_to_try:
    print(f"Trying to import {mod_name}...", end=" ")
    try:
        __import__(mod_name)
        print("SUCCESS")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        # Keep going to see if others fail too
