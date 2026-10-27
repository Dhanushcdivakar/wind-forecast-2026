import os
import sys

cur_dir = os.path.dirname(os.path.abspath(__file__))

if os.path.exists(os.path.join(cur_dir, "app")):
    if cur_dir not in sys.path:
        sys.path.insert(0, cur_dir)
else:
    backend_dir = os.path.abspath(os.path.join(cur_dir, "..", "backend"))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

try:
    from app.main import app
except Exception as e:
    import traceback
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    err_trace = traceback.format_exc()
    app = FastAPI()

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
    async def debug_error(path: str = ""):
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "traceback": err_trace.splitlines()},
        )
