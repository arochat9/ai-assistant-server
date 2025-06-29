import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routes import messages, todos
from app.core.config import settings
from app.core.database import get_db
from app.services.debounce_service import DebounceService


@pytest_asyncio.fixture
async def db_session():
    """Test database session with transaction rollback"""
    engine = create_async_engine(
        settings.ASYNC_DATABASE_URL,
        pool_size=10,  # Increased for parallel tests
        max_overflow=20,
    )
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:
        transaction = await session.begin()
        try:
            yield session
        finally:
            if transaction.is_active:
                await transaction.rollback()
            await engine.dispose()


@pytest_asyncio.fixture
async def async_client(db_session):
    """Async test client with mocked services"""
    app = FastAPI(title="Test App")
    app.include_router(messages.router, prefix="/api/v1")
    app.include_router(todos.router, prefix="/api/v1")

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    # Create debounce service with disabled timer
    disabled_debounce = DebounceService(debounce_seconds=-1)

    app.dependency_overrides[get_db] = lambda: db_session

    # Mock debounce service at the app level instead of module level
    import app.api.routes.messages as msg_module

    original = msg_module.debounce_service
    msg_module.debounce_service = disabled_debounce

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    finally:
        disabled_debounce.shutdown()
        msg_module.debounce_service = original
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client_with_debounce(db_session):
    """Test client with enabled debounce for timer testing"""
    app = FastAPI(title="Test App")
    app.include_router(messages.router, prefix="/api/v1")
    app.include_router(todos.router, prefix="/api/v1")

    enabled_debounce = DebounceService(debounce_seconds=1)

    app.dependency_overrides[get_db] = lambda: db_session

    import app.api.routes.messages as msg_module

    original = msg_module.debounce_service
    msg_module.debounce_service = enabled_debounce

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client, enabled_debounce
    finally:
        enabled_debounce.shutdown()
        msg_module.debounce_service = original
        app.dependency_overrides.clear()
