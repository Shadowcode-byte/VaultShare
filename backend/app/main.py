import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.routers import auth, files, admin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vaultshare")

app = FastAPI(title="VaultShare API", version="0.1.0")

# allow_credentials=True is required for the session cookie to be sent
# on cross-origin requests from the React dev server (different port =
# different origin). allow_origins is deliberately an explicit list, not
# "*" — a wildcard origin is incompatible with allow_credentials anyway,
# and more importantly would let ANY site's JS make authenticated
# requests on a logged-in user's behalf.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server; add prod frontend URL here too
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catches anything that isn't already an HTTPException (those still
    return their own status/detail as normal). This is the backstop for
    rule #22 in the project brief: a raw database error, a stack trace,
    or an internal file path must never reach the client — but we still
    want the real detail in server-side logs for debugging.
    """
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Something went wrong. Please try again."})


app.include_router(auth.router)
app.include_router(files.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok", "env": settings.env}


# Production SPA hosting. API routes are registered above, so these
# catch-all routes only serve frontend paths such as /login or /dashboard.
if settings.env == "production":
    from pathlib import Path
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    _dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if not (_dist / "index.html").is_file():
        raise RuntimeError("Production frontend build missing")
    app.mount("/assets", StaticFiles(directory=str(_dist / "assets")), name="assets")

    @app.get("/", include_in_schema=False)
    def serve_root():
        return FileResponse(_dist / "index.html")

    @app.get("/{frontend_path:path}", include_in_schema=False)
    def serve_spa(frontend_path: str):
        if frontend_path.startswith(("auth/", "files/", "admin/", "api/")):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        requested = (_dist / frontend_path).resolve()
        if requested.is_relative_to(_dist.resolve()) and requested.is_file():
            return FileResponse(requested)
        return FileResponse(_dist / "index.html")
