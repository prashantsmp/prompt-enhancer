# dashboard/main.py

import os
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI(title="PromptEnhancer Dashboard")

# Base URL of the ADK agent running locally or in production
AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://localhost:8000")
APP_NAME = os.getenv("APP_NAME", "app")
USER_ID = os.getenv("USER_ID", "default-user")

# Resolve template directories
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, "templates")
os.makedirs(templates_dir, exist_ok=True)
templates = Jinja2Templates(directory=templates_dir)

class PromptRequest(BaseModel):
    prompt: str

def parse_session_info(session: dict) -> dict:
    """Parses session event logs to extract execution status and metadata."""
    session_id = session.get("id")
    state = session.get("state", {})
    events = session.get("events", [])
    
    # Retrieve base data from state
    raw_prompt = state.get("raw_prompt", "")
    redacted = state.get("redacted_categories", [])
    is_security_event = state.get("security_event", False)
    is_quarantined = state.get("quarantine", False)
    
    # Retrieve refinement data
    rewritten_data = state.get("rewritten_prompt", {})
    enriched_prompt = ""
    cot_reasoning = ""
    if rewritten_data:
        enriched_prompt = rewritten_data.get("final_reprompt", "")
        cot_reasoning = rewritten_data.get("cot_reasoning", "")
        
    eval_data = state.get("evaluation_result", {})
    alignment_score = eval_data.get("alignment_score", 0) if eval_data else 0
    eval_rationale = eval_data.get("rationale", "") if eval_data else ""
    
    # Count iterations of cot_rewriter runs
    iterations = sum(1 for e in events if e.get("author") == "cot_rewriter")
    
    # Identify pending interrupt call for vibe_diff_gate
    pending_interrupt_id = None
    responded_call_ids = set()
    
    # First, track all answered interrupts
    for event in events:
        parts = event.get("content", {}).get("parts", []) if event.get("content") else []
        for part in parts:
            func_resp = part.get("functionResponse") or part.get("function_response")
            if func_resp:
                resp_id = func_resp.get("id") or func_resp.get("response_id")
                if resp_id:
                    responded_call_ids.add(resp_id)
                
    # Now find any unanswered vibe_diff_gate call
    for event in reversed(events):
        parts = event.get("content", {}).get("parts", []) if event.get("content") else []
        for part in parts:
            func_call = part.get("functionCall") or part.get("function_call")
            if func_call:
                call_name = func_call.get("name")
                call_id = func_call.get("id")
                if call_name == "vibe_diff_gate" and call_id not in responded_call_ids:
                    pending_interrupt_id = call_id
                    break
        if pending_interrupt_id:
            break
            
    # Check if image has been generated
    image_url = None
    for event in reversed(events):
        parts = event.get("content", {}).get("parts", []) if event.get("content") else []
        for part in parts:
            func_resp = part.get("functionResponse") or part.get("function_response")
            if func_resp:
                if func_resp.get("name") == "generate_image":
                    output = func_resp.get("response") or func_resp.get("output") or {}
                    if isinstance(output, dict):
                        image_url = output.get("image_url")
                    break
        if image_url:
            break
            
    # Resolve overall status
    status = "running"
    if is_quarantined:
        status = "quarantined"
    elif is_security_event:
        status = "security_block"
    elif image_url:
        status = "completed"
    elif pending_interrupt_id:
        status = "pending_approval"
        
    return {
        "session_id": session_id,
        "status": status,
        "raw_prompt": raw_prompt,
        "redacted_categories": redacted,
        "cot_reasoning": cot_reasoning,
        "enriched_prompt": enriched_prompt,
        "alignment_score": alignment_score,
        "eval_rationale": eval_rationale,
        "iterations": iterations,
        "pending_interrupt_id": pending_interrupt_id,
        "image_url": image_url,
        "last_update": session.get("last_update_time")
    }

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """Renders the main dashboard page."""
    return templates.TemplateResponse(request, "index.html")

@app.get("/api/sessions")
async def list_sessions():
    """Queries the ADK SessionService to list all active sessions."""
    url = f"{AGENT_SERVICE_URL}/apps/{APP_NAME}/users/{USER_ID}/sessions"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10.0)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="Failed to fetch sessions from ADK service.")
            sessions = resp.json()
            # Parse and transform each session
            parsed = [parse_session_info(s) for s in sessions]
            # Sort by last update time descending
            parsed.sort(key=lambda x: x["last_update"] or 0, reverse=True)
            return parsed
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to agent service: {e}")

@app.post("/api/create")
async def create_session(req: PromptRequest):
    """Creates a new session and triggers the enhancement flow."""
    create_url = f"{AGENT_SERVICE_URL}/apps/{APP_NAME}/users/{USER_ID}/sessions"
    run_url = f"{AGENT_SERVICE_URL}/run"
    
    try:
        async with httpx.AsyncClient() as client:
            # 1. Create a new session
            create_resp = await client.post(create_url, json={}, timeout=10.0)
            if create_resp.status_code != 200:
                raise HTTPException(status_code=create_resp.status_code, detail="Failed to create session.")
            session = create_resp.json()
            session_id = session["id"]
            
            # 2. Trigger the agent execution loop with the user's prompt
            payload = {
                "app_name": APP_NAME,
                "user_id": USER_ID,
                "session_id": session_id,
                "new_message": {
                    "role": "user",
                    "parts": [{"text": req.prompt}]
                }
            }
            # We run it asynchronously. Since the agent will pause on the HITL gate, 
            # this call will complete and return the state up to the confirmation prompt.
            run_resp = await client.post(run_url, json=payload, timeout=30.0)
            if run_resp.status_code != 200:
                raise HTTPException(status_code=run_resp.status_code, detail="Agent run failed.")
                
            return {"status": "success", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting agent session: {e}")

@app.post("/api/approve/{session_id}")
async def approve_session(session_id: str):
    """Approves the pending enhanced prompt, resuming the execution to generate the image."""
    return await resume_session_with_decision(session_id, approved=True)

@app.post("/api/reject/{session_id}")
async def reject_session(session_id: str):
    """Rejects the pending prompt, halting or redirecting the execution."""
    return await resume_session_with_decision(session_id, approved=False)

async def resume_session_with_decision(session_id: str, approved: bool):
    """Helper to resume agent session execution with user's approval response."""
    session_url = f"{AGENT_SERVICE_URL}/apps/{APP_NAME}/users/{USER_ID}/sessions/{session_id}"
    run_url = f"{AGENT_SERVICE_URL}/run"
    
    async with httpx.AsyncClient() as client:
        # 1. Fetch the session details to identify the active interrupt ID
        resp = await client.get(session_url)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Session not found.")
            
        session_info = parse_session_info(resp.json())
        interrupt_id = session_info["pending_interrupt_id"]
        
        if not interrupt_id:
            raise HTTPException(status_code=400, detail="No pending approval gate found for this session.")
            
        # 2. Construct the resume payload containing the function response
        payload = {
            "app_name": APP_NAME,
            "user_id": USER_ID,
            "session_id": session_id,
            "new_message": {
                "role": "user",
                "parts": [
                    {
                        "function_response": {
                            "id": interrupt_id,
                            "name": "vibe_diff_gate",
                            "response": {
                                "approved": approved
                            }
                        }
                    }
                ]
            }
        }
        
        # 3. POST to /run to resume execution
        run_resp = await client.post(run_url, json=payload, timeout=30.0)
        if run_resp.status_code != 200:
            raise HTTPException(status_code=run_resp.status_code, detail="Failed to resume session.")
            
        return {"status": "success", "message": "Session resumed successfully."}
