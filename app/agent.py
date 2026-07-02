# app/agent.py

import os
import sys
import google.auth
from google.adk.agents import Agent, LoopAgent, SequentialAgent, BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App, ResumabilityConfig
from google.adk.models import Gemini, LlmResponse
from google.adk.events import Event, EventActions
from google.genai import types
import google.genai as genai
from pydantic import BaseModel, Field
from typing import List, Literal, AsyncGenerator

# Import instructions, tools, and security functions
from app.instructions import ORCHESTRATOR_INSTRUCTION, COT_REWRITER_INSTRUCTION, ALIGN_EVALUATOR_INSTRUCTION
from app.tools import vibe_diff_tool, generate_image, is_eval
from app.security import scrub_pii, detect_prompt_injection

# Set up GCP project and location env variables
try:
    _, project_id = google.auth.default()
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
except Exception:
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "mock-project")
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id

os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

# --- Output Schemas ---

class EnrichedPrompt(BaseModel):
    cot_reasoning: str = Field(description="Internal Chain-of-Thought reasoning steps for prompt expansion.")
    final_reprompt: str = Field(description="The finalized, enriched descriptive prompt for the T2I model.")

class KeypointStatus(BaseModel):
    keypoint: Literal["Negation", "Counting", "Cross-Entity Binding", "Abstract Reasoning"] = Field(description="Keypoint evaluated.")
    passed: bool = Field(description="True if the rewritten prompt successfully aligns on this keypoint.")
    notes: str = Field(description="Specific feedback or rationale.")

class EvaluationResult(BaseModel):
    alignment_score: int = Field(description="Overall alignment score from 1 (poor) to 5 (excellent).", ge=1, le=5)
    rationale: str = Field(description="Detailed explanation of the score.")
    keypoints_checked: List[KeypointStatus] = Field(description="List of specific keypoints checked.")

# --- Callbacks ---

async def security_checkpoint_callback(callback_context: CallbackContext) -> None:
    """Security checkpoint that scrubs PII and checks for prompt injection."""
    raw_content = ""
    if callback_context.user_content and callback_context.user_content.parts:
        for part in callback_context.user_content.parts:
            if part.text:
                raw_content = part.text
                break
                
    scrubbed_content, redacted = scrub_pii(raw_content)
    
    callback_context.state["raw_prompt"] = raw_content
    if redacted:
        callback_context.state["redacted_categories"] = redacted
        print(f"[security] Redacted PII categories: {redacted}")
        
    if detect_prompt_injection(scrubbed_content):
        print("[security] Prompt injection attempt detected!")
        callback_context.state["security_event"] = True
        callback_context.state["quarantine"] = True
        # In non-evaluation execution, we raise ValueError to immediately interrupt and stop.
        # In evaluation execution, we let the flow run to completion to collect safety traces.
        if not is_eval:
            raise ValueError("Security Checkpoint Block: Prompt Injection detected.")
        
    # Apply scrubbed content back to user_content
    if callback_context.user_content and callback_context.user_content.parts:
        for part in callback_context.user_content.parts:
            if part.text:
                part.text = scrubbed_content
                break

async def skip_model_if_quarantined(callback_context: CallbackContext, llm_request: types.GenerateContentConfig) -> LlmResponse | None:
    """Bypasses LLM call completely if the session is flagged as quarantined."""
    if callback_context.state.get("quarantine"):
        print("[security] Bypassing model execution due to quarantine status.")
        return LlmResponse(
            content=types.Content(
                parts=[
                    types.Part.from_text(
                        '{"cot_reasoning": "Prompt injection detected.", "final_reprompt": "Blocked: Prompt Injection detected."}'
                    )
                ]
            )
        )
    return None

