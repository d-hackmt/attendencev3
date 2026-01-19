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
from langchain_groq import ChatGroq

logger = get_logger(__name__)

# --- LLM Setup ---
# Note: Ensure GOOGLE_API_KEY is in .env or environment
try:
    gemini_llm = ChatGroq(
    model_name = "llama-3.3-70b-versatile",
    temperature=0.3
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


# --- Context Engineering ---
def generate_context_summary(df: pd.DataFrame) -> str:
    """
    Generates a rich semantic summary of the DataFrame to help the LLM understand
    the structure (Students vs Dates) and key statistics.
    """
    total_students = len(df)
    
    # Identify Date Columns (YYYY-MM-DD)
    date_cols = [c for c in df.columns if re.match(r"\d{4}-\d{2}-\d{2}", str(c))]
    date_cols.sort()
    
    total_classes = len(date_cols)
    start_date = date_cols[0] if date_cols else "N/A"
    end_date = date_cols[-1] if date_cols else "N/A"
    
    # Identify Metadata Columns
    meta_cols = [c for c in df.columns if c not in date_cols]
    
    summary = f"""
    ### Dataset Structure (Wide Format)
    - **Rows**: Each row represents a SINGLE STUDENT.
    - **Metadata Columns**: {', '.join(map(str, meta_cols))} (Use these to identify students)
    - **Data Columns**: {total_classes} columns representing class dates from {start_date} to {end_date}.
    
    ### Statistics
    - **Total Students**: {total_students}
    - **Total Class Days**: {total_classes}
    - **Latest Date**: {end_date}
    
    ### Attendance Codes
    - 'P' = Present
    - '' (Empty String) or 'A' or NaN = Absent
    """
    return summary

# --- Prompt Builder ---
def build_prompt(question: str, df: pd.DataFrame) -> str:
    context_summary = generate_context_summary(df)
    head_sample = df.head(3).to_string(index=False)
    
    return f"""
You are a pandas expert. You are given a DataFrame named `df` tracking student attendance.

{context_summary}

### Sample Data (First 3 rows)
{head_sample}

### Task
Write a SINGLE line of Python code using pandas to answer the question.
- The `df` is already loaded.
- `date_cols` list is NOT pre-defined; filter columns using regex if needed (e.g. `[c for c in df.columns if re.match(r'\d{4}-\d{2}-\d{2}', str(c))]`).
- Return ONLY the code. No markdown, no explanations.

### Examples
{EXAMPLES}

### Question: {question}
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

# --- Prompt Builder ---
def build_prompt(question: str, df: pd.DataFrame) -> str:
    context_summary = generate_context_summary(df)
    head_sample = df.head(3).to_string(index=False)
    
    return f"""
You are a smart attendance assistant. You have access to a pandas DataFrame `df`.

{context_summary}

### Sample Data
{head_sample}

### Instructions
1. **Analyze the User's Input**:
   - If it is a **Greeting** (e.g., "hi", "hello") or **General Chat**, return `TEXT: <your friendly response>`.
   - If it is a **Data Question**, return `CODE: <single line of pandas code>`.

2. **Rules for Code**:
   - Use `df` variable.
   - Filter `date_cols` dynamically if needed.
   - Return ONLY the code prefixed with `CODE:`.

### Examples
Q: Hi, who are you?
A: TEXT: I am your Attendance Assistant. Ask me anything about class records!

Q: {EXAMPLES}

### User Input: {question}
"""

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
        response = gemini_llm.invoke(prompt).content.strip()
        
        # Intent Parsing
        if response.startswith("TEXT:"):
            # It's a greeting/conversational reply
            text_reply = response.replace("TEXT:", "").strip()
            return AppState(question=state.question, code=None, result=text_reply)
        elif response.startswith("CODE:"):
            code = response.replace("CODE:", "").strip()
            # Remove any markdown backticks if present
            code = code.replace("```python", "").replace("```", "").strip()
            return AppState(question=state.question, code=code)
        else:
            # Fallback: Assume it's code if it looks like code, else text
            if "df" in response or "pd." in response:
                return AppState(question=state.question, code=response)
            return AppState(question=state.question, code=None, result=response)
            
    except Exception as e:
        logger.exception("Error in generate_code_node")
        return AppState(question=state.question, code="", result=f"LLM Error: {e}")

def execute_code_node(state: AppState, df: pd.DataFrame) -> AppState:
    if not state.code:
        # No code to execute (was a greeting or error)
        return AppState(question=state.question, code=None, result=state.result)
    try:
        # Unsafe eval (as per user request domain)
        result = eval(state.code, {"df": df.copy(), "pd": pd, "re": re})
        return AppState(question=state.question, code=state.code, result=result)
    except Exception as e:
        return AppState(question=state.question, code=state.code, result=f"ERROR executing code: {str(e)}")

def format_response(state: AppState) -> AppState:
    """
    Synthesizes a final natural language response using the LLM.
    """
    question = state.question
    result = state.result
    
    # If the result is an error, just return it
    if isinstance(result, str) and (result.startswith("ERROR") or "Error" in result or "Traceback" in result):
         return AppState(question=question, result=result, answer=f"❌ I encountered an issue: {result}")

    # If we already have a text result (from greeting), refine it or pass through
    if not state.code and isinstance(result, str):
         # It was a greeting, just ensure it's clean
         return AppState(question=question, result=result, answer=result)

    # Synthesis Prompt
    summary_prompt = f"""
    You are an AI assistant summarizing data results.
    
    **User's Question**: "{question}"
    **Raw Data Result**: {result}
    
    **Task**: Write a helpful, natural language response.
    - Do NOT repeat the question.
    - Be concise but friendly.
    - If the result is a list of names, list them clearly.
    - If the result is a number, explain what it means.
    
    **Response**:
    """
    
    try:
        final_answer = gemini_llm.invoke(summary_prompt).content.strip()
    except Exception:
        final_answer = str(result)

    # Update state
    state_dict = state.model_dump()
    state_dict["answer"] = final_answer
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
