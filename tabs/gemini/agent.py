from langchain_google_genai     import ChatGoogleGenerativeAI
from langchain_core.runnables   import RunnableLambda
from langchain_core.prompts     import PromptTemplate
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict

LLM    = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0.3)
prompt = PromptTemplate.from_template("List the major steps involved in {sector} manufacturing")
lchain = prompt | LLM | (lambda x: x.content.strip().split("\n"))

class FlowState(TypedDict, total=False):
    prompt  : str
    parsed  : Dict
    graph   : Dict
    steps   : List[str]

# --- Node 1: ParsePrompt ---
def node_parse(state: FlowState) -> FlowState:

    # Get the user's prompt:
    user_prompt = state["prompt"].lower()
    sector_list = ["cement", "steel", "power", "textile", "fertilizer", "petrochemicals"]
    factor_list = ["raw", "materials", "energy", "electricity", "heat", "CO2", "emissions", "waste", "labour", "costs"]

    # Identify the sector and relevant resources:
    sector = next((s for s in sector_list if s in user_prompt), "unknown")
    factor = [f for f in factor_list if f in user_prompt]

    # Create typed-dictionary:
    parsed = {
        "sectors": sector,
        "factors": factor
    }

    # Return typed-dictionary:
    return {**state, "parsed": parsed}

# --- Node 2: GenerateSteps ---
def node_steps(state: FlowState) -> FlowState:

    sector = state["parsed"]["sectors"]
    steps  = lchain.invoke({"sector": sector})
    steps  = [s.strip("-•. ").strip() for s in steps if s.strip()]

    return {**state, "steps": steps}

# --- Node 3: BuildGraphStructure ---
def node_build(state: FlowState) -> FlowState:
    steps = state["steps"]
    graph = {
        "nodes": [{"id": i, "label": step} for i, step in enumerate(steps)],
        "edges": [{"from": i, "to": i + 1} for i in range(len(steps) - 1)],
    }
    return {**state, "graph": graph}

# --- Build LangGraph ---
builder = StateGraph(FlowState)
builder.add_node("Parse", RunnableLambda(node_parse))
builder.add_node("Steps", RunnableLambda(node_steps))
builder.add_node("Build", RunnableLambda(node_build))

builder.set_entry_point("Parse")
builder.add_edge("Parse", "Steps")
builder.add_edge("Steps", "Build")
builder.add_edge("Build", END)

app = builder.compile()