async def semantic_drift_callback(callback_context: CallbackContext) -> None:
    """Calculates semantic similarity between raw prompt and enriched prompt.
    If similarity < 0.65, raises an escalation event to quarantine the session.
    """
    raw_prompt = callback_context.state.get("raw_prompt")
    rewritten_data = callback_context.state.get("rewritten_prompt")
    
    if raw_prompt and rewritten_data:
        enriched_prompt = None
        if isinstance(rewritten_data, dict):
            enriched_prompt = rewritten_data.get("final_reprompt")
        else:
            enriched_prompt = getattr(rewritten_data, "final_reprompt", None)
            
        if enriched_prompt:
            try:
                client = genai.Client(vertexai=True)
                res_raw = client.models.embed_content(model="text-embedding-004", contents=raw_prompt)
                res_enriched = client.models.embed_content(model="text-embedding-004", contents=enriched_prompt)
                
                vec_raw = res_raw.embeddings[0].values
                vec_enriched = res_enriched.embeddings[0].values
                
                dot_product = sum(a * b for a, b in zip(vec_raw, vec_enriched))
                norm_raw = sum(a * a for a in vec_raw) ** 0.5
                norm_enriched = sum(b * b for b in vec_enriched) ** 0.5
                similarity = dot_product / (norm_raw * norm_enriched)
                
                print(f"[telemetry] Semantic similarity: {similarity:.4f}")
                
                if similarity < 0.65:
                    print("[security] Semantic drift too high! Quarantining session.")
                    callback_context.state["quarantine"] = True
                    if not is_eval:
                        raise ValueError("Semantic drift detected. Session quarantined.")
            except Exception as e:
                print(f"[warning] Semantic drift check fallback (API unavailable): {e}")

# --- Custom BaseAgent Loop Escalator ---

class LoopEscalator(BaseAgent):
    """Checks the AlignEvaluator score and escalates (breaking the LoopAgent) if criteria is satisfied."""
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        eval_result = ctx.session.state.get("evaluation_result")
        
        score = 0
        if eval_result:
            if isinstance(eval_result, dict):
                score = eval_result.get("alignment_score", 0)
            else:
                score = getattr(eval_result, "alignment_score", 0)
                
        print(f"[loop] Alignment Evaluator Score: {score}/5")
        
        is_quarantined = ctx.session.state.get("quarantine", False)
        
        # If score >= 4 or quarantined, escalate=True to terminate the loop
        if score >= 4 or is_quarantined:
            if is_quarantined:
                print("[loop] Session is quarantined. Exiting refinement loop.")
            else:
                print("[loop] Quality threshold satisfied. Exiting refinement loop.")
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            print("[loop] Quality threshold not met. Continuing refinement.")
            yield Event(author=self.name)

# --- Agent Definitions ---

cot_rewriter = Agent(
    name="cot_rewriter",
    model=Gemini(
        model="gemini-flash-latest",
        api_key="AIzaSyD-mock-key-value-12345",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=COT_REWRITER_INSTRUCTION,
    output_schema=EnrichedPrompt,
    output_key="rewritten_prompt",
    before_agent_callback=security_checkpoint_callback,
    before_model_callback=skip_model_if_quarantined,
    after_agent_callback=semantic_drift_callback
)

align_evaluator = Agent(
    name="align_evaluator",
    model=Gemini(
        model="gemini-flash-latest",
        api_key="AIzaSyD-mock-key-value-12345",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=ALIGN_EVALUATOR_INSTRUCTION,
    output_schema=EvaluationResult,
    output_key="evaluation_result"
)

loop_escalator = LoopEscalator(name="loop_escalator")

# Refinement loop runs up to 4 iterations
refinement_loop = LoopAgent(
    name="refinement_loop",
    sub_agents=[cot_rewriter, align_evaluator, loop_escalator],
    max_iterations=4
)

# Finalizer calls the Vibe Diff confirmation and T2I tool
finalizer = Agent(
    name="finalizer",
    model=Gemini(
        model="gemini-flash-latest",
        api_key="AIzaSyD-mock-key-value-12345",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are the final execution agent.
Your instructions:
1. If the session state has 'quarantine' set to True, do NOT call any tools. Output a report explaining that the request was blocked/quarantined.
2. Otherwise, call the vibe_diff_gate tool using the original raw prompt (state['raw_prompt']), the CoT reasoning (state['rewritten_prompt']['cot_reasoning']), and the final reprompt (state['rewritten_prompt']['final_reprompt']).
3. NOTE: The system will intercept your vibe_diff_gate call and return an `adk_request_confirmation` response. When you receive `{"confirmed": true}`, this means the user APPROVED the prompt! YOU MUST THEN immediately call the `generate_image` tool with the final reprompt. Do not finish until you have called `generate_image`.
4. Report back the final status and output.
""",
    tools=[vibe_diff_tool, generate_image]
)

# Root pipeline orchestrator
orchestrator = SequentialAgent(
    name="orchestrator",
    sub_agents=[refinement_loop, finalizer]
)

# Application runtime configuration
app = App(
    root_agent=orchestrator,
    name="app",
    resumability_config=ResumabilityConfig(is_resumable=True)
)
