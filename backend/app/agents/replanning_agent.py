"""
Replanning Agent - Specialized agent for handling user modifications to itinerary
Handles chat-based customizations and re-plans the itinerary based on user feedback
"""
from __future__ import annotations

import copy
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
            
            if self._is_modification_noop(current_itinerary, modified.get("itinerary"), modified.get("changes")):
                result["success"] = False
                result["modified_itinerary"] = current_itinerary
                result["changes_made"] = modified.get("changes", [])
                result["explanation"] = modified.get("explanation", "Could not apply the requested modification.")
                print(f"✗ [Replanning Agent] Modification could not be applied: {result['explanation']}")
            else:
                result["success"] = True
                result["modified_itinerary"] = modified["itinerary"]
                result["changes_made"] = modified["changes"]
                result["explanation"] = modified["explanation"]
                print(f"✓ [Replanning Agent] Applied {len(modified['changes'])} changes")
        except Exception as e:
            print(f"✗ [Replanning Agent] Error: {e}")
            result["success"] = False
            result["modified_itinerary"] = current_itinerary
            result["changes_made"] = []
            result["explanation"] = str(e)
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
                max_tokens=6000,
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
                "changes": [],
                "explanation": f"Error occurred while modifying itinerary: {str(e)}"
            }
    
    def _is_modification_noop(
        self,
        original_itinerary: Dict[str, Any],
        modified_itinerary: Optional[Dict[str, Any]],
        changes: Optional[List[str]],
    ) -> bool:
        if not modified_itinerary or not isinstance(modified_itinerary, dict):
            return True
        if modified_itinerary == original_itinerary:
            return True
        if not changes:
            return True
        if len(changes) == 1 and "Unable to apply changes" in changes[0]:
            return True
        return False

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
                "content": """You are a powerful agentic travel planning assistant with access to real-time data. You can:
1. Create brand-new trip itineraries from scratch via conversation
2. Modify existing itineraries (add/remove/replace activities, change days, update schedule)
3. Find and compare flights, trains, buses via live API searches
4. Find and compare hotels and accommodations
5. Answer questions about destinations, weather, places, restaurants, visa, packing
6. Provide local tips, crowd predictions, best-time-to-visit advice
7. Help with travel budget planning in Indian Rupees (₹)

Always be proactive, helpful and specific. When the user asks you to modify something, do it directly.
All costs and budgets should be in Indian Rupees (₹).
If the user wants to make changes to the itinerary, confirm what changes you will make and apply them."""
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
