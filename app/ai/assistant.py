"""
Core AI Assistant Coordinator for ALINA.
Combines deterministic intent routing, optional LLM enhancement,
TTS vocalization, and event logging.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.voice.speaker import speak
from app.ai.llm import get_llm_response
from app.database.repository import EventRepository
from app.config.settings import settings, logger


class AlinaAssistant:
    def __init__(self, db: Session, sensor_manager=None):
        from app.voice.commands import VoiceCommandRouter

        self.db = db
        self.sensor_manager = sensor_manager
        self.router = VoiceCommandRouter(db, sensor_manager=sensor_manager)
        self.event_repo = EventRepository(db)

    def ask(self, query: str, speak_output: bool = True) -> Dict[str, Any]:
        """
        Processes query from voice listener or web dashboard text input.
        Returns:
        - query: str
        - response: str
        - intent: str
        - data: Any
        """
        logger.info("AlinaAssistant received query: '%s'", query)

        # 1. First run deterministic command router
        route_result = self.router.process(query)

        # 2. If intent was unknown, check if optional LLM can provide a helpful answer
        final_response = route_result["response"]
        if route_result["intent"] == "unknown" and settings.AI_PROVIDER != "none":
            # Build inventory context for LLM
            active_foods = self.router.food_service.list_foods(status="active")
            items_str = ", ".join([f"{f['name']} ({f['days_remaining']} days left)" for f in active_foods])
            llm_reply = get_llm_response(query, context=f"Current foods: {items_str}")
            if llm_reply:
                final_response = llm_reply
                route_result["intent"] = "llm_generated"
                route_result["response"] = final_response

        # 3. Log event
        self.event_repo.add("ASSISTANT_QUERY", f"User: '{query}' | Alina: '{final_response}'")

        # 4. Speak response if requested
        if speak_output and settings.VOICE_ENABLED:
            speak(final_response, async_mode=True)

        return {
            "query": query,
            "response": final_response,
            "intent": route_result["intent"],
            "data": route_result.get("data"),
            "should_exit": route_result.get("should_exit", False)
        }
