import json
import logging
import re
from datetime import date, time
from uuid import UUID
from zoneinfo import ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from backend.app.models.company import Company
from backend.app.models.chat import ChatSession
from backend.app.models.service import Service
from backend.app.services.ai_tool_definitions import AI_TOOLS
from backend.app.services.ai_tools import (
    tool_book_appointment,
    tool_cancel_appointment,
    tool_get_available_slots,
    tool_list_customer_appointments,
    tool_request_schedule,
    tool_reschedule_appointment,
)
from backend.app.services.credential_service import get_openai_client
from backend.app.utils.date_utils import get_company_now

logger = logging.getLogger(__name__)


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
- Match service names to the supplied internal service IDs yourself.
- Never ask a customer to provide or understand a UUID.
- Never expose internal UUIDs unless explicitly asked for debugging.
- Interpret dates such as DD/MM/YYYY, month-name dates, tomorrow,
  and next Friday, then send tool dates in YYYY-MM-DD format.
- Before proposing a booking, collect name, valid email, and phone.
- Selecting a time is not confirmation. Call the booking tool to prepare
  a summary, then ask "Should I confirm this booking?"
- Use list_customer_appointments internally before cancellation or
  rescheduling. Never ask the customer for an appointment UUID.
- Cancellation and rescheduling always require an explicit final
  confirmation after you summarize the action.
- For cancellation, company_id comes from the current chat and appointment_id
  comes from the private appointment lookup. Never ask for either UUID.
- If several confirmed appointments match, ask for service/date/time to select
  one. A cancellation reason is optional; ask for it only when useful.
- Explain that after one appointment is selected, the customer can reply
  "yes", "confirm", "cancel it", or "proceed" to complete cancellation.
