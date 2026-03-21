import json
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from app.services.db_service import db_service
from app.services.ml_service import ml_service

# Load environment variables from .env file at repository root
load_dotenv()

@tool
def query_olap_tool(query: str) -> str:
    """Executes a SELECT query on PostgreSQL OLAP views to analyze prompt metrics. Returns JSON results."""
    try:
        if not query.strip().upper().startswith("SELECT"):
            return "Error: Only SELECT queries are allowed."
        
        results = db_service.fetch_all(query)
        # return a stringified dump; bounded to 50 rows 
        return json.dumps(results[:50], default=str)
    except Exception as e:
        return f"Database query error: {str(e)}"

@tool
def get_prompt_recommendations(prompt_text: str) -> str:
    """Get ML-based recommendations for how to improve a prompt's performance based on historical data rules."""
    res = ml_service.recommend_improvements(prompt_text)
    return json.dumps(res)

class ChatRequest(BaseModel):
    query: str

class SafeChatNVIDIA(ChatNVIDIA):
    def bind_tools(self, tools, **kwargs):
        kwargs["parallel_tool_calls"] = False
        return super().bind_tools(tools, **kwargs)

def get_agent_executor():
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY environment variable is not set")

    llm = SafeChatNVIDIA(
        model="meta/llama-3.1-70b-instruct",
        api_key=api_key,
        temperature=0.6,
        top_p=0.95,
        max_tokens=1024,
    )
    
    tools = [query_olap_tool, get_prompt_recommendations]
    
    # We will pass the system prompt directly in the messages stream below
    agent = create_react_agent(llm, tools)
    return agent

try:
    agent_executor = get_agent_executor()
except Exception as e:
    print(f"Warning: Could not initialize AI Agent. LLM key missing?: {e}")
    agent_executor = None

def run_agent_query(user_query: str) -> str:
    if not agent_executor:
        return "Agent is disconnected (check API keys)."
    try:
        system_prompt = """You are PromptLens, an advanced analytics AI agent and an elite Senior Prompt Engineer.
Your goal is to help users analyze ML prompt performance, extract insights from an OLAP warehouse, and recommend improvements for prompt texts.

You have access to PostgreSQL metrics through specific materialized views:
1. `mv_model_performance_arena` (Columns: model_name, attempts, avg_success, median_success)
2. `mv_language_performance` (Columns: programming_lang, prompts, success_rate, median_success)
3. `mv_prompt_feature_impact` (Columns: contains_examples, contains_code, contains_constraints, cnt, avg_success, median_success)
4. `mv_top_prompt_templates` (Columns: prompt_hash, prompt_text, uses, avg_success, median_success)
5. `mv_daily_model_success` (Columns: day, model_name, attempts, avg_success, median_success)

Whenever a user asks for data trends, explicitly query the OLAP tool using standard Postgres SQL.

BEHAVIOR AND TONE GUIDELINES:
1. **Be Data-Rich:** Never just list names or categories. ALWAYS include the supporting metrics (e.g., instead of "The top model is GPT-4", say "GPT-4 is the top model with a 75.4% average success rate over 4,217 attempts").
2. **Format Numbers Beautifully:** Round long decimals to 2 decimal places. Convert success rates/averages (like 0.66666) to readable percentages (like 66.67%).
3. **Act Like an Expert Prompt Engineer (No raw JSON dumps):** When evaluating prompts via `get_prompt_recommendations`, DO NOT just list raw JSON extracted features like an API (never say "contains_code is false, latency_ms is 100, cluster_group is unknown"). Instead, interpret them into actionable human advice.
   - Example Good Advice: "Your prompt lacks explicit constraints and examples, which typically hurts success rates. It is also quite short (only 7 words)."
   - Ignore internal backend fields like `latency_ms`, `tokens_used`, or `attempt_count`. Focus entirely on the linguistic and structural features (complexity, length, examples, constraints).
4. **Tool Calling:** DO NOT use parallel tool calls. If a user asks a complex multi-part question, complete one tool call, observe the results, and then smoothly synthesize all the insights into your final answer.

Always cite the data from the database or the ML service organically in your final response."""

        response = agent_executor.invoke({
            "messages": [
                ("system", system_prompt),
                ("user", user_query)
            ]
        })
        return response["messages"][-1].content
    except Exception as e:
        return f"Agent Error: {str(e)}"
