from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user
from pydantic import BaseModel
from typing import List, Optional
import httpx
import os

router = APIRouter(prefix="/api/agent", tags=["agent"])

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

SYSTEM_PROMPT = """You are an operations assistant for ISSG (Indigenous Shared Services Group), helping manage vending machine technician rosters across WA Pilbara mining sites.

You assist the Operations Coordinator (Britt) and Operations Manager (Ryan) with:
- Roster queries (who is on site, when is next fly-in/fly-out)
- Flight booking drafts (Civeo/Workflow system via FMG)
- Leave and swing planning
- Mobilisation of relief staff (Pete Scully)

Eastern Hub context:
- Site: Christmas Creek (CC), operated for Fortescue (FMG)
- Amanda Inglis-Baillie (#764148): 8/6 roster, Java Village (JV), roster expires 18 Aug 2026
- Clive Ettia (#807406): 8/6 roster, Kariyarra Village (KV), roster expires 19 Aug 2026
- Pete Scully: Casual relief, mobilised when Amanda or Clive cannot travel
- Amanda and Clive strictly alternate — CC always has one technician on site
- Fly in/out day: Wednesday
- Flights: Qantas PER ↔ CC (QF2924 inbound, QF2925 outbound most common)
- Villages: JV = Java Village (orange), KV = Kariyarra Village (red)
- Flight bookings go through Ryan Clifton or Riel Sibley at Civeo

Be concise and operationally specific. Use plain language. Don't over-explain."""


class Message(BaseModel):
    role: str
    content: str


class AgentRequest(BaseModel):
    messages: List[Message]


@router.post("/chat")
async def agent_chat(request: AgentRequest, _=Depends(get_current_user)):
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="Claude API not configured")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            ANTHROPIC_URL,
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1024,
                "system": SYSTEM_PROMPT,
                "messages": [m.model_dump() for m in request.messages],
            }
        )

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Claude API error: {response.text}")

    data = response.json()
    reply = data["content"][0]["text"] if data.get("content") else ""
    return {"reply": reply}
