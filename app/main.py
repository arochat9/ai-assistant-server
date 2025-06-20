import time
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import messages, todos
from app.core.config import settings
from app.core.middleware import APMMiddleware, LoggingMiddleware
from app.services.agent_service import AgentService
from app.services.debounce_service import DebounceService

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global services
debounce_service = DebounceService()
agent_service = AgentService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting FastAPI application")
    yield
    # Shutdown
    logger.info("Shutting down FastAPI application")
    debounce_service.shutdown()


app = FastAPI(
    title="AI Assistant Server",
    description="FastAPI server for processing messages and managing todos with agentic processing",
    version="1.0.0",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(APMMiddleware)
app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(messages.router, prefix="/api/v1")
app.include_router(todos.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "AI Assistant Server is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=settings.PORT, reload=settings.DEBUG
    )
