from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
import os
from dotenv import load_dotenv

from api.api_gateway import include_api_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables - try .env.local first, then .env
env_file = '.env.local' if os.path.exists('.env.local') else '.env'
load_dotenv(env_file)
logger.info(f"Environment variables loaded from {env_file}")

def create_app() -> FastAPI:
    """
    Application factory for the digital twin backend.
    Sets up CORS, routes, and basic metadata.
    """
    app = FastAPI(
        title="Digital Twin Smart Building API",
        version="0.1.0",
        description=(
            "Backend for a smart-building digital twin that simulates, "
            "detects anomalies, and suggests energy/comfort optimizations."
        ),
    )

    # Configure CORS based on environment
    allowed_origins = os.getenv("FRONTEND_URL", "http://localhost:5173").split(",")
    logger.info(f"CORS allowed origins: {allowed_origins}")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    include_api_routes(app)
    logger.info("API routes initialized")

    @app.get("/", tags=["system"])
    async def root() -> dict:
        """Root endpoint with API information."""
        return {
            "name": "Digital Twin Smart Building API",
            "version": "0.1.0",
            "status": "operational",
            "endpoints": {
                "docs": "/docs",
                "health": "/health",
                "simulation": "/simulation",
                "anomalies": "/anomalies",
                "suggestions": "/suggestions",
                "layout": "/layout",
                "historical": "/historical",
                "websocket": "/ws"
            }
        }

    @app.get("/health", tags=["system"])
    async def health_check() -> dict:
        return {"status": "ok"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
