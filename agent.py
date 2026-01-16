from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from typing import TypedDict, Annotated, Literal
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, AIMessage
from langgraph.prebuilt import ToolNode, tools_condition
import operator
from db import save_booking
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta


class booking_data(BaseModel):
    name: str = Field(..., description="person's first name")
    surname: str = Field(..., description="person's last name")
    problems: list[str] = Field(..., description="problems / symptoms the patient has, if not provided say not provided")
    mobile_no: int = Field(..., description="10 digit mobile number", ge=1000000000, le=9999999999)
    gender: Literal["male", "female"]
    booking_date: str = Field(..., description="Appointment date in YYYY-MM-DD format")
    booking_time: str = Field(..., description="Appointment time in HH:MM format (24-hour)")
    city: str = Field(..., description="City where patient wants appointment")


class state_llm(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    done: bool


@tool
def make_booking(data: booking_data):
    """
    Store booking in SQLite and confirm appointment.
    Only call this when ALL required fields are collected.
    """
    print("\n=== BOOKING CONFIRMED ===")
    print(data.model_dump())

    save_booking(data.model_dump())

    return f"DONE: Thank you! ✅ Your appointment has been successfully booked for {data.booking_date} at {data.booking_time} in {data.city}."


@tool
def get_current_datetime():
    """
    Get the current date and time information.
    Returns current date, time, day of week.
    Use this to calculate dates like 'tomorrow', 'next Monday', etc.
    """
    now = datetime.now()
    
    result = {
        "current_date": now.strftime("%Y-%m-%d"),
        "current_time": now.strftime("%H:%M"),
        "day_of_week": now.strftime("%A"),
        "current_datetime": now.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return f"Current datetime info: Date is {result['current_date']}, Time is {result['current_time']}, Day is {result['day_of_week']}"


@tool
def calculate_date(days_offset: int = 0):
    """
    Calculate a date based on offset from today.
    
    Args:
        days_offset: Number of days from today (0=today, 1=tomorrow, -1=yesterday)
    
    Returns the date in YYYY-MM-DD format
    """
    target_date = datetime.now() + timedelta(days=days_offset)
    return f"The date for {days_offset} days from today is: {target_date.strftime('%Y-%m-%d')} ({target_date.strftime('%A')})"


load_dotenv()

# Option 1: Groq (FREE - RECOMMENDED)
from langchain_groq import ChatGroq
model = ChatGroq(
    model="llama-3.3-70b-versatile",  # or "mixtral-8x7b-32768"
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)

# Option 2: Google Gemini (FREE Alternative)
# from langchain_google_genai import ChatGoogleGenerativeAI
# model = ChatGoogleGenerativeAI(
#     model="gemini-1.5-flash",
#     google_api_key=os.getenv("GOOGLE_API_KEY"),
#     temperature=0
# )

tools = [make_booking, get_current_datetime, calculate_date]
model_with_tools = model.bind_tools(tools)


def chat_node(state: state_llm) -> state_llm:
    system_message = AIMessage(
        content=(
            "You are a hospital appointment assistant.\n\n"
            "IMPORTANT INSTRUCTIONS:\n"
            "1. ALWAYS use get_current_datetime() or calculate_date() tools when the user mentions dates like 'today', 'tomorrow', 'next week', etc.\n"
            "2. When user says 'tomorrow', first call calculate_date(1).\n"
            "3. Convert times like '7pm' → 19:00 (24-hour format).\n"
            "4. Never guess dates or times.\n"
            "5. Only call make_booking() when ALL required fields are present.\n\n"
            "Required fields:\n"
            "- First name\n"
            "- Last name\n"
            "- Mobile number (10 digits)\n"
            "- Gender (male/female)\n"
            "- Problems / symptoms\n"
            "- Booking date (YYYY-MM-DD)\n"
            "- Booking time (HH:MM)\n"
            "- City\n\n"
            "important :- Keep responses WhatsApp-friendly with proper emoji, so that new user can easyly understand how to communicate "
        )
    )

    if not state["messages"] or not isinstance(state["messages"][0], AIMessage):
        state["messages"].insert(0, system_message)

    response = model_with_tools.invoke(state["messages"])
    state["messages"].append(response)

    # ✅ If booking completed → clear history
    if "DONE:" in response.content:
        state["done"] = True

        # Keep only last confirmation message
        state["messages"] = [response]

    return state



def build_graph():
    graph = StateGraph(state_llm)
    tool_node = ToolNode(tools)

    graph.add_node("chat_node", chat_node)
    graph.add_node("tool_node", tool_node)

    graph.add_edge(START, "chat_node")

    graph.add_conditional_edges(
        "chat_node",
        tools_condition,
        {
            "tools": "tool_node",
            "__end__": END
        }
    )

    graph.add_edge("tool_node", "chat_node")

    return graph.compile()