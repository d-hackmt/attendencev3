# Attendence/services/chatbot_service.py
import pandas as pd
import re
from datetime import datetime
from dateparser import parse as parse_date
from typing import Optional, Any
from pydantic import BaseModel
from langgraph.graph import StateGraph
from langchain_google_genai import ChatGoogleGenerativeAI
from Attendence.core.logger import get_logger

logger = get_logger(__name__)

# --- LLM Setup ---
# Note: Ensure GOOGLE_API_KEY is in .env or environment
try:
    gemini_llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        # temperature=0.5
    )
except Exception:
    logger.warning("Failed to initialize ChatGoogleGenerativeAI. Check API Key.")
    gemini_llm = None

# --- Load prompt examples ---
try:
    with open("Prompts/few_shot_prompt.txt", "r", encoding="utf-8") as f:
        EXAMPLES = f.read()
except FileNotFoundError:
    logger.warning("Prompts/few_shot_prompt.txt not found.")
    EXAMPLES = ""

# --- Schemas ---
class AppState(BaseModel):
    question: str
    code: Optional[str] = None
    result: Optional[Any] = None
    answer: Optional[str] = None


# --- Prompt Builder ---
def build_prompt(question: str, df: pd.DataFrame) -> str:
    schema = df.dtypes.to_string()
    head = df.head(2).to_string(index=False)
    
    return f"""
You are a pandas expert. You are given a DataFrame named `df` which tracks student attendance.
Each row is a student with a roll number, name, and dates (YYYY-MM-DD) as columns.
'P' means present; '' (empty string) means absent.

DataFrame schema:
{schema}

Sample data:
{head}

Your task is to write one line of Python code using pandas to answer the following question:

{EXAMPLES}

Question: {question}

Rules:
- Only use pandas methods, not print statements.
- Use df as the DataFrame name.
- Do NOT modify df.
- Only return the line of code (nothing else).
"""


# --- Date Normalization ---
def normalize_dates_in_question(inputs: dict, df) -> dict:
    question = inputs["question"]

    possible_phrases = re.findall(
        r"\b(?:today|yesterday|tomorrow|\d+\s+days?\s+(?:ago|before|after)|next\s+\w+|on\s+\w+day|\d{4}-\d{2}-\d{2})\b",
        question,
        re.IGNORECASE,
    )

    for phrase in possible_phrases:
        resolved = parse_date(phrase)
        if resolved:
            formatted = resolved.strftime("%Y-%m-%d")
            # If future date, return error
            if resolved > datetime.today():
                 # We return error as result immediately
                return {"error": f"⚠️ Attendance can't be checked for a future date: {formatted}"}
            
            # Check if date exists in columns
            if formatted not in df.columns:
                # Find latest date if possible
                date_cols = [c for c in df.columns if re.match(r"\d{4}-\d{2}-\d{2}", str(c))]
                latest = max(date_cols) if date_cols else "N/A"
                return {"error": f"⚠️ Date '{formatted}' not found in records. Latest date is: {latest}"}
            
            question = question.replace(phrase, formatted)

    return {"question": question}


# --- Nodes ---
def normalize_node(state: AppState, df) -> AppState:
    try:
        out = normalize_dates_in_question({"question": state.question}, df)
        if "error" in out:
            return AppState(question=state.question, result=out["error"], answer=out["error"])
        return AppState(question=out["question"])
    except Exception as e:
        logger.exception("Error in normalize_node")
        return AppState(question=state.question, result=f"Error processing dates: {e}")

def generate_code_node(state: AppState, df: pd.DataFrame) -> AppState:
    if not gemini_llm:
        return AppState(question=state.question, code="", result="LLM not initialized.")
    try:
        prompt = build_prompt(state.question, df)
        response = gemini_llm.invoke(prompt)
        return AppState(question=state.question, code=response.content.strip())
    except Exception as e:
        logger.exception("Error in generate_code_node")
        return AppState(question=state.question, code="", result=f"LLM Error: {e}")

def execute_code_node(state: AppState, df: pd.DataFrame) -> AppState:
    if not state.code:
         # Propagate previous error if any
        return AppState(question=state.question, result=state.result or "No code generated.")
    try:
        # unsafe eval - but user requested restricted env
        result = eval(state.code, {"df": df.copy()})
        return AppState(question=state.question, code=state.code, result=result)
    except Exception as e:
        return AppState(question=state.question, code=state.code, result=f"ERROR executing code: {str(e)}")

def format_response(state: AppState) -> AppState:
    question = state.question
    result = state.result

    # Generate new answer string
    if isinstance(result, str) and (result.startswith("ERROR") or result.startswith("⚠️")):
        new_answer = f"❌ Failed to answer: {result}"
    elif isinstance(result, (int, float, str, bool)) or hasattr(result, "__str__"):
        new_answer = f"📊 Answer to: '{question}' is → {result}"
    else:
        new_answer = f"✅ Answer to your question: '{question}'\n\n{result}"

    # Create new state with updated answer (override old answer)
    state_dict = state.model_dump()
    state_dict["answer"] = new_answer
    return AppState(**state_dict)


# --- Entry Point ---
def get_agent_for_df(df: pd.DataFrame):
    def norm(state): return normalize_node(state, df)
    def codegen(state): return generate_code_node(state, df)
    def execute(state): return execute_code_node(state, df)
    def respond(state): return format_response(state)

    graph = StateGraph(AppState)
    graph.add_node("normalize", norm)
    graph.add_node("generate_code", codegen)
    graph.add_node("execute", execute)
    graph.add_node("respond", respond)

    graph.set_entry_point("normalize")
    graph.add_edge("normalize", "generate_code")
    graph.add_edge("generate_code", "execute")
    graph.add_edge("execute", "respond")
    graph.set_finish_point("respond")

    return graph.compile()
