import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agent_bazaar.api.routes import tasks, agents, websocket
from agent_bazaar.storage.database import create_tables

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from agent_bazaar.config import settings
    logger = logging.getLogger("agent_bazaar.startup")
    if not settings.anthropic_api_key and not settings.gemini_api_key:
        logger.error(
            "No API key configured! Set GEMINI_API_KEY (or ANTHROPIC_API_KEY) in your .env file. "
            "All tasks will fail until a key is provided."
        )
    else:
        provider = "Anthropic" if settings.anthropic_api_key else "Gemini"
        logger.info("API key configured for provider: %s", provider)
        logger.info("Models — broker=%s  aggregator=%s  scorer=%s",
                    settings.broker_model, settings.aggregator_model, settings.scorer_model)
    await create_tables()
    yield


app = FastAPI(title="Agent Bazaar", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])
