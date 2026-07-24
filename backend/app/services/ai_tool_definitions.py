BOOKING_TOOL = {
    "type": "function",
    "function": {
        "name": "book_appointment",
        "description": (
            "Book an appointment only after the user has selected "
            "a valid service, date, and available time."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "service_id": {
                    "type": "string",
                    "description": "UUID of the selected service",
                },
                "appointment_date": {
                    "type": "string",
                    "description": "Appointment date in YYYY-MM-DD format",
                },
                "start_time": {
                    "type": "string",
                    "description": "Start time in HH:MM format",
                },
                "customer_name": {
                    "type": "string",
                },
                "customer_email": {
                    "type": "string",
                },
                "customer_phone": {
                    "type": "string",
                },
            },
            "required": [
                "service_id",
                "appointment_date",
                "start_time",
            ],
        },
    },
}


AVAILABILITY_TOOL = {
    "type": "function",
    "function": {
        "name": "get_available_slots",
        "description": (
            "Check available appointment times for a service "
            "on a specific date."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "service_id": {
                    "type": "string",
                },
                "requested_date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format",
                },
            },
            "required": [
                "service_id",
                "requested_date",
            ],
        },
    },
}


CANCEL_TOOL = {
    "type": "function",
    "function": {
        "name": "cancel_appointment",
        "description": (
            "Cancel an existing appointment when the user "
            "provides enough information to identify it."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "appointment_id": {
                    "type": "string",
                },
                "cancellation_reason": {
                    "type": "string",
                },
            },
            "required": [
                "appointment_id",
            ],
        },
    },
}


SCHEDULE_REQUEST_TOOL = {
    "type": "function",
    "function": {
        "name": "request_schedule",
        "description": (
            "Create a schedule request when the user wants "
            "a time outside the available schedule."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "service_id": {
                    "type": "string",
                },
                "requested_date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format",
                },
                "preferred_start_time": {
                    "type": "string",
                },
                "preferred_end_time": {
                    "type": "string",
                },
                "message": {
                    "type": "string",
                },
                "customer_name": {
                    "type": "string",
                },
                "customer_email": {
                    "type": "string",
                },
                "customer_phone": {
                    "type": "string",
                },
            },
            "required": [
                "service_id",
                "requested_date",
            ],
        },
    },
}


AI_TOOLS = [
    AVAILABILITY_TOOL,
    BOOKING_TOOL,
    CANCEL_TOOL,
    SCHEDULE_REQUEST_TOOL,
]