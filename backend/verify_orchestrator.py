import asyncio
from app.agents.orchestrator import AgentOrchestrator

class DummyCompletions:
    class Create:
        async def __call__(self, *args, **kwargs):
            raise RuntimeError('offline')
    def __init__(self):
        self.create = self.Create()

class DummyChat:
    def __init__(self):
        self.completions = DummyCompletions()

orchestrator = AgentOrchestrator('dummy','dummy','dummy')
orchestrator.llm_client.chat = DummyChat()

async def main():
    result = await orchestrator._detect_chat_intent('I need only veg hotels and restaurants.', {'destination': 'Goa'}, session_state={})
    print(result['intent_type'])

asyncio.run(main())