"""

CONFIRMATIONS = {
    "book it",
    "confirm",
    "confirm it",
    "cancel it",
    "okay book it",
    "okay, book it",
    "proceed",
    "yes",
    "yes confirm",
}
REJECTIONS = {
    "cancel",
    "do not",
    "don't",
    "never mind",
    "no",
    "stop",
}
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _normalized_reply(content: str) -> str:
    return " ".join(
        re.sub(r"[^a-z0-9@.' ]", " ", content.lower()).split()
    )


def _is_confirmation(content: str) -> bool:
    return _normalized_reply(content) in CONFIRMATIONS


def _is_rejection(content: str) -> bool:
    return _normalized_reply(content) in REJECTIONS


def _last_user_content(messages: list[dict]) -> str:
    return next(
        (
            message.get("content") or ""
            for message in reversed(messages)
            if message.get("role") == "user"
        ),
        "",
    )


def _service_name(
    db: Session,
    company_id: UUID,
    service_id: str,
) -> str:
    try:
        parsed_id = UUID(service_id)
    except (TypeError, ValueError):
        return "Selected service"
    service = (
        db.query(Service)
        .filter(
            Service.id == parsed_id,
            Service.company_id == company_id,
        )
        .first()
    )
    return service.name if service else "Selected service"


def _booking_summary(
    db: Session,
    company_id: UUID,
    arguments: dict,
) -> str:
    return (
        f"Service: {_service_name(db, company_id, arguments['service_id'])}\n"
        f"Date: {arguments['appointment_date']}\n"
        f"Time: {arguments['start_time']}\n"
        f"Name: {arguments['customer_name']}\n"
        f"Email: {arguments['customer_email']}\n"
        f"Phone: {arguments['customer_phone']}"
    )


def _time_tokens(value: str) -> set[str]:
    parsed = time.fromisoformat(value)
    return {
        parsed.strftime("%H:%M").lower(),
        parsed.strftime("%I:%M %p").lower().lstrip("0"),
    }


def _cancellation_reason(content: str) -> str | None:
    match = re.search(
        r"\breason(?:\s+is|\s*:)\s*(.+?)(?:[.!?]|$)",
        content,
        flags=re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def _latest_cancellation_reason(messages: list[dict]) -> str | None:
    for message in reversed(messages):
        if message.get("role") == "user":
            reason = _cancellation_reason(message.get("content") or "")
            if reason:
                return reason
    return None


def _stage_cancellation_from_reply(
    db: Session,
    company_id: UUID,
    chat_session: ChatSession,
    external_user_id: str | None,
    customer_email: str | None,
    cancellation_reason: str | None,
    assistant_content: str,
    appointments: list[dict],
) -> None:
    if chat_session.pending_action or "cancel" not in assistant_content.lower():
        return
    response_text = assistant_content.lower()
    matches = []
    for appointment in appointments:
        if appointment.get("status") != "confirmed":
            continue
        start_tokens = _time_tokens(appointment["start_time"])
        end_tokens = _time_tokens(appointment["end_time"])
        start_positions = [
            response_text.rfind(token)
            for token in start_tokens
            if token in response_text
        ]
        end_positions = [
            response_text.rfind(token)
            for token in end_tokens
            if token in response_text
        ]
        if start_positions and end_positions:
            matches.append(
                (max(start_positions + end_positions), appointment)
            )
    if not matches:
        return
    matches.sort(key=lambda item: item[0], reverse=True)
    if len(matches) > 1 and matches[0][0] == matches[1][0]:
        return
    match = matches[0][1]
    summary = (
        f"Appointment on {match['date']} from "
        f"{match['start_time']} to {match['end_time']}"
    )
    _save_pending_action(
        db,
        chat_session,
        {
            "action_type": "cancel_appointment",
            "appointment_id": match["appointment_id"],
            "company_id": str(company_id),
            "external_user_id": external_user_id,
            "customer_email": customer_email,
            "chat_session_id": str(chat_session.id),
            "summary": summary,
            "awaiting_confirmation": True,
            "arguments": {
                "appointment_id": match["appointment_id"],
                "cancellation_reason": cancellation_reason,
            },
        },
    )


def _save_pending_action(
    db: Session,
    chat_session: ChatSession,
    action: dict,
) -> None:
    action.setdefault("chat_session_id", str(chat_session.id))
    chat_session.pending_action = action
    db.commit()
    db.refresh(chat_session)
    logger.info(
        "Pending action created action_type=%s session_id=%s appointment_id=%s",
        action.get("action_type") or action.get("type"),
        chat_session.id,
        action.get("appointment_id"),
    )


def _clear_pending_action(
    db: Session,
    chat_session: ChatSession,
) -> None:
    chat_session.pending_action = None
    db.commit()
    db.refresh(chat_session)


def _execute_confirmed_action(
    db: Session,
    company_id: UUID,
    chat_session: ChatSession,
    external_user_id: str | None,
):
    pending = chat_session.pending_action or {}
    arguments = pending.get("arguments", {})
    action_type = pending.get("action_type") or pending.get("type")

    if not pending.get("awaiting_confirmation", True):
        _clear_pending_action(db, chat_session)
        return {"message": "There is no pending action to confirm."}
    if str(pending.get("company_id", company_id)) != str(company_id):
        _clear_pending_action(db, chat_session)
        return {"message": "I couldn't confirm that action for this company."}
    pending_user_id = pending.get("external_user_id")
    if pending_user_id and pending_user_id != external_user_id:
        _clear_pending_action(db, chat_session)
        return {"message": "I couldn't confirm that action for this customer."}

    # Consume confirmation state before executing so a repeated "yes" can
    # never perform the same mutation twice. Failures also clear the action.
    _clear_pending_action(db, chat_session)

    if action_type in {"booking", "book_appointment"}:
        appointment, error = tool_book_appointment(
            db=db,
            company_id=company_id,
            service_id=UUID(arguments["service_id"]),
            appointment_date=date.fromisoformat(
                arguments["appointment_date"]
            ),
            start_time=time.fromisoformat(arguments["start_time"]),
            external_user_id=external_user_id,
            customer_name=arguments["customer_name"],
            customer_email=arguments["customer_email"],
            customer_phone=arguments["customer_phone"],
        )
        if error:
            return {"message": f"I couldn't confirm the booking: {error}"}
        return {
            "message": (
                "Your appointment is confirmed for "
                f"{appointment.appointment_date} at "
                f"{appointment.start_time.strftime('%H:%M')}."
            )
        }

    if action_type in {"cancellation", "cancel_appointment"}:
        logger.info(
            "Cancellation service called company_id=%s appointment_id=%s",
            company_id,
            arguments.get("appointment_id"),
        )
        appointment, error = tool_cancel_appointment(
            db=db,
            company_id=company_id,
            appointment_id=UUID(arguments["appointment_id"]),
            cancellation_reason=arguments.get(
                "cancellation_reason"
            ),
        )
        if error:
            logger.info(
                "Cancellation result appointment_id=%s success=false",
                arguments.get("appointment_id"),
            )
            return {"message": f"I couldn't cancel the appointment: {error}"}
        logger.info(
            "Cancellation result appointment_id=%s success=true",
            arguments.get("appointment_id"),
        )
        return {
            "message": (
                "The appointment on "
                f"{appointment.appointment_date} at "
                f"{appointment.start_time.strftime('%H:%M')} "
                "has been cancelled."
            )
        }

    if action_type in {"reschedule", "reschedule_appointment"}:
        replacement, error = tool_reschedule_appointment(
            db=db,
            company_id=company_id,
            appointment_id=UUID(arguments["appointment_id"]),
            new_date=date.fromisoformat(arguments["new_date"]),
            new_start_time=time.fromisoformat(
                arguments["new_start_time"]
            ),
        )
        if error:
            return {
                "message": (
                    "I couldn't reschedule the appointment. "
                    f"The original remains confirmed. {error}"
                )
            }
        return {
            "message": (
                "Your appointment was rescheduled to "
                f"{replacement.appointment_date} at "
                f"{replacement.start_time.strftime('%H:%M')}."
            )
        }

    if action_type in {"schedule_request", "request_schedule"}:
        schedule_request, error = tool_request_schedule(
            db=db,
            company_id=company_id,
            service_id=UUID(arguments["service_id"]),
            requested_date=date.fromisoformat(arguments["requested_date"]),
            preferred_start_time=(
                time.fromisoformat(arguments["preferred_start_time"])
                if arguments.get("preferred_start_time")
                else None
            ),
            preferred_end_time=(
                time.fromisoformat(arguments["preferred_end_time"])
                if arguments.get("preferred_end_time")
                else None
            ),
            message=arguments.get("message"),
            external_user_id=external_user_id,
            customer_name=arguments.get("customer_name"),
            customer_email=arguments.get("customer_email"),
            customer_phone=arguments.get("customer_phone"),
        )
        if error:
            return {"message": f"I couldn't create the schedule request: {error}"}
        return {
            "message": (
                "Your schedule request was submitted for "
                f"{schedule_request.requested_date}. It is pending review."
            )
        }

    return {"message": "There is no pending action to confirm."}


def _build_company_context(
    db: Session,
    company_id: UUID,
) -> str:
    company = (
        db.query(Company)
        .filter(Company.id == company_id)
        .first()
    )
    services = (
        db.query(Service)
        .filter(
            Service.company_id == company_id,
            Service.is_active.is_(True),
        )
        .order_by(Service.name)
        .all()
    )

    if not company:
        return "The current company could not be loaded."

    try:
        company_now = get_company_now(company.timezone)
        current_datetime = company_now.isoformat()
    except ZoneInfoNotFoundError:
        current_datetime = (
            f"{date.today().isoformat()} "
            "(timezone database unavailable on this server)"
        )

    service_lines = "\n".join(
        (
            f"- {service.name}: internal service_id={service.id}; "
            f"duration={service.duration_minutes} minutes; "
            f"buffer={service.buffer_minutes} minutes"
        )
        for service in services
    )
    return (
        "Current company context:\n"
        f"Company: {company.name}\n"
        f"Description: {company.description or 'No description'}\n"
        f"Timezone: {company.timezone}\n"
        f"Current company date/time: {current_datetime}\n"
        "Active services (use IDs internally for tools, never ask the "
        "customer for them):\n"
        f"{service_lines or '- No active services'}"
    )


def execute_tool(
    tool_name: str,
    arguments: dict,
    db: Session,
    company_id: UUID,
    external_user_id: str | None = None,
    customer_email: str | None = None,
):
    if tool_name == "list_customer_appointments":
        service_id = arguments.get("service_id")
        appointments, error = tool_list_customer_appointments(
            db=db,
            company_id=company_id,
            external_user_id=external_user_id,
            customer_email=(
                arguments.get("customer_email")
                or customer_email
            ),
            service_id=UUID(service_id) if service_id else None,
            appointment_date=(
                date.fromisoformat(arguments["appointment_date"])
                if arguments.get("appointment_date")
                else None
            ),
            start_time=(
                time.fromisoformat(arguments["start_time"])
                if arguments.get("start_time")
                else None
            ),
        )
        if error:
            return {"error": error}
        return [
            {
                "appointment_id": str(appointment.id),
                "service_id": str(appointment.service_id),
                "date": appointment.appointment_date.isoformat(),
                "start_time": appointment.start_time.isoformat(),
                "end_time": appointment.end_time.isoformat(),
                "status": appointment.status,
            }
            for appointment in appointments
        ]

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
            external_user_id=external_user_id,
            customer_name=arguments.get("customer_name"),
            customer_email=arguments.get("customer_email"),
            customer_phone=arguments.get("customer_phone"),
        )

    if tool_name == "cancel_appointment":
        return tool_cancel_appointment(
            db=db,
            company_id=company_id,
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
            external_user_id=external_user_id,
            customer_name=arguments.get("customer_name"),
            customer_email=arguments.get("customer_email"),
            customer_phone=arguments.get("customer_phone"),
        )

    if tool_name == "reschedule_appointment":
        return tool_reschedule_appointment(
            db=db,
            company_id=company_id,
            appointment_id=UUID(arguments["appointment_id"]),
            new_date=date.fromisoformat(arguments["new_date"]),
            new_start_time=time.fromisoformat(
                arguments["new_start_time"]
            ),
        )

    return {
        "error": "Unknown AI tool",
    }


def run_ai_agent(
    db: Session,
    company_id: UUID,
    messages: list[dict],
    external_user_id: str | None = None,
    customer_context: dict | None = None,
    chat_session: ChatSession | None = None,
):
    customer_context = customer_context or {}
    latest_user_content = _last_user_content(messages)

    if chat_session and chat_session.pending_action:
        if _is_confirmation(latest_user_content):
            logger.info(
                "Pending action confirmation received session_id=%s action_type=%s",
                chat_session.id,
                chat_session.pending_action.get("action_type")
                or chat_session.pending_action.get("type"),
            )
            return _execute_confirmed_action(
                db=db,
                company_id=company_id,
                chat_session=chat_session,
                external_user_id=external_user_id,
            )
        if _is_rejection(latest_user_content):
            _clear_pending_action(db, chat_session)
            return {
                "message": (
                    "Okay, I have not made that change. "
                    "What would you like to do instead?"
                )
            }

    company_context = _build_company_context(
        db=db,
        company_id=company_id,
    )
    customer_prompt = (
        "Known customer context (do not ask again for non-empty values):\n"
        f"external_user_id: {external_user_id or 'missing'}\n"
        f"customer_name: {customer_context.get('customer_name') or 'missing'}\n"
        f"customer_email: {customer_context.get('customer_email') or 'missing'}\n"
        f"customer_phone: {customer_context.get('customer_phone') or 'missing'}"
    )
    pending_prompt = (
        "\nPending action awaiting confirmation:\n"
        f"{json.dumps(chat_session.pending_action, default=str)}"
        if chat_session and chat_session.pending_action
        else ""
    )
    ai_client = get_openai_client(db)
    response = ai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    f"{SYSTEM_PROMPT}\n\n{company_context}\n\n"
                    f"{customer_prompt}{pending_prompt}"
                ),
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

    listed_appointments = []
    for tool_call in assistant_message.tool_calls:
        arguments = json.loads(
            tool_call.function.arguments
        )

        try:
            tool_name = tool_call.function.name
            if (
                chat_session
                and tool_name == "book_appointment"
            ):
                for field in (
                    "customer_name",
                    "customer_email",
                    "customer_phone",
                ):
                    arguments[field] = (
                        arguments.get(field)
                        or customer_context.get(field)
                    )

                missing = [
                    field
                    for field in (
                        "customer_name",
                        "customer_email",
                        "customer_phone",
                    )
                    if not str(arguments.get(field) or "").strip()
                ]
                if missing:
                    result = {
                        "error": (
                            "Ask only for these missing customer fields: "
                            + ", ".join(missing)
                        )
                    }
                elif not EMAIL_PATTERN.fullmatch(
                    arguments["customer_email"].strip()
                ):
                    result = {
                        "error": (
                            "The customer email is invalid. Ask for "
                            "a valid email address."
                        )
                    }
                else:
                    action = {
                        "action_type": "book_appointment",
                        "company_id": str(company_id),
                        "external_user_id": external_user_id,
                        "customer_email": arguments.get("customer_email"),
                        "awaiting_confirmation": True,
                        "summary": _booking_summary(
                            db,
                            company_id,
                            arguments,
                        ),
                        "arguments": arguments,
                    }
                    _save_pending_action(
                        db,
                        chat_session,
                        action,
                    )
                    result = {
                        "confirmation_required": True,
                        "summary": _booking_summary(
                            db,
                            company_id,
                            arguments,
                        ),
                        "instruction": (
                            "Show this complete summary and ask exactly: "
                            "Should I confirm this booking? Do not claim "
                            "it is booked yet."
                        ),
                    }
            elif (
                chat_session
                and tool_name in {
                    "cancel_appointment",
                    "reschedule_appointment",
                }
            ):
                appointment_id = arguments.get("appointment_id")
                appointments, lookup_error = (
                    tool_list_customer_appointments(
                        db=db,
                        company_id=company_id,
                        external_user_id=external_user_id,
                        customer_email=customer_context.get(
                            "customer_email"
                        ),
                    )
                )
                match = next(
                    (
                        appointment
                        for appointment in appointments or []
                        if str(appointment.id) == appointment_id
                        and appointment.status == "confirmed"
                    ),
                    None,
                )
                if lookup_error or not match:
                    result = {
                        "error": (
                            "No matching confirmed appointment belongs "
                            "to this customer."
                        )
                    }
                else:
                    action_type = (
                        "cancel_appointment"
                        if tool_name == "cancel_appointment"
                        else "reschedule_appointment"
                    )
                    summary = (
                        f"Existing appointment: "
                        f"{_service_name(db, company_id, str(match.service_id))}, "
                        f"{match.appointment_date}, "
                        f"{match.start_time.strftime('%H:%M')}"
                    )
                    if action_type == "reschedule_appointment":
                        summary += (
                            f"\nReplacement: {arguments['new_date']}, "
                            f"{arguments['new_start_time']}"
                        )
                    _save_pending_action(
                        db,
                        chat_session,
                        {
                            "action_type": action_type,
                            "appointment_id": appointment_id,
                            "company_id": str(company_id),
                            "external_user_id": external_user_id,
                            "customer_email": customer_context.get(
                                "customer_email"
                            ),
                            "summary": summary,
                            "awaiting_confirmation": True,
                            "arguments": arguments,
                        },
                    )
                    logger.info(
                        "Appointment selected for confirmation session_id=%s "
                        "appointment_id=%s",
                        chat_session.id,
                        appointment_id,
                    )
                    result = {
                        "confirmation_required": True,
                        "summary": summary,
                        "instruction": (
                            "Summarize the action and ask for explicit "
                            "confirmation. Do not perform it yet."
                        ),
                    }
            elif chat_session and tool_name == "request_schedule":
                for field in (
                    "customer_name",
                    "customer_email",
                    "customer_phone",
                ):
                    arguments[field] = (
                        arguments.get(field)
                        or customer_context.get(field)
                    )
                missing = [
                    field
                    for field in (
                        "customer_name",
                        "customer_email",
                        "customer_phone",
                    )
                    if not str(arguments.get(field) or "").strip()
                ]
                if missing:
                    result = {
                        "error": (
                            "Ask only for these missing customer fields: "
                            + ", ".join(missing)
                        )
                    }
                else:
                    summary = (
                        f"Schedule request for "
                        f"{_service_name(db, company_id, arguments['service_id'])}"
                        f" on {arguments['requested_date']}"
                    )
                    _save_pending_action(
                        db,
                        chat_session,
                        {
                            "action_type": "request_schedule",
                            "company_id": str(company_id),
                            "external_user_id": external_user_id,
                            "customer_email": arguments.get("customer_email"),
                            "summary": summary,
                            "awaiting_confirmation": True,
                            "arguments": arguments,
                        },
                    )
                    result = {
                        "confirmation_required": True,
                        "summary": summary,
                        "instruction": (
                            "Show the schedule request summary and ask "
                            "for explicit confirmation. Do not submit yet."
                        ),
                    }
            else:
                result = execute_tool(
                    tool_name=tool_name,
                    arguments=arguments,
                    db=db,
                    company_id=company_id,
                    external_user_id=external_user_id,
                    customer_email=customer_context.get(
                        "customer_email"
                    ),
                )
                if tool_name == "list_customer_appointments" and isinstance(
                    result, list
                ):
                    listed_appointments = result
        except (KeyError, TypeError, ValueError) as exc:
            result = {
                "error": str(exc),
            }

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

    final_response = ai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    f"{SYSTEM_PROMPT}\n\n{company_context}\n\n"
                    f"{customer_prompt}{pending_prompt}"
                ),
            },
            *messages,
        ],
    )

    final_content = final_response.choices[0].message.content
    if chat_session and listed_appointments:
        _stage_cancellation_from_reply(
            db=db,
            company_id=company_id,
            chat_session=chat_session,
            external_user_id=external_user_id,
            customer_email=customer_context.get("customer_email"),
            cancellation_reason=_latest_cancellation_reason(messages),
            assistant_content=final_content or "",
            appointments=listed_appointments,
        )
    return {"message": final_content}
