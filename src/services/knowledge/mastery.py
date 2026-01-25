import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.logging.logger import get_logger

logger = get_logger("MasteryService")

class MasteryService:
    """
    Manages knowledge mastery tracking for users.
    Implements a simple version of Deep Knowledge Tracing.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            # Default storage path
            self.base_dir = Path(__file__).parent.parent.parent.parent / "data" / "user" / "mastery"
        else:
            self.base_dir = base_dir
        
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_user_file(self, user_id: str, kb_name: str) -> Path:
        return self.base_dir / f"{user_id}_{kb_name}_mastery.json"

    def load_mastery(self, user_id: str, kb_name: str) -> Dict:
        """Load mastery data for a specific user and knowledge base."""
        file_path = self._get_user_file(user_id, kb_name)
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load mastery data: {e}")
        
        return {"user_id": user_id, "kb_name": kb_name, "concepts": {}}

    def save_mastery(self, user_id: str, kb_name: str, data: Dict):
        """Save mastery data."""
        file_path = self._get_user_file(user_id, kb_name)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save mastery data: {e}")

    def update_mastery(self, user_id: str, kb_name: str, concept: str, score_delta: float):
        """
        Update mastery score for a concept.
        score_delta: typically in range [-1.0, 1.0].
        Positive delta means mastery improved, negative means struggle detected.
        """
        data = self.load_mastery(user_id, kb_name)
        concepts = data.setdefault("concepts", {})
        
        concept_data = concepts.setdefault(concept, {
            "score": 0.5, # Initial probabilistic score
            "hits": 0,
            "misses": 0,
            "last_updated": ""
        })
        
        # Simple probabilistic update (smoothing)
        # score = (old_score * weight + new_observation) / (weight + 1)
        # For now, let's just use a simpler additive/clamping approach
        old_score = concept_data.get("score", 0.5)
        new_score = max(0.0, min(1.0, old_score + (score_delta * 0.1)))
        
        concept_data["score"] = new_score
        if score_delta > 0:
            concept_data["hits"] = concept_data.get("hits", 0) + 1
        else:
            concept_data["misses"] = concept_data.get("misses", 0) + 1
            
        concept_data["last_updated"] = datetime.now().isoformat()
        
        self.save_mastery(user_id, kb_name, data)
        logger.info(f"Updated mastery for {user_id}/{kb_name}/{concept}: {new_score:.2f}")

    def get_weak_concepts(self, user_id: str, kb_name: str, threshold: float = 0.4) -> List[str]:
        """Find concepts where the user is struggling."""
        data = self.load_mastery(user_id, kb_name)
        concepts = data.get("concepts", {})
        
        return [c for c, d in concepts.items() if d.get("score", 0.5) < threshold]

    async def extract_concepts(self, text: str) -> List[str]:
        """Use LLM to extract main concepts from text."""
        from src.services.llm import complete as llm_complete
        
        prompt = f"Extract 1-3 key technical or academic concepts from the following text. Return only the concept names separated by commas:\n\n{text}"
        try:
            response = await llm_complete(
                prompt=prompt,
                system_prompt="You are a knowledge extraction assistant. Output only comma-separated concepts.",
                model="gpt-4o-mini" # Use a small model for extraction
            )
            return [c.strip() for c in response.split(",") if c.strip()]
        except Exception as e:
            logger.warning(f"Concept extraction failed: {e}")
            return []

    def predict_struggle(self, user_id: str, kb_name: str, retrieved_context: str) -> Optional[str]:
        """
        Check if the retrieved context contains concepts the user historically struggles with.
        This is a foundation for 'Predictive Assistance'.
        """
        weak_concepts = self.get_weak_concepts(user_id, kb_name)
        for concept in weak_concepts:
            if concept.lower() in retrieved_context.lower():
                return f"I noticed this topic involves '{concept}', which you've found challenging before. Would you like a quick refresher?"
        return None

# Global instance for easy access
_mastery_service = None

def get_mastery_service() -> MasteryService:
    global _mastery_service
    if _mastery_service is None:
        _mastery_service = MasteryService()
    return _mastery_service
