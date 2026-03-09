"""Node for updating user profile and preferences."""
import json
from typing import Dict, Any, List, Optional
from apps.core.agent.workflow.nodes.BaseNode import BaseNode
from apps.core.agent.workflow.state.RecommendationState import RecommendationState
from apps.core.llm.Ollama import OllamaClient
from apps.database.Mongo import UserProfileRepository
from apps.config.Setting import settings
from apps.config.Tracing import get_logger

logger = get_logger(__name__)

class UpdateUserProfileNode(BaseNode):
    """Node that analyzes user message to update their profile preferences."""
    
    SYSTEM_PROMPT = """You are an e-commerce user profile analyst. 
Based on the user's message and the assistant's response, extract and update the user's preferences.
The current preferences are provided (if any). You should merge new insights into them.

Output ONLY a valid JSON object with the following keys:
- "favorite_categories": (list of strings) Product categories the user is interested in.
- "price_sensitivity": (string) One of ["Low", "Medium", "High"].
- "brand_preferences": (list of strings) Specific brands the user mentions or shows interest in.
- "product_features": (list of strings) Desired features (e.g., "organic", "fragrance-free", "long-lasting").
- "last_intent": (string) Short summary of the last user intent.

Current Preferences: {current_preferences}
User Message: "{user_message}"

If a preference is not explicitly mentioned or cannot be inferred, keep the existing value from the current preferences.
Return ONLY the JSON object. Do not include any other text."""

    def __init__(self, model: Optional[str] = None):
        self.client = OllamaClient(model=model or settings.ollama_model)

    async def execute(self, state: RecommendationState) -> Dict[str, Any]:
        """Analyze message and update user profile in MongoDB."""
        try:
            user_id = state.get("user_id") or "AFNT6ZJCYQN3WDIKUSWHJDXNND2Q"
            user_message = state.get("user_message", "")
            
            if not user_message:
                return {}

            # 1. Get existing profile
            profile = UserProfileRepository.get_profile(user_id)
            current_preferences = profile.get("preferences", {}) if profile else {}
            
            # 2. Analyze using LLM
            logger.info(f"Analyzing user preferences for user_id: {user_id}")
            analysis_prompt = self.SYSTEM_PROMPT.format(
                current_preferences=json.dumps(current_preferences),
                user_message=user_message
            )
            
            response = await self.client.generate(
                prompt=analysis_prompt,
                system_prompt="You are a helpful user profile analyst. Return ONLY JSON."
            )
            
            # Clean and parse JSON
            cleaned_response = response.strip()
            if "```json" in cleaned_response:
                cleaned_response = cleaned_response.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_response:
                cleaned_response = cleaned_response.split("```")[1].split("```")[0].strip()
            
            try:
                updated_preferences = json.loads(cleaned_response)
                logger.info(f"Extracted updated preferences for {user_id}: {updated_preferences}")
                
                # 3. Save to MongoDB
                UserProfileRepository.update_preferences(user_id, updated_preferences)
                logger.info(f"User profile updated for {user_id}")
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse preferences JSON: {e}. Response: {cleaned_response}")
            
            return {} # This node just performs a side effect
            
        except Exception as e:
            logger.error(f"Error in UpdateUserProfileNode: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}

# Node instance
update_user_profile_node = UpdateUserProfileNode()
