"""Agent response handling."""
import anyio
import uuid
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from apps.core.agent.workflow.graph.RecommendationGraph import get_recommendation_graph, get_browse_graph
from apps.core.agent.workflow.state.RecommendationState import RecommendationState
from apps.core.agent.workflow.utils.ConversationLogger import ConversationLogger
from apps.database.Mongo import ConversationRepository
from apps.config.Tracing import get_logger
from apps.config.Setting import settings

logger = get_logger(__name__)


class RecommendationAgent:
    """Main agent for handling recommendation requests."""
    
    def __init__(self):
        self.recommendation_graph = get_recommendation_graph()
        self.browse_graph = get_browse_graph()
    
    async def process_request(
        self,
        user_message: str,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        top_k: Optional[int] = None,
        model: Optional[str] = None,
        algorithm: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user recommendation request (Ask Assistant mode).
        """
        try:
            # ... existing logic ...
            if not user_id:
                user_id = "AFNT6ZJCYQN3WDIKUSWHJDXNND2Q"
            
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
            
            history = ConversationRepository.get_history(conversation_id)
            current_message = {"role": "user", "content": user_message}
            
            initial_state: RecommendationState = {
                "user_message": user_message,
                "constraints": None,
                "user_id": user_id,
                "top_k": top_k,
                "algorithm": algorithm,
                "model": model,
                "raw_recommendations": [],
                "product_details": [],
                "product_metadata": None,
                "final_response": None,
                "messages": history + [current_message]
            }
            
            logger.info(f"Processing ASK request for user: {user_id}")
            # The graph itself needs to be awaited if it's compiled with async nodes
            # However, langgraph works fine with async nodes.
            result = await self.recommendation_graph.ainvoke(initial_state)
            # ... rest of the extraction and logging ...
            
            # Extract results
            raw_recs = result.get("raw_recommendations", [])
            product_details = result.get("product_details", [])
            final_response = result.get("final_response", "No response generated")
            
            # Update history with AI response
            updated_messages = result.get("messages", [])
            if final_response and final_response != "No response generated":
                # Ensure the AI response is in the messages if not already there
                ai_message = {"role": "assistant", "content": final_response}
                # Check if it was already added by a node (GenerateResponseNode)
                last_message = updated_messages[-1] if updated_messages else None
                if not last_message or last_message.get("content") != final_response:
                    updated_messages.append(ai_message)
            
            # Save updated history to MongoDB
            ConversationRepository.save_history(conversation_id, updated_messages)
            
            # --- FS Logging (Extra Copy) ---
            # Capture ALL information for the FS record
            interaction_record = {
                "timestamp": datetime.now().isoformat(),
                "conversation_id": conversation_id,
                "user_id": user_id,
                "input": {
                    "user_message": user_message,
                    "history": history,
                    "parameters": {
                        "top_k": top_k,
                        "algorithm": algorithm,
                        "model": model
                    }
                },
                "output": {
                    "final_response": final_response,
                    "recommendations": product_details[:top_k],
                    "raw_recommendations": raw_recs[:top_k] if raw_recs else [],
                    "updated_history": updated_messages
                },
                "state_snapshot": result  # Full LangGraph state at end
            }
            ConversationLogger.log_interaction(interaction_record)
            # -------------------------------
            
            # Debug info
            debug_info = {
                "raw_recommendations_count": len(raw_recs),
                "product_details_count": len(product_details),
                "has_final_response": final_response is not None,
                "algorithm_used": algorithm or "LightGCN",
                "model_used": model or settings.ollama_model,
                "history_length": len(updated_messages)
            }
            
            # Return top_k recommendations (not all context items)
            requested_top_k = top_k or settings.recommendation_top_k
            top_recommendations = product_details[:requested_top_k]
            
            return {
                "response": final_response,
                "conversation_id": conversation_id,
                "recommendations": top_recommendations,
                "raw_recommendations": raw_recs[:requested_top_k] if raw_recs else [],
                "user_id": result.get("user_id"),
                "success": len(raw_recs) > 0 or len(updated_messages) > 0,
                "debug": debug_info
            }
            
        except Exception as e:
            logger.error(f"Error processing recommendation request: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "response": f"I encountered an error: {str(e)}",
                "conversation_id": conversation_id or str(uuid.uuid4()),
                "recommendations": [],
                "success": False,
                "error": str(e)
            }

    async def process_browse(
        self,
        user_message: str,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        algorithm: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a browse discovery request (Enhanced Browse mode).
        """
        try:
            if not user_id:
                user_id = "AFNT6ZJCYQN3WDIKUSWHJDXNND2Q"
            
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
            
            history = ConversationRepository.get_history(conversation_id)
            current_message = {"role": "user", "content": user_message}
            
            initial_state: RecommendationState = {
                "user_message": user_message,
                "constraints": None,
                "user_id": user_id,
                "top_k": 20, # Always return 20 for browse
                "algorithm": algorithm,
                "model": settings.ollama_model,
                "raw_recommendations": [],
                "product_details": [],
                "product_metadata": None,
                "final_response": None,
                "messages": history + [current_message]
            }
            
            logger.info(f"Processing BROWSE request for user: {user_id}")
            result = await self.browse_graph.ainvoke(initial_state)
            
            product_details = result.get("product_details", [])
            final_response = result.get("final_response", "I've found some products for you.")
            metadata = result.get("product_metadata", {})
            
            # Update history
            updated_messages = result.get("messages", [])
            if final_response:
                ai_message = {"role": "assistant", "content": final_response}
                last_message = updated_messages[-1] if updated_messages else None
                if not last_message or last_message.get("content") != final_response:
                    updated_messages.append(ai_message)
            
            ConversationRepository.save_history(conversation_id, updated_messages)
            
            # FS Logging
            interaction_record = {
                "timestamp": datetime.now().isoformat(),
                "mode": "browse",
                "conversation_id": conversation_id,
                "user_id": user_id,
                "input": {"user_message": user_message},
                "output": {
                    "final_response": final_response,
                    "product_count": len(product_details),
                    "metadata": metadata
                },
                "state_snapshot": result
            }
            ConversationLogger.log_interaction(interaction_record)
            
            return {
                "response": final_response,
                "conversation_id": conversation_id,
                "products": product_details,
                "constraints": result.get("constraints", {}),
                "metadata": metadata,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error processing browse request: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "response": f"I encountered an error: {str(e)}",
                "conversation_id": conversation_id or str(uuid.uuid4()),
                "products": [],
                "success": False,
                "error": str(e)
            }

    async def extract_constraints(self, user_message: str) -> Dict[str, Any]:
        """Extract structured constraints from user message."""
        from apps.core.agent.workflow.utils.QueryProcessor import QueryProcessor
        processor = QueryProcessor()
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
        algorithm: Optional[str] = None
    ) -> Dict[str, Any]:
        """Filter products based on constraints and RecBole candidates (Async-safe)."""
        from apps.core.agent.workflow.tools.RecBoleModel import get_recbole_engine
        from apps.database.Mongo import ProductRepository
        
        try:
            # Get candidates (Top 100) - Run in thread to avoid blocking loop
            engine = get_recbole_engine(algorithm=algorithm)
            candidates = await anyio.to_thread.run_sync(
                engine.recommend, user_id, 100
            )
            candidate_asins = [c["item_id"] for c in candidates]
            
            # Filter - MongoDB calls are sync, run in thread too
            matching_products = await anyio.to_thread.run_sync(
                ProductRepository.filter_products,
                candidate_asins,
                constraints.get("category"),
                constraints.get("max_price"),
                constraints.get("min_rating"),
                constraints.get("keywords")
            )
            
            # Fallback logic
            final_products = matching_products[:20]
            metadata = {"matched_count": len(matching_products), "source": "recbole_filtered"}
            
            if len(final_products) < 5 and constraints.get("category"):
                db_fallback = await anyio.to_thread.run_sync(
                    ProductRepository.get_top_rated_by_category,
                    constraints["category"], 
                    10
                )
                existing_asins = {p["asin"] for p in final_products}
                for p in db_fallback:
                    if p["asin"] not in existing_asins:
                        final_products.append(p)
                        existing_asins.add(p["asin"])
                metadata["source"] = "mixed_db_fallback"

            if len(final_products) < 20:
                existing_asins = {p["asin"] for p in final_products}
                full_candidates = await anyio.to_thread.run_sync(
                    ProductRepository.get_products_by_ids,
                    candidate_asins[:50]
                )
                candidate_map = {p["asin"]: p for p in full_candidates}
                for asin in candidate_asins:
                    if asin not in existing_asins and asin in candidate_map:
                        final_products.append(candidate_map[asin])
                        existing_asins.add(asin)
                    if len(final_products) >= 20: break
            
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
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate Assistant response for given products."""
        try:
            # We skip the graph and use GenerateResponseNode logic directly
            # to avoid re-running RecBole or filtering
            from apps.core.agent.workflow.nodes.GenerateResponse import generate_response_node
            
            history = ConversationRepository.get_history(conversation_id)
            current_message = {"role": "user", "content": user_message}
            
            state: RecommendationState = {
                "user_message": user_message,
                "constraints": None,
                "user_id": user_id,
                "top_k": len(product_details),
                "algorithm": None,
                "model": settings.ollama_model,
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
            
            return {"response": final_response, "conversation_id": conversation_id, "success": True}
        except Exception as e:
            logger.error(f"Respond error: {e}")
            return {"response": f"Error: {e}", "conversation_id": conversation_id, "success": False}


# Global agent instance
recommendation_agent: Optional[RecommendationAgent] = None


def get_recommendation_agent() -> RecommendationAgent:
    """Get or create recommendation agent instance."""
    global recommendation_agent
    if recommendation_agent is None:
        recommendation_agent = RecommendationAgent()
    return recommendation_agent

