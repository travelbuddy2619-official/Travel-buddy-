"""
Replanning Agent - Specialized agent for handling user modifications to itinerary
Handles chat-based customizations and re-plans the itinerary based on user feedback
"""
from __future__ import annotations

from typing import Optional, Dict, Any, List
from groq import AsyncGroq


class ReplanningAgent:
    """Agent specialized in modifying itineraries based on user feedback."""
    
    name = "Replanning Agent"
    description = "Handles user modification requests and adjusts the itinerary accordingly"
    
    def __init__(self, groq_api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.client = AsyncGroq(api_key=groq_api_key)
        self.model = model
    
    async def process_modification(
        self,
        current_itinerary: Dict[str, Any],
        user_request: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process a user's modification request and return updated itinerary.
        
        Args:
            current_itinerary: The current itinerary data
            user_request: User's modification request (e.g., "add more temples", "remove beach", "extend day 2")
            context: Additional context (weather, preferences, etc.)
        
        Returns:
            Modified itinerary with changes applied
        """
        print(f"✏️ [Replanning Agent] Processing modification: '{user_request}'...")
        
        result = {
            "success": False,
            "modified_itinerary": None,
            "changes_made": [],
            "explanation": None,
        }
        
        try:
            # Analyze the modification request
            analysis = await self._analyze_request(user_request, current_itinerary)
            
            # Generate modified itinerary
            modified = await self._generate_modification(
                current_itinerary, 
                user_request, 
                analysis,
                context
            )
            
            result["success"] = True
            result["modified_itinerary"] = modified["itinerary"]
            result["changes_made"] = modified["changes"]
            result["explanation"] = modified["explanation"]
            
            print(f"✓ [Replanning Agent] Applied {len(modified['changes'])} changes")
            
        except Exception as e:
            print(f"✗ [Replanning Agent] Error: {e}")
            result["error"] = str(e)
        
        return result
    
    async def _analyze_request(
        self, 
        request: str, 
        itinerary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze what kind of modification is being requested."""
        
        prompt = f"""Analyze this travel itinerary modification request.

User Request: "{request}"

Current Itinerary Summary:
- Destination: {itinerary.get('destination', 'Unknown')}
- Duration: {len(itinerary.get('days', []))} days
- Current activities: {self._summarize_activities(itinerary)}

Classify the modification type and extract key details:
1. Type: ADD_ACTIVITY, REMOVE_ACTIVITY, REPLACE_ACTIVITY, CHANGE_TIME, EXTEND_DAY, SHORTEN_DAY, ADD_DAY, REMOVE_DAY, CHANGE_RESTAURANT, OTHER
2. Target: Which day(s) or activity(s) are affected
3. Details: Specific changes requested

Respond in this JSON format:
{{
    "modification_type": "type",
    "target_days": [1, 2],
    "target_activities": ["activity name"],
    "new_preference": "what user wants instead",
    "reason": "why user wants this change"
}}"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a travel planning assistant. Analyze modification requests and respond with JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500,
            )
            
            import json
            content = response.choices[0].message.content.strip()
            # Extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            return json.loads(content)
            
        except Exception as e:
            print(f"⚠️ [Replanning Agent] Analysis failed: {e}")
            return {
                "modification_type": "OTHER",
                "target_days": [],
                "target_activities": [],
                "new_preference": request,
                "reason": "User requested change"
            }
    
    async def _generate_modification(
        self,
        itinerary: Dict[str, Any],
        request: str,
        analysis: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate the modified itinerary."""
        
        prompt = f"""Modify this travel itinerary based on the user's request.

CURRENT ITINERARY (JSON):
{self._itinerary_to_text(itinerary)}

USER REQUEST: "{request}"

ANALYSIS:
- Modification Type: {analysis.get('modification_type')}
- Target Days: {analysis.get('target_days')}
- Target Activities: {analysis.get('target_activities')}
- New Preference: {analysis.get('new_preference')}

CONTEXT:
{context if context else 'No additional context'}

REQUIREMENTS:
1. Apply the requested changes while keeping the rest of the itinerary intact
2. Maintain realistic timing (use actual visit durations)
3. Keep meal breaks (breakfast, lunch, tea, dinner) in place
4. Ensure logical flow between activities
5. All costs should be in Indian Rupees (₹)

Respond with a JSON object containing:
{{
    "itinerary": {{ ... the full modified itinerary ... }},
    "changes": ["list of changes made"],
    "explanation": "Brief explanation of what was changed and why"
}}

Keep the same JSON structure as the original itinerary."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert travel planner. Modify itineraries based on user requests. Respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=4000,
            )
            
            import json
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            return json.loads(content)
            
        except Exception as e:
            print(f"⚠️ [Replanning Agent] Modification generation failed: {e}")
            # Return original itinerary if modification fails
            return {
                "itinerary": itinerary,
                "changes": ["Unable to apply changes - keeping original"],
                "explanation": f"Error occurred: {str(e)}"
            }
    
    def _summarize_activities(self, itinerary: Dict[str, Any]) -> str:
        """Summarize activities in the itinerary."""
        activities = []
        for day in itinerary.get("days", []):
            for slot in day.get("schedule", []):
                if slot.get("activity"):
                    activities.append(slot["activity"])
        return ", ".join(activities[:10]) + ("..." if len(activities) > 10 else "")
    
    def _itinerary_to_text(self, itinerary: Dict[str, Any]) -> str:
        """Convert itinerary to readable text format."""
        import json
        # Return a condensed version to fit in prompt
        condensed = {
            "destination": itinerary.get("destination"),
            "startDate": itinerary.get("startDate"),
            "endDate": itinerary.get("endDate"),
            "days": []
        }
        
        for day in itinerary.get("days", []):
            day_summary = {
                "day": day.get("day"),
                "date": day.get("date"),
                "theme": day.get("theme"),
                "schedule": []
            }
            for slot in day.get("schedule", []):
                day_summary["schedule"].append({
                    "time": slot.get("time"),
                    "activity": slot.get("activity"),
                    "duration": slot.get("duration"),
                    "isMeal": slot.get("isMeal", False),
                    "mealType": slot.get("mealType")
                })
            condensed["days"].append(day_summary)
        
        return json.dumps(condensed, indent=2)
    
    async def chat(
        self,
        message: str,
        itinerary: Dict[str, Any],
        chat_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Handle a chat message about the itinerary.
        Can answer questions or make modifications.
        """
        print(f"💬 [Replanning Agent] Processing chat: '{message[:50]}...'")
        
        # Build conversation history
        messages = [
            {
                "role": "system",
                "content": """You are a helpful travel planning assistant. You can:
1. Answer questions about the itinerary
2. Suggest modifications based on user preferences
3. Provide additional information about places in the itinerary
4. Help with practical travel tips

Current itinerary context is provided. Be helpful and conversational.
If the user wants to make changes, confirm what they want before suggesting modifications.
All costs and budgets should be in Indian Rupees (₹)."""
            }
        ]
        
        # Add itinerary context
        messages.append({
            "role": "system",
            "content": f"Current Itinerary Summary:\n{self._itinerary_to_text(itinerary)}"
        })
        
        # Add chat history
        if chat_history:
            for msg in chat_history[-5:]:  # Keep last 5 messages for context
                messages.append(msg)
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
            )
            
            reply = response.choices[0].message.content.strip()
            
            # Check if this is a modification request
            is_modification = any(word in message.lower() for word in [
                "change", "modify", "add", "remove", "replace", "swap",
                "different", "instead", "skip", "extend", "shorten"
            ])
            
            return {
                "success": True,
                "reply": reply,
                "is_modification_request": is_modification,
                "should_replan": is_modification,
            }
            
        except Exception as e:
            print(f"✗ [Replanning Agent] Chat error: {e}")
            return {
                "success": False,
                "reply": "I'm sorry, I couldn't process your request. Please try again.",
                "error": str(e)
            }
