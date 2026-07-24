import json
from datetime import date, time
from uuid import UUID

from openai import OpenAI
from sqlalchemy.orm import Session

from backend.app.core.config import OPENAI_API_KEY
from backend.app.services.ai_tool_definitions import AI_TOOLS
from backend.app.services.ai_tools import (
    tool_book_appointment,
    tool_cancel_appointment,
    tool_get_available_slots,
    tool_request_schedule,
)

client = OpenAI(api_key=OPENAI_API_KEY)


SYSTEM_PROMPT = """
You are the Slotely AI receptionist, booking assistant, promoter,
and customer support agent.

Your responsibilities:

1. Help users understand the company and its services.
2. Help users find available appointment times.
3. Book appointments using the booking tool.
4. Cancel appointments using the cancellation tool.
5. Create schedule requests when the requested time is unavailable.
6. Answer general questions naturally and professionally.

Rules:

- Never claim an appointment is booked until the backend confirms it.
- Never invent availability.
- Always use the availability tool before booking.
- Never directly access or modify the database.
- Ask for missing information when necessary.
- Be concise, friendly, and professional.
"""


def execute_tool(
    tool_name: str,
    arguments: dict,
    db: Session,
    company_id: UUID,
):
    if tool_name == "get_available_slots":
        return tool_get_available_slots(
            db=db,
            company_id=company_id,
            service_id=UUID(arguments["service_id"]),
            requested_date=date.fromisoformat(
                arguments["requested_date"]
            ),
        )

    if tool_name == "book_appointment":
        return tool_book_appointment(
            db=db,
            company_id=company_id,
            service_id=UUID(arguments["service_id"]),
            appointment_date=date.fromisoformat(
                arguments["appointment_date"]
            ),
            start_time=time.fromisoformat(
                arguments["start_time"]
            ),
            customer_name=arguments.get("customer_name"),
            customer_email=arguments.get("customer_email"),
            customer_phone=arguments.get("customer_phone"),
        )

    if tool_name == "cancel_appointment":
        return tool_cancel_appointment(
            db=db,
            appointment_id=UUID(
                arguments["appointment_id"]
            ),
            cancellation_reason=arguments.get(
                "cancellation_reason"
            ),
        )

    if tool_name == "request_schedule":
        return tool_request_schedule(
            db=db,
            company_id=company_id,
            service_id=UUID(arguments["service_id"]),
            requested_date=date.fromisoformat(
                arguments["requested_date"]
            ),
            preferred_start_time=(
                time.fromisoformat(
                    arguments["preferred_start_time"]
                )
                if arguments.get("preferred_start_time")
                else None
            ),
            preferred_end_time=(
                time.fromisoformat(
                    arguments["preferred_end_time"]
                )
                if arguments.get("preferred_end_time")
                else None
            ),
            message=arguments.get("message"),
            customer_name=arguments.get("customer_name"),
            customer_email=arguments.get("customer_email"),
            customer_phone=arguments.get("customer_phone"),
        )

    return {
        "error": "Unknown AI tool",
    }


def run_ai_agent(
    db: Session,
    company_id: UUID,
    messages: list[dict],
):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            *messages,
        ],
        tools=AI_TOOLS,
        tool_choice="auto",
    )

    assistant_message = response.choices[0].message

    if not assistant_message.tool_calls:
        return {
            "message": assistant_message.content,
        }

    messages.append(
        {
            "role": "assistant",
            "content": assistant_message.content,
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    },
                }
                for tool_call in assistant_message.tool_calls
            ],
        }
    )

    for tool_call in assistant_message.tool_calls:
        arguments = json.loads(
            tool_call.function.arguments
        )

        result = execute_tool(
            tool_name=tool_call.function.name,
            arguments=arguments,
            db=db,
            company_id=company_id,
        )

        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(
                    result,
                    default=str,
                ),
            }
        )

    final_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            *messages,
        ],
    )

    return {
        "message": final_response.choices[0].message.content,
    }