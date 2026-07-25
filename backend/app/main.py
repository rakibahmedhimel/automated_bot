from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routers.admin_dashboard import (
    router as admin_dashboard_router,
)
from backend.app.routers.admin_schedule import (
    router as admin_schedule_router,
)
from backend.app.routers.appointments import (
    router as appointments_router,
)
from backend.app.routers.availability import (
    router as availability_router,
)
from backend.app.routers.chat import (
    router as chat_router,
)
from backend.app.routers.companies import (
    router as companies_router,
)
from backend.app.routers.customer_conversations import (
    admin_router as admin_customer_conversations_router,
    router as customer_conversations_router,
)
from backend.app.routers.schedule_requests import (
    router as schedule_requests_router,
)
from backend.app.routers.services import (
    router as services_router,
)
from backend.app.routers.superadmin import router as superadmin_router

app = FastAPI(
    title="Slotely Booking API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(companies_router)
app.include_router(services_router)
app.include_router(availability_router)
app.include_router(appointments_router)
app.include_router(schedule_requests_router)
app.include_router(admin_schedule_router)
app.include_router(admin_dashboard_router)
app.include_router(chat_router)
app.include_router(customer_conversations_router)
app.include_router(admin_customer_conversations_router)
app.include_router(superadmin_router)
