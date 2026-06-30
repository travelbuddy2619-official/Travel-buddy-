import asyncio
from types import SimpleNamespace

from app.agents.orchestrator import AgentOrchestrator


def test_veg_preference_request_is_routed_to_modify_itinerary(monkeypatch):
    orchestrator = AgentOrchestrator("dummy", "dummy", "dummy")

    async def raise_error(*args, **kwargs):
        raise RuntimeError("offline")

    monkeypatch.setattr(orchestrator.llm_client.chat.completions, "create", raise_error)

    result = asyncio.run(
        orchestrator._detect_chat_intent(
            "I need only veg hotels and restaurants.",
            {"destination": "Goa"},
            session_state={},
        )
    )

    assert result["intent_type"] == "modify_itinerary"


def test_llm_create_intent_is_overridden_for_modification_requests(monkeypatch):
    orchestrator = AgentOrchestrator("dummy", "dummy", "dummy")

    async def fake_create(*args, **kwargs):
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content='{"intent_type":"create_itinerary","action":null,"target":null,"details":"new trip","trip_request":{},"missing_fields":[],"clarifying_question":null}'
                    )
                )
            ]
        )

    monkeypatch.setattr(orchestrator.llm_client.chat.completions, "create", fake_create)

    result = asyncio.run(
        orchestrator._detect_chat_intent(
            "I need only veg hotels and restaurants.",
            {"destination": "Goa", "days": [{"day": 1}]},
            session_state={},
        )
    )

    assert result["intent_type"] == "modify_itinerary"


def test_booking_action_handles_missing_target_and_details():
    orchestrator = AgentOrchestrator("dummy", "dummy", "dummy")
    result = asyncio.run(
        orchestrator._handle_booking_action(
            {"target": None, "details": None},
            {"reply": "", "action": None, "action_data": None},
        )
    )

    assert result["action"] is None
    assert "What would you like to book?" in result["reply"]
