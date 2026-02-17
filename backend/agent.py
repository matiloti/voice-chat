"""LangGraph conversational agent with Brave Search and memory."""

import logging
from typing import TypedDict, Annotated
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import operator

from config import settings
from tools import get_brave_search_tool

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a friendly voice assistant. You speak naturally and conversationally.
Keep responses concise — aim for 1-3 sentences unless the user asks for more detail.
Use contractions (I'm, you're, don't, can't). Avoid markdown formatting, bullet lists, code blocks, or URLs in your spoken responses.
Speak linearly — no parenthetical asides.
React naturally: brief acknowledgments like "Got it", "Sure thing", "Interesting" before substance.

IMPORTANT: When you need to search the web, you MUST say "Hold on, let me check that out" before using the brave_search tool. Always do this — it tells the user you're about to search.

When referencing memories from past conversations, be natural: "You mentioned last time that..." not "According to my memory records..."
If you're unsure about something, say so honestly and offer to search.

Today's date is {current_date}.

{memory_context}"""

HEARTBEAT_ADDENDUM = """

HEARTBEAT INSTRUCTION: This is an internal heartbeat prompt, not something the user said.
Based on the prompt below, decide whether to say something to the user or stay silent.
If you have nothing meaningful to say, respond with exactly: [SILENT]
If you do want to speak, respond naturally as if initiating conversation.

[HEARTBEAT: {heartbeat_name}]
{heartbeat_prompt}"""


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    memory_context: str
    current_date: str


def create_agent():
    """Build and compile the LangGraph agent."""
    llm = ChatOpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        temperature=0.7,
        streaming=True,
    )

    brave_search = get_brave_search_tool()
    tools = [brave_search]
    llm_with_tools = llm.bind_tools(tools)

    async def call_model(state: AgentState):
        system_content = SYSTEM_PROMPT.format(
            current_date=state.get("current_date", datetime.now().strftime("%Y-%m-%d")),
            memory_context=state.get("memory_context", "No memories from past conversations yet."),
        )
        system_msg = SystemMessage(content=system_content)
        messages = [system_msg] + state["messages"]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    def should_continue(state: AgentState) -> str:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "end"

    tool_node = ToolNode(tools)

    workflow = StateGraph(AgentState)
    workflow.add_node("call_model", call_model)
    workflow.add_node("tools", tool_node)
    workflow.set_entry_point("call_model")
    workflow.add_conditional_edges("call_model", should_continue, {
        "tools": "tools",
        "end": END,
    })
    workflow.add_edge("tools", "call_model")

    return workflow.compile()
