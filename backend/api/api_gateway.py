from fastapi import FastAPI

from .routes import (
    simulation_routes,
    anomaly_routes,
    suggestions_routes,
    layout_routes,
    auth_routes,
    websocket_routes,
    historical_routes,
    dashboard_routes,
    forecasting_routes,
    chat_routes,
)


def include_api_routes(app: FastAPI) -> None:
    """
    Central place to mount all API routers onto the FastAPI app.
    """
    
    app.include_router(
        simulation_routes.router,
        prefix="/simulation",
        tags=["simulation"],
    )
    app.include_router(
        anomaly_routes.router,
        prefix="/anomalies",
        tags=["anomalies"],
    )
    app.include_router(
        suggestions_routes.router,
        prefix="/suggestions",
        tags=["suggestions"],
    )
    app.include_router(
        layout_routes.router,
        prefix="/layout",
        tags=["layout"],
    )
    app.include_router(
        auth_routes.router,
        prefix="/auth",
        tags=["auth"],
    )
    app.include_router(
        websocket_routes.router,
        prefix="/ws",
        tags=["websocket"],
    )
    app.include_router(
        historical_routes.router,
        prefix="/historical",
        tags=["historical"],
    )
    app.include_router(
        dashboard_routes.router,
        prefix="/dashboard",
        tags=["dashboard"],
    )
    app.include_router(
        forecasting_routes.router,
        prefix="/forecast",
        tags=["forecasting"],
    )
    app.include_router(
        chat_routes.router,
        prefix="/chat",
        tags=["chat"],
    )
