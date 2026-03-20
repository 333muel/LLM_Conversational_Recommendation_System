"""Agent response handling."""
import anyio
import uuid
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from apps.core.agent.workflow.graph.RecommendationGraph import get_recommendation_graph, get_browse_graph, get_baseline_graph
from apps.core.agent.workflow.state.RecommendationState import RecommendationState
from apps.core.agent.workflow.utils.ConversationLogger import ConversationLogger
from apps.database.Mongo import ConversationRepository, UserProfileRepository, ProductRepository
from apps.config.Tracing import get_logger
from apps.config.Setting import settings

logger = get_logger(__name__)


class RecommendationAgent:
    """Main agent for handling recommendation requests."""
    
    def __init__(self):
        self.recommendation_graph = get_recommendation_graph()
        self.browse_graph = get_browse_graph()
        self.baseline_graph = get_baseline_graph()
    
    async def process_request(
        self,
        user_message: str,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        top_k: Optional[int] = None,
        model: Optional[str] = None,
        llm_provider: Optional[str] = "ollama",
        algorithm: Optional[str] = None,
        background_tasks: Any = None
    ) -> Dict[str, Any]:
        """Process a user recommendation request."""
        try:
            user_id = user_id or "AFNT6ZJCYQN3WDIKUSWHJDXNND2Q"
            conversation_id = conversation_id or str(uuid.uuid4())
            
            history = ConversationRepository.get_history(conversation_id)
            session_start_time = ConversationRepository.get_conversation_created_at(conversation_id) or datetime.utcnow()
            
            # --- Regenerate: exclude previously recommended items ---
            _regenerate_keywords = ("regenerate", "different products", "something else", "more options", "other options", "show me different", "try again", "new recommendations", "different set", "new set", "give me a new", "replace the")
            _msg_lower = user_message.lower().strip()
            exclude_item_ids = None
            if any(kw in _msg_lower for kw in _regenerate_keywords):
                exclude_item_ids = ConversationRepository.get_last_recommended(conversation_id)
                if exclude_item_ids:
                    logger.info(f"Regenerate detected, excluding {len(exclude_item_ids)} previously recommended items")
            
            # --- Feedback Injection ---
            # Get any pending thumbs up/down feedback from previous turns
            pending_feedback = ConversationRepository.get_pending_feedback(conversation_id)
            feedback_context = ""
            if pending_feedback:
                feedback_items = []
                for item_id, info in pending_feedback.items():
                    product = ProductRepository.get_product_by_id(item_id)
                    title = product.get("product_title", "Unknown") if product else item_id
                    feedback_items.append(f"- {title}: {info['type']}")
                feedback_context = "\n[System Note: User feedback on previous recommendations:\n" + "\n".join(feedback_items) + "]"
                # Clear feedback after retrieving it for this turn's context
                ConversationRepository.clear_pending_feedback(conversation_id)

            _model = model or (settings.dashscope_model if llm_provider == "dashscope" else settings.ollama_model)
            initial_state: RecommendationState = {
                "user_message": user_message + (f"\n{feedback_context}" if feedback_context else ""),
                "constraints": None,
                "user_id": user_id,
                "top_k": top_k,
                "algorithm": algorithm,
                "model": _model,
                "llm_provider": llm_provider,
                "raw_recommendations": [],
                "product_details": [],
                "product_metadata": None,
                "final_response": None,
                "exclude_item_ids": exclude_item_ids,
                "messages": history + [{"role": "user", "content": user_message}]
            }
            
            result = await self.recommendation_graph.ainvoke(initial_state)
            
            final_response = result.get("final_response", "No response generated")
            product_details = result.get("product_details", [])
            metadata = result.get("product_metadata", {})
            
            # Update history and save
            updated_messages = result.get("messages", [])
            ConversationRepository.save_history(conversation_id, updated_messages)
            # Store last recommended for regenerate logic
            if product_details:
                ConversationRepository.save_last_recommended(conversation_id, [p.get("item_id") for p in product_details if p.get("item_id")])
            
            # --- Non-blocking Post-processing (Logging & Profile) ---
            if background_tasks:
                background_tasks.add_task(
                    self._post_process_interaction,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    user_message=user_message,
                    final_response=final_response,
                    product_details=product_details,
                    metadata=metadata,
                    session_start_time=session_start_time,
                    turn_num=len(updated_messages) // 2 + 1,
                    constraints=result.get("constraints")
                )
            else:
                # Fallback if no background tasks provided
                await self._post_process_interaction(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    user_message=user_message,
                    final_response=final_response,
                    product_details=product_details,
                    metadata=metadata,
                    session_start_time=session_start_time,
                    turn_num=len(updated_messages) // 2 + 1,
                    constraints=result.get("constraints")
                )
            
            return {
                "response": final_response,
                "conversation_id": conversation_id,
                "recommendations": product_details[:top_k or settings.recommendation_top_k],
                "raw_recommendations": result.get("raw_recommendations", [])[:top_k or settings.recommendation_top_k],
                "user_id": user_id,
                "success": True,
                "debug": {"algorithm_used": algorithm or "LightGCN"}
            }
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return {"response": f"Error: {e}", "conversation_id": conversation_id or str(uuid.uuid4()), "success": False}

    async def process_browse(
        self,
        user_message: str,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        llm_provider: Optional[str] = "ollama",
        algorithm: Optional[str] = None,
        background_tasks: Any = None
    ) -> Dict[str, Any]:
        """Process a browse discovery request."""
        try:
            user_id = user_id or "AFNT6ZJCYQN3WDIKUSWHJDXNND2Q"
            conversation_id = conversation_id or str(uuid.uuid4())
            
            history = ConversationRepository.get_history(conversation_id)
            session_start_time = ConversationRepository.get_conversation_created_at(conversation_id) or datetime.utcnow()
            
            # --- Feedback Injection ---
            # Get any pending thumbs up/down feedback from previous turns
            pending_feedback = ConversationRepository.get_pending_feedback(conversation_id)
            feedback_context = ""
            if pending_feedback:
                feedback_items = []
                for item_id, info in pending_feedback.items():
                    product = ProductRepository.get_product_by_id(item_id)
                    title = product.get("product_title", "Unknown") if product else item_id
                    feedback_items.append(f"- {title}: {info['type']}")
                feedback_context = "\n[System Note: User feedback on previous recommendations:\n" + "\n".join(feedback_items) + "]"
                # Clear feedback after retrieving it for this turn's context
                ConversationRepository.clear_pending_feedback(conversation_id)

            _model = settings.dashscope_model if llm_provider == "dashscope" else settings.ollama_model
            initial_state: RecommendationState = {
                "user_message": user_message + (f"\n{feedback_context}" if feedback_context else ""),
                "constraints": None,
                "user_id": user_id,
                "top_k": 20,
                "algorithm": algorithm,
                "model": _model,
                "llm_provider": llm_provider,
                "raw_recommendations": [],
                "product_details": [],
                "product_metadata": None,
                "final_response": None,
                "messages": history + [{"role": "user", "content": user_message}]
            }
            
            result = await self.browse_graph.ainvoke(initial_state)
            
            final_response = result.get("final_response", "I've found some products for you.")
            product_details = result.get("product_details", [])
            metadata = result.get("product_metadata", {})
            
            updated_messages = result.get("messages", [])
            ConversationRepository.save_history(conversation_id, updated_messages)
            
            # --- Non-blocking Post-processing ---
            if background_tasks:
                background_tasks.add_task(
                    self._post_process_interaction,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    user_message=user_message,
                    final_response=final_response,
                    product_details=product_details,
                    metadata=metadata,
                    session_start_time=session_start_time,
                    turn_num=len(updated_messages) // 2 + 1,
                    constraints=result.get("constraints")
                )
            else:
                await self._post_process_interaction(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    user_message=user_message,
                    final_response=final_response,
                    product_details=product_details,
                    metadata=metadata,
                    session_start_time=session_start_time,
                    turn_num=len(updated_messages) // 2 + 1,
                    constraints=result.get("constraints")
                )
            
            return {
                "response": final_response,
                "conversation_id": conversation_id,
                "products": product_details,
                "constraints": result.get("constraints", {}),
                "metadata": metadata,
                "success": True
            }
        except Exception as e:
            logger.error(f"Error: {e}")
            return {"response": f"Error: {e}", "conversation_id": conversation_id or str(uuid.uuid4()), "success": False}

    async def process_baseline(
        self,
        user_message: str,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        top_k: Optional[int] = None,
        model: Optional[str] = None,
        llm_provider: Optional[str] = "ollama",
        background_tasks: Any = None
    ) -> Dict[str, Any]:
        """Process a baseline request (no RecBole) through the specialized LangGraph."""
        try:
            user_id = user_id or "AFNT6ZJCYQN3WDIKUSWHJDXNND2Q"
            conversation_id = conversation_id or str(uuid.uuid4())
            
            history = ConversationRepository.get_history(conversation_id)
            session_start_time = ConversationRepository.get_conversation_created_at(conversation_id) or datetime.utcnow()
            
            # --- Feedback Injection ---
            # Get any pending thumbs up/down feedback from previous turns
            pending_feedback = ConversationRepository.get_pending_feedback(conversation_id)
            feedback_context = ""
            if pending_feedback:
                feedback_items = []
                for item_id, info in pending_feedback.items():
                    product = ProductRepository.get_product_by_id(item_id)
                    title = product.get("product_title", "Unknown") if product else item_id
                    feedback_items.append(f"- {title}: {info['type']}")
                feedback_context = "\n[System Note: User feedback on previous recommendations:\n" + "\n".join(feedback_items) + "]"
                # Clear feedback after retrieving it for this turn's context
                ConversationRepository.clear_pending_feedback(conversation_id)

            _model = model or (settings.dashscope_model if llm_provider == "dashscope" else settings.ollama_model)
            initial_state: RecommendationState = {
                "user_message": user_message + (f"\n{feedback_context}" if feedback_context else ""),
                "constraints": None,
                "user_id": user_id,
                "top_k": top_k or 20,
                "algorithm": None,
                "model": _model,
                "llm_provider": llm_provider,
                "raw_recommendations": [],
                "product_details": [],
                "product_metadata": None,
                "final_response": None,
                "messages": history + [{"role": "user", "content": user_message}],
                "mode": "baseline"
            }
            
            result = await self.baseline_graph.ainvoke(initial_state)
            
            final_response = result.get("final_response", "I've found some products for you.")
            product_details = result.get("product_details", [])
            metadata = result.get("product_metadata", {})
            
            updated_messages = result.get("messages", [])
            ConversationRepository.save_history(conversation_id, updated_messages)
            
            # --- Non-blocking Post-processing ---
            if background_tasks:
                background_tasks.add_task(
                    self._post_process_interaction,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    user_message=user_message,
                    final_response=final_response,
                    product_details=product_details,
                    metadata=metadata,
                    session_start_time=session_start_time,
                    turn_num=len(updated_messages) // 2 + 1,
                    constraints=result.get("constraints")
                )
            else:
                await self._post_process_interaction(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    user_message=user_message,
                    final_response=final_response,
                    product_details=product_details,
                    metadata=metadata,
                    session_start_time=session_start_time,
                    turn_num=len(updated_messages) // 2 + 1,
                    constraints=result.get("constraints")
                )
            
            return {
                "response": final_response,
                "conversation_id": conversation_id,
                "recommendations": product_details,
                "constraints": result.get("constraints", {}),
                "metadata": metadata,
                "success": True
            }
        except Exception as e:
            logger.error(f"Baseline error: {e}")
            return {"response": f"Error: {e}", "conversation_id": conversation_id or str(uuid.uuid4()), "success": False}

    async def _post_process_interaction(self, user_id, conversation_id, user_message, final_response, product_details, metadata, session_start_time, turn_num, constraints):
        """Asynchronous task to update user profile and log interaction."""
        try:
            # 1. Update User Profile (AI Analysis)
            from apps.core.agent.workflow.nodes.UpdateUserProfile import update_user_profile_node
            # Create a minimal state for the node
            mock_state = {
                "user_id": user_id,
                "user_message": user_message,
                "final_response": final_response
            }
            await update_user_profile_node.execute(mock_state)
            
            # 2. Log Interaction
            recommended_items = [{"item_id": p.get("item_id"), "price": p.get("price")} for p in product_details]
            fallback_triggered = metadata.get("source") in ["mixed_db_fallback", "recbole_default"] if metadata else False
            
            interaction_record = {
                "top_level": {
                    "participant_id": user_id,
                    "session_start_time": session_start_time.isoformat(),
                    "session_end_time": datetime.utcnow().isoformat()
                },
                "task_level": {
                    "profile": user_id,
                    "task_id": conversation_id,
                    "task_start_time": session_start_time.isoformat(),
                    "task_end_time": datetime.utcnow().isoformat()
                },
                "dialogue_turn": {
                    "turn_num": turn_num,
                    "timestamp": datetime.utcnow().isoformat(),
                    "speaker": "system",
                    "full_text": final_response,
                    "user_input": user_message,
                    "recommended_items": recommended_items,
                    "word_count": len(final_response.split()) if final_response else 0,
                    "clarification_question": final_response.strip().endswith("?") if final_response else False,
                    "fallback_triggered": fallback_triggered
                },
                "events": {
                    "refine_constraint": constraints
                }
            }
            ConversationLogger.log_interaction(interaction_record)
            
        except Exception as e:
            logger.error(f"Error in background post-processing: {e}")

    def _log_interaction(self, user_id, conversation_id, user_message, final_response, product_details, metadata, session_start_time, turn_num, constraints):
        """Deprecated: Internal helper to log hierarchical conversation data. Use _post_process_interaction instead."""
        pass

    async def explain_recommendation(
        self,
        user_id: str,
        conversation_id: str,
        item_id: str,
        user_query: Optional[str] = None,
        llm_provider: Optional[str] = "ollama"
    ) -> Dict[str, Any]:
        """Explain why a specific product was recommended with structured attribute scores."""
        from apps.core.llm import get_llm_client
        import json
        
        try:
            # 1. Get product details
            product = ProductRepository.get_product_by_id(item_id)
            if not product:
                return {"explanation": "Product not found.", "product_id": item_id, "success": False}
                
            # 2. Get user profile context
            profile = UserProfileRepository.get_profile(user_id)
            profile_context = f"User preferences: {profile.get('preferences', {})}" if profile else "No profile data yet."
            
            # 3. Create explanation prompt
            prompt = f"""You are a beauty sales expert. Explain why the following product was recommended to the user.
            
Product: {product.get('product_title')}
Description: {product.get('product_description')}
Rating: {product.get('product_avg_rating')}
Price: {product.get('product_price')}
Categories: {product.get('product_categories')}

User Context: {profile_context}
User Query: {user_query or "Why was this recommended?"}

First, provide a warm, 2-3 sentence explanation of why this product fits the user.
Second, provide attribute match scores on a scale of 0.0 to 1.0 for the following categories:
- category_match
- price_relevance
- quality_rating
- preference_alignment

Output format:
Explanation text...
JSON: {{"category_match": 0.0, "price_relevance": 0.0, "quality_rating": 0.0, "preference_alignment": 0.0}}
"""
            client = get_llm_client(provider=llm_provider)
            response = await client.generate(prompt=prompt)
            
            # Extract JSON for the "graph" (attribute scores)
            explanation_text = response.split("JSON:")[0].strip()
            attribute_scores = {"category_match": 0.8, "price_relevance": 0.7, "quality_rating": 0.9, "preference_alignment": 0.8}
            
            try:
                if "JSON:" in response:
                    json_str = response.split("JSON:")[1].strip()
                    attribute_scores = json.loads(json_str)
            except Exception as e:
                logger.error(f"Error parsing attribute scores from LLM: {e}")

            return {
                "explanation": explanation_text,
                "product_id": item_id,
                "attribute_scores": attribute_scores, # Frontend will use this for the "simple graph"
                "success": True
            }
        except Exception as e:
            logger.error(f"Explain error: {e}")
            return {"explanation": f"Error: {e}", "product_id": item_id, "success": False}

    async def log_item_selection(self, user_id: str, conversation_id: str, item_id: str):
        """Log a select_item event."""
        log_data = {
            "participant_id": user_id,
            "task_id": conversation_id,
            "event": "select_item",
            "item_id": item_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        ConversationLogger.log_interaction(log_data)

    async def extract_constraints(self, user_message: str, llm_provider: Optional[str] = "ollama") -> Dict[str, Any]:
        """Extract structured constraints from user message."""
        from apps.core.agent.workflow.utils.QueryProcessor import QueryProcessor
        processor = QueryProcessor(provider=llm_provider)
        constraints = await processor.process(user_message)
        return {
            "constraints": constraints,
            "intent": constraints.get("intent", "general discovery"),
            "success": True
        }

    async def filter_candidates(
        self, 
        constraints: Dict[str, Any], 
        user_id: str, 
        algorithm: Optional[str] = None,
        exclude_item_ids: Optional[List[str]] = None,
        limit: int = 25
    ) -> Dict[str, Any]:
        """Filter products based on constraints and RecBole candidates (Async-safe)."""
        from apps.core.agent.workflow.tools.RecBoleModel import get_recbole_engine
        
        try:
            # Get candidates (Top 100) - Run in thread to avoid blocking loop
            engine = get_recbole_engine(algorithm=algorithm)
            candidates = await anyio.to_thread.run_sync(
                engine.recommend, user_id, 100
            )
            candidate_asins = [c["item_id"] for c in candidates]
            
            # Filter - MongoDB calls are sync, run in thread too
            def _filter():
                return ProductRepository.filter_products(
                    candidate_asins,
                    constraints.get("category"),
                    constraints.get("max_price"),
                    constraints.get("min_rating"),
                    constraints.get("keywords"),
                    exclude_item_ids=exclude_item_ids
                )
            matching_products = await anyio.to_thread.run_sync(_filter)
            
            # Fallback logic
            final_products = matching_products[:limit]
            metadata = {"matched_count": len(matching_products), "source": "recbole_filtered"}
            
            exclude_set = set(exclude_item_ids or [])
            if len(final_products) < 5 and constraints.get("category"):
                db_fallback = await anyio.to_thread.run_sync(
                    ProductRepository.get_top_rated_by_category,
                    constraints["category"], 
                    10
                )
                existing_asins = {p["asin"] for p in final_products}
                for p in db_fallback:
                    if p["asin"] not in existing_asins and p["asin"] not in exclude_set:
                        final_products.append(p)
                        existing_asins.add(p["asin"])
                metadata["source"] = "mixed_db_fallback"

            if len(final_products) < limit:
                existing_asins = {p["asin"] for p in final_products}
                full_candidates = await anyio.to_thread.run_sync(
                    ProductRepository.get_products_by_ids,
                    candidate_asins[:50]
                )
                candidate_map = {p["asin"]: p for p in full_candidates}
                for asin in candidate_asins:
                    if asin not in existing_asins and asin not in exclude_set and asin in candidate_map:
                        final_products.append(candidate_map[asin])
                        existing_asins.add(asin)
                    if len(final_products) >= limit:
                        break
            
            # Format
            formatted = []
            for p in final_products:
                formatted.append({
                    "item_id": p.get("asin"),
                    "title": p.get("product_title", "Unknown"),
                    "description": p.get("product_description", ""),
                    "rating": p.get("product_avg_rating"),
                    "price": p.get("product_price", ""),
                    "categories": p.get("product_categories", ""),
                    "main_category": p.get("product_main_category", ""),
                    "image": p.get("product_image_url", ""),
                    "score": 0.0, "rank": 0
                })
                
            return {"products": formatted, "metadata": metadata, "success": True}
        except Exception as e:
            logger.error(f"Filter error: {e}")
            return {"products": [], "metadata": {"error": str(e)}, "success": False}

    async def generate_assistant_response(
        self,
        user_message: str,
        conversation_id: str,
        user_id: str,
        product_details: List[Dict[str, Any]],
        llm_provider: Optional[str] = "ollama",
        metadata: Optional[Dict[str, Any]] = None,
        background_tasks: Any = None
    ) -> Dict[str, Any]:
        """Generate Assistant response for given products."""
        try:
            from apps.core.agent.workflow.nodes.GenerateResponse import generate_response_node
            
            history = ConversationRepository.get_history(conversation_id)
            session_start_time = ConversationRepository.get_conversation_created_at(conversation_id) or datetime.utcnow()
            current_message = {"role": "user", "content": user_message}
            
            _model = settings.dashscope_model if llm_provider == "dashscope" else settings.ollama_model
            state: RecommendationState = {
                "user_message": user_message,
                "constraints": None,
                "user_id": user_id,
                "top_k": len(product_details),
                "algorithm": None,
                "model": _model,
                "llm_provider": llm_provider,
                "raw_recommendations": [],
                "product_details": product_details,
                "product_metadata": metadata,
                "final_response": None,
                "messages": history + [current_message]
            }
            
            result = await generate_response_node.execute(state)
            final_response = result.get("final_response", "Done.")
            
            # Update history
            updated_messages = state["messages"] + [{"role": "assistant", "content": final_response}]
            ConversationRepository.save_history(conversation_id, updated_messages)
            
            # --- Non-blocking Post-processing ---
            if background_tasks:
                background_tasks.add_task(
                    self._post_process_interaction,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    user_message=user_message,
                    final_response=final_response,
                    product_details=product_details,
                    metadata=metadata,
                    session_start_time=session_start_time,
                    turn_num=len(updated_messages) // 2 + 1,
                    constraints=None
                )
            else:
                await self._post_process_interaction(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    user_message=user_message,
                    final_response=final_response,
                    product_details=product_details,
                    metadata=metadata,
                    session_start_time=session_start_time,
                    turn_num=len(updated_messages) // 2 + 1,
                    constraints=None
                )
            
            return {"response": final_response, "conversation_id": conversation_id, "success": True}
        except Exception as e:
            logger.error(f"Respond error: {e}")
            return {"response": f"Error: {e}", "conversation_id": conversation_id, "success": False}

# Global agent instance
recommendation_agent = RecommendationAgent()

def get_recommendation_agent() -> RecommendationAgent:
    return recommendation_agent